"""nudle telemetry: the opt-out switches, the dev-install skip, the route, the wire.

Nothing here touches the network: ``_fire`` is replaced with a recorder, or
``urlopen`` with a fake, and ``HOME`` points at a temp dir so ``~/.nudle`` is
a scratch directory. The root conftest turns telemetry off for every test;
the ``sent`` fixture clears that for the tests here.
"""

from __future__ import annotations

import json
import threading

import pytest
from starlette.routing import Route
from starlette.testclient import TestClient

from nustd.ui.nudle import telemetry
from nustd.ws_server import WebServer


_OPT_OUT_VARS = ("NUDLE_TELEMETRY", *telemetry._OFF_WHEN_SET)


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in _OPT_OUT_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("NUDLE_POSTHOG_TOKEN", raising=False)
    monkeypatch.delenv("NUDLE_POSTHOG_HOST", raising=False)
    monkeypatch.setenv("NUDLE_DEV", "0")


@pytest.fixture
def sent(clean_env, monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(telemetry, "_fire", lambda *a, **kw: calls.append((a, kw)))
    return calls


def test_config_lives_under_home_dot_nudle(sent, tmp_path):
    cfg = telemetry.ensure_config()
    assert telemetry.config_path() == tmp_path / ".nudle" / "config.json"
    on_disk = json.loads(telemetry.config_path().read_text())
    assert on_disk == cfg
    assert cfg["telemetry"] is True
    assert telemetry.distinct_id() == cfg["distinct_id"]
    assert telemetry.ensure_config()["distinct_id"] == cfg["distinct_id"]


def test_first_run_fires_once_on(sent):
    telemetry.capture_first_run()
    assert len(sent) == 1
    (event, did), kw = sent[0]
    assert event == telemetry.FIRST_RUN_EVENT
    assert did == telemetry.distinct_id()
    kw["on_success"]()
    assert telemetry.first_run_marker().exists()
    telemetry.capture_first_run()
    assert len(sent) == 1


@pytest.mark.parametrize("value", ["0", "false", "off", "OFF"])
def test_env_opt_out_wins_over_config(sent, monkeypatch, value):
    telemetry.set_telemetry(True)
    monkeypatch.setenv("NUDLE_TELEMETRY", value)
    assert telemetry.telemetry_enabled() is False
    telemetry.capture_first_run()
    telemetry.capture("x")
    assert sent == []
    assert telemetry.config_for_browser()["enabled"] is False


def test_env_on_wins_over_config_off(sent, monkeypatch):
    telemetry.set_telemetry(False)
    monkeypatch.setenv("NUDLE_TELEMETRY", "1")
    assert telemetry.telemetry_enabled() is True


def test_config_opt_out(sent):
    telemetry.set_telemetry(False)
    telemetry.capture_first_run()
    assert sent == []
    payload = telemetry.config_for_browser()
    assert payload["enabled"] is False
    assert payload["posthog_token"] == ""


def test_dev_install_skips(sent, monkeypatch):
    monkeypatch.setenv("NUDLE_DEV", "1")
    telemetry.capture_first_run()
    assert sent == []
    assert telemetry.config_for_browser()["enabled"] is False


def test_this_checkout_counts_as_dev(monkeypatch):
    monkeypatch.delenv("NUDLE_DEV", raising=False)
    assert telemetry.is_dev_install() is True


def test_browser_payload_shape(sent):
    telemetry.ensure_config()
    payload = telemetry.config_for_browser()
    assert payload["enabled"] is True
    assert payload["posthog_token"] == telemetry.POSTHOG_TOKEN
    assert payload["posthog_host"] == telemetry.POSTHOG_HOST
    assert payload["product"] == "nudle"
    for key in ("distinct_id", "nu_version", "nudle_version", "python_version", "platform", "arch"):
        assert key in payload


def test_route_is_served_through_the_ws_server(sent):
    class _Session:
        def __init__(self, ws: object) -> None:
            del ws

        async def run_intake(self) -> None:
            return None

    route = telemetry.route()
    assert isinstance(route, Route)
    app = WebServer(session_cls=_Session, routes=[route])._build_app()
    with TestClient(app) as client:
        body = client.get("/api/telemetry-config").json()
    assert body["enabled"] is True
    assert body["product"] == "nudle"


def test_serve_mounts_the_route_and_the_first_run_hook():
    import nu
    import nustd

    extra = Route("/api/extra", lambda request: None)
    tree = nustd.ui.serve(nu.Int(0), routes=[extra])
    first_run, server = tree._payload["brackets"]
    assert first_run._payload["cls"] is telemetry.FirstRun
    paths = [r.path for r in server._payload["kwargs"]["routes"]]
    assert paths == ["/api/telemetry-config", "/api/extra"]


def test_first_run_hook_fires_on_setup(sent):
    telemetry.FirstRun().setup(None)
    assert len(sent) == 1


def test_the_suite_runs_with_telemetry_off():
    assert telemetry.telemetry_enabled() is False
    assert telemetry.config_for_browser()["posthog_token"] == ""


@pytest.mark.parametrize("name", telemetry._OFF_WHEN_SET)
def test_do_not_track_and_ci_turn_it_off(sent, monkeypatch, name):
    monkeypatch.setenv(name, "1")
    assert telemetry.env_override() == name
    assert telemetry.telemetry_enabled() is False
    telemetry.capture_first_run()
    telemetry.capture(telemetry.OPENED_EVENT)
    assert sent == []
    payload = telemetry.config_for_browser()
    assert payload["enabled"] is False
    assert payload["posthog_token"] == ""
    assert payload["distinct_id"] == ""


def test_do_not_track_wins_over_forced_on(sent, monkeypatch):
    monkeypatch.setenv("NUDLE_TELEMETRY", "1")
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    assert telemetry.telemetry_enabled() is False


@pytest.mark.parametrize("value", ["", "0", "false"])
def test_ci_set_to_off_or_empty_does_not_count(sent, monkeypatch, value):
    monkeypatch.setenv("CI", value)
    assert telemetry.telemetry_enabled() is True


def test_unknown_events_are_dropped(sent):
    telemetry.capture("nudle_something_else")
    telemetry.capture("x")
    assert sent == []
    telemetry.capture(telemetry.OPENED_EVENT)
    assert [a[0] for a, _ in sent] == [telemetry.OPENED_EVENT]


def test_browser_gets_an_id_once_enabled(sent):
    payload = telemetry.config_for_browser()
    assert payload["distinct_id"] == telemetry.distinct_id() != "unknown"


def test_the_token_has_one_source(clean_env, monkeypatch):
    assert telemetry.posthog_token() == telemetry.POSTHOG_TOKEN
    monkeypatch.setenv("NUDLE_POSTHOG_TOKEN", "phc_local")
    monkeypatch.setenv("NUDLE_POSTHOG_HOST", "http://127.0.0.1:1/")
    assert telemetry.posthog_token() == "phc_local"
    assert telemetry.posthog_host() == "http://127.0.0.1:1"


def test_no_install_record_counts_as_dev(monkeypatch):
    from importlib import metadata

    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.delenv("NUDLE_DEV", raising=False)
    monkeypatch.setattr(telemetry.metadata, "distribution", missing)
    assert telemetry.is_dev_install() is True


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return b'{"status":"Ok"}'


@pytest.fixture
def wire(clean_env, monkeypatch):
    """Every request ``urlopen`` sees, with a 200 back; set once each lands."""
    requests: list = []
    landed = threading.Event()

    def fake_urlopen(req, timeout, context):
        requests.append((req, timeout, context))
        landed.set()
        return _Response()

    monkeypatch.setattr(telemetry.urllib.request, "urlopen", fake_urlopen)
    return requests, landed


def test_first_run_goes_to_batch_with_our_user_agent(wire):
    requests, landed = wire
    telemetry.capture_first_run()
    assert landed.wait(5)
    req, timeout, context = requests[0]
    assert req.full_url == f"{telemetry.POSTHOG_HOST}{telemetry.POSTHOG_BATCH_PATH}"
    assert req.get_method() == "POST"
    assert req.get_header("User-agent").startswith("nudle-py/")
    assert timeout == telemetry.HTTP_TIMEOUT_SECONDS
    assert context is telemetry._ssl_context()
    body = json.loads(req.data)
    assert body["api_key"] == telemetry.POSTHOG_TOKEN
    (event,) = body["batch"]
    assert event["event"] == telemetry.FIRST_RUN_EVENT
    assert event["distinct_id"] == telemetry.distinct_id()
    assert event["properties"]["product"] == "nudle"
    assert "timestamp" in event


def test_a_failed_post_is_swallowed_and_retried_next_start(clean_env, monkeypatch):
    def down(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(telemetry.urllib.request, "urlopen", down)
    marked: list = []
    telemetry._post({"batch": []}, lambda: marked.append(1))
    assert marked == []
    assert not telemetry.first_run_marker().exists()


def test_a_2xx_marks_the_first_run(wire):
    telemetry._post({"batch": []}, telemetry._mark_first_run_sent)
    assert telemetry.first_run_marker().exists()


def test_ssl_context_verifies_and_is_made_once():
    import ssl

    context = telemetry._ssl_context()
    assert context is telemetry._ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
