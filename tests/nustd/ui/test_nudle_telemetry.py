"""nudle telemetry: the opt-out switches, the dev-install skip, the config route.

Python sends nothing: the browser owns the one ``nudle_opened`` ping, and
this side only answers ``/api/telemetry-config``. ``HOME`` points at a temp
dir so ``~/.nudle`` is a scratch directory. The root conftest turns
telemetry off for every test; the ``clean_env`` fixture clears that for the
tests here.
"""

from __future__ import annotations

import json
import socket

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


def _assert_off(payload: dict) -> None:
    assert payload == {"enabled": False}


def test_config_lives_under_home_dot_nudle(clean_env, tmp_path):
    cfg = telemetry.ensure_config()
    assert telemetry.config_path() == tmp_path / ".nudle" / "config.json"
    on_disk = json.loads(telemetry.config_path().read_text())
    assert on_disk == cfg
    assert cfg["telemetry"] is True
    assert telemetry.ensure_config()["distinct_id"] == cfg["distinct_id"]


@pytest.mark.parametrize("value", ["0", "false", "off", "OFF", "no"])
def test_env_opt_out_wins_over_config(clean_env, monkeypatch, value):
    telemetry.set_telemetry(True)
    monkeypatch.setenv("NUDLE_TELEMETRY", value)
    assert telemetry.telemetry_enabled() is False
    _assert_off(telemetry.config_for_browser())


def test_env_on_wins_over_config_off(clean_env, monkeypatch):
    telemetry.set_telemetry(False)
    monkeypatch.setenv("NUDLE_TELEMETRY", "1")
    assert telemetry.telemetry_enabled() is True
    assert telemetry.config_for_browser()["enabled"] is True


def test_config_opt_out(clean_env):
    telemetry.set_telemetry(False)
    _assert_off(telemetry.config_for_browser())


def test_dev_install_is_off(clean_env, monkeypatch):
    monkeypatch.setenv("NUDLE_DEV", "1")
    _assert_off(telemetry.config_for_browser())


def test_this_checkout_counts_as_dev(monkeypatch):
    monkeypatch.delenv("NUDLE_DEV", raising=False)
    assert telemetry.is_dev_install() is True


def test_no_install_record_counts_as_dev(monkeypatch):
    from importlib import metadata

    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.delenv("NUDLE_DEV", raising=False)
    monkeypatch.setattr(telemetry.metadata, "distribution", missing)
    assert telemetry.is_dev_install() is True


def test_browser_payload_when_on(clean_env):
    payload = telemetry.config_for_browser()
    assert payload["enabled"] is True
    assert payload["posthog_token"] == telemetry.POSTHOG_TOKEN
    assert payload["posthog_host"] == telemetry.POSTHOG_HOST
    assert payload["distinct_id"] == telemetry.ensure_config()["distinct_id"]
    assert payload["product"] == "nudle"
    for key in ("nu_version", "nudle_version", "python_version", "platform", "arch"):
        assert key in payload


def test_off_hands_out_no_id_and_writes_nothing(clean_env, monkeypatch):
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    _assert_off(telemetry.config_for_browser())
    assert not telemetry.config_path().exists()


def test_a_failure_reads_as_off(clean_env, monkeypatch):
    def broken() -> bool:
        raise RuntimeError("boom")

    monkeypatch.setattr(telemetry, "_active", broken)
    _assert_off(telemetry.config_for_browser())


def _client() -> TestClient:
    class _Session:
        def __init__(self, ws: object) -> None:
            del ws

        async def run_intake(self) -> None:
            return None

    route = telemetry.route()
    assert isinstance(route, Route)
    return TestClient(WebServer(session_cls=_Session, routes=[route])._build_app())


def test_route_serves_the_config_when_on(clean_env):
    with _client() as client:
        body = client.get("/api/telemetry-config").json()
    assert body["enabled"] is True
    assert body["product"] == "nudle"
    assert body["posthog_token"] == telemetry.POSTHOG_TOKEN


def test_route_serves_off_when_opted_out(clean_env, monkeypatch):
    monkeypatch.setenv("NUDLE_TELEMETRY", "0")
    with _client() as client:
        _assert_off(client.get("/api/telemetry-config").json())


def test_serve_mounts_the_route_first():
    import nu
    import nustd

    extra = Route("/api/extra", lambda request: None)
    tree = nustd.ui.serve(nu.Int(0), routes=[extra])
    (server,) = tree._payload["brackets"]
    paths = [r.path for r in server._payload["kwargs"]["routes"]]
    assert paths == ["/api/telemetry-config", "/api/extra"]


def test_the_suite_runs_with_telemetry_off():
    assert telemetry.telemetry_enabled() is False
    _assert_off(telemetry.config_for_browser())


@pytest.mark.parametrize("name", telemetry._OFF_WHEN_SET)
def test_do_not_track_and_ci_turn_it_off(clean_env, monkeypatch, name):
    monkeypatch.setenv(name, "1")
    assert telemetry.env_override() == name
    assert telemetry.telemetry_enabled() is False
    _assert_off(telemetry.config_for_browser())


def test_do_not_track_wins_over_forced_on(clean_env, monkeypatch):
    monkeypatch.setenv("NUDLE_TELEMETRY", "1")
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    assert telemetry.telemetry_enabled() is False


@pytest.mark.parametrize("value", ["", "0", "false"])
def test_ci_set_to_off_or_empty_does_not_count(clean_env, monkeypatch, value):
    monkeypatch.setenv("CI", value)
    assert telemetry.telemetry_enabled() is True


def test_the_token_has_one_source(clean_env, monkeypatch):
    assert telemetry.posthog_token() == telemetry.POSTHOG_TOKEN
    monkeypatch.setenv("NUDLE_POSTHOG_TOKEN", "phc_local")
    monkeypatch.setenv("NUDLE_POSTHOG_HOST", "http://127.0.0.1:1/")
    assert telemetry.posthog_token() == "phc_local"
    assert telemetry.posthog_host() == "http://127.0.0.1:1"


def test_python_side_never_touches_the_network(clean_env, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("telemetry opened a socket")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    assert telemetry.config_for_browser()["enabled"] is True
    for name in ("urllib", "http", "ssl", "threading", "certifi"):
        assert name not in vars(telemetry)
