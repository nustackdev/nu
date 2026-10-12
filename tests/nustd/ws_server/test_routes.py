"""Extra routes: the server mounts what it is handed and knows nothing else.

``routes=`` sits between ``/ws`` and the SPA mount, so a caller's endpoint
wins over the index.html fallback while unknown paths still reach the SPA.
The server itself serves no endpoint of its own beyond ``/ws``.
"""

from __future__ import annotations

import pytest
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, WebSocketRoute
from starlette.testclient import TestClient

from nustd.ws_server import WebServer, listen
from nustd.ws_server.fabric import _bundled_static


class _Session:
    def __init__(self, ws: object) -> None:
        self.ws = ws

    async def run_intake(self) -> None:
        return None


async def _ping(request: object) -> PlainTextResponse:
    del request
    return PlainTextResponse("pong")


async def _info(request: object) -> JSONResponse:
    del request
    return JSONResponse({"ok": True})


def test_no_routes_serves_ws_alone():
    app = WebServer(session_cls=_Session)._build_app()
    assert [type(r) for r in app.routes] == [WebSocketRoute]
    with TestClient(app) as client:
        assert client.get("/api/telemetry-config").status_code == 404


def test_extra_routes_are_served_after_ws():
    server = WebServer(session_cls=_Session, routes=[Route("/api/ping", _ping)])
    app = server._build_app()
    assert app.routes[0].path == "/ws"
    assert app.routes[1].path == "/api/ping"
    with TestClient(app) as client:
        assert client.get("/api/ping").text == "pong"


@pytest.mark.skipif(_bundled_static("nudle") is None, reason="nudle bundle not built")
def test_extra_routes_win_over_the_spa_fallback():
    server = WebServer(session_cls=_Session, static="nudle", routes=[Route("/api/info", _info)])
    with TestClient(server._build_app()) as client:
        assert client.get("/api/info").json() == {"ok": True}
        deep = client.get("/some/deep/page")
        assert deep.status_code == 200
        assert "text/html" in deep.headers["content-type"]


def test_listen_threads_routes_into_the_constructor():
    route = Route("/api/ping", _ping)
    kwargs = listen(session_cls=_Session, routes=[route])._payload["kwargs"]
    assert kwargs["routes"] == (route,)
    assert WebServer(**kwargs)._routes == (route,)
