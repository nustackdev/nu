"""The session id: ``session_for`` binds it under ``SessionId`` for its arm.

Driven against a server whose connection book the test fills by hand, so no
socket is opened. Covers the bracket alone, the fold handing each arm its own
id, ``run_once`` reading it, and the Shape's module staying light.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import uuid

import pytest

import nu
from nu.context import FabricRef
from nu.lang.runtime import Context
from nustd.session import SessionId
from nustd.ws_server import WebServer, run_once, session_for, sessions_fold
from nustd.ws_server.fabric import _Connection


class _Session:
    async def run_intake(self) -> None:
        return None


class Out(nu.Shape):
    log = nu.mem.ListRef.slot(object)


def _server(n: int) -> tuple[WebServer, list[str]]:
    server = WebServer(session_cls=_Session)
    sids = [uuid.uuid4().hex for _ in range(n)]
    for sid in sids:
        server._connections[sid] = _Connection(_Session())
    return server, sids


def _ctx(server: WebServer) -> tuple[dict, Context]:
    data: dict = {"log": []}
    return data, Context().bind(WebServer, server).bind(dict, data, Out)


async def test_session_for_binds_the_id_and_the_transport() -> None:
    server, (sid,) = _server(1)
    _, ctx = _ctx(server)
    body = nu.List.of(SessionId.sid, FabricRef(_Session).exists())
    got, out = await nu.arun(session_for(sid, body), ctx)
    assert got == [sid, True]
    assert out is ctx


async def test_session_for_an_unknown_id_raises() -> None:
    server, _ = _server(0)
    _, ctx = _ctx(server)
    with pytest.raises(LookupError, match="no live ws session"):
        await nu.arun(session_for("gone", SessionId.sid), ctx)


def test_a_read_outside_session_for_names_the_shape() -> None:
    with pytest.raises(LookupError, match="SessionId"):
        nu.run(SessionId.sid)


async def test_each_arm_of_the_fold_reads_its_own_id_once() -> None:
    server, sids = _server(3)
    data, ctx = _ctx(server)
    fold = sessions_fold(lambda sid: session_for(sid, run_once(Out.log.append(SessionId.sid))))
    task = asyncio.ensure_future(nu.arun(fold, ctx))
    for _ in range(200):
        if len(data["log"]) == len(sids):
            break
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert sorted(data["log"]) == sorted(sids)
    assert all(server.is_done(sid) for sid in sids)


def test_the_shape_imports_without_the_web_stack() -> None:
    code = (
        "import sys, nustd.session, nustd.ui.uploads; "
        "assert 'starlette' not in sys.modules and 'uvicorn' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)  # noqa: S603 - our own code
