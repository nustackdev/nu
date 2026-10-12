"""nudle telemetry: the opt-out switches, the dev-install skip, the route.

Nothing here touches the network: ``_fire`` is replaced with a recorder, and
``HOME`` points at a temp dir so ``~/.nudle`` is a scratch directory.
"""

from __future__ import annotations

import json

import pytest
from starlette.routing import Route
from starlette.testclient import TestClient

from nustd.ui.nudle import telemetry
from nustd.ws_server import WebServer


@pytest.fixture
def sent(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NUDLE_TELEMETRY", raising=False)
    monkeypatch.setenv("NUDLE_DEV", "0")
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
    tree = nustd.ui.serve(nustd.ui.Index, nu.Int(0), routes=[extra])
    first_run, server = tree._payload["brackets"]
    assert first_run._payload["cls"] is telemetry.FirstRun
    paths = [r.path for r in server._payload["kwargs"]["routes"]]
    assert paths == ["/api/telemetry-config", "/api/extra"]


def test_first_run_hook_fires_on_setup(sent):
    telemetry.FirstRun().setup(None)
    assert len(sent) == 1
