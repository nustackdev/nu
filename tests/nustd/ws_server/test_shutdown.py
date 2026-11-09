"""Shutdown: a cancel of the cleanup is never swallowed, and a stuck server is cancelled.

The server task is stood in for by a plain task, so the race between the
server stopping and the cleanup being cancelled lands on one tick.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from nustd.ws_server import WebServer


class _Session:
    async def run_intake(self) -> None:
        return None


def _serving(web: WebServer, task: asyncio.Task) -> None:
    web._server = SimpleNamespace(should_exit=False)  # type: ignore[assignment]
    web._task = task


async def test_a_cancel_landing_as_the_server_stops_still_cancels():
    web = WebServer(session_cls=_Session)
    stopped = asyncio.Event()
    _serving(web, asyncio.ensure_future(stopped.wait()))
    cleanup = asyncio.ensure_future(web.acleanup())
    await asyncio.sleep(0)
    stopped.set()
    cleanup.cancel()
    await asyncio.wait({cleanup})
    assert cleanup.cancelled()


async def test_a_server_that_does_not_stop_in_time_is_cancelled():
    web = WebServer(session_cls=_Session, shutdown_timeout=0.05)
    server_task = asyncio.ensure_future(asyncio.sleep(60))
    _serving(web, server_task)
    await web.acleanup()
    assert server_task.cancelled()
    assert web._task is None


async def test_a_cancelled_cleanup_cancels_the_server():
    web = WebServer(session_cls=_Session)
    server_task = asyncio.ensure_future(asyncio.sleep(60))
    _serving(web, server_task)
    cleanup = asyncio.ensure_future(web.acleanup())
    await asyncio.sleep(0)
    cleanup.cancel()
    await asyncio.wait({cleanup, server_task})
    assert cleanup.cancelled()
    assert server_task.cancelled()
