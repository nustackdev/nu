"""`nudle.serve` -- async host function that runs a Nu UI program over ws.

Not a Nu. A plain async function that owns the ws listener, accepts
connections, and for each one evaluates the user's Nu with a fresh
NudleSession bound on Context. Inbound frames (notify, read replies)
are drained by `session.run_intake` in parallel with the Nu evaluation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from nu import runtime
from nu.tree.walk import preorder

from .page import Page
from .refs.base import NudleRef
from .session import NudleSession


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["serve"]


def _find_page(app: Nu) -> type[Page]:
    """Walk the Nu tree, find the page Shape that owns the nudle refs."""
    seen: set[type[Page]] = set()
    for node in preorder(app):
        if isinstance(node, NudleRef):
            root = node.get_root_shape()
            if root is not None and issubclass(root, Page):
                seen.add(root)
    if not seen:
        raise RuntimeError("no nudle.Page found in Nu tree")
    if len(seen) > 1:
        names = ", ".join(p.__name__ for p in seen)
        raise RuntimeError(f"multiple nudle.Page shapes found ({names}); v0.1.0 supports one")
    return next(iter(seen))


async def serve(
    app: Nu,
    ctx: Context,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    static_dir: Path | str | None = None,
) -> None:
    """Run a nudle UI program."""
    page_cls = _find_page(app)
    fastapi_app = FastAPI(title="nudle")

    @fastapi_app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        session = NudleSession(ws)
        await session.mount(page_cls.__name__, page_cls.mount_fields())
        per_conn_ctx = ctx.bind(NudleSession, session)
        intake_task = asyncio.create_task(session.run_intake())
        eval_task = asyncio.create_task(runtime.aexecute(app, per_conn_ctx))
        try:
            done, _ = await asyncio.wait(
                {intake_task, eval_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in done:
                exc = t.exception()
                if exc is not None and not isinstance(exc, asyncio.CancelledError):
                    raise exc
        finally:
            for t in (intake_task, eval_task):
                if not t.done():
                    t.cancel()
                    try:
                        await t
                    except (asyncio.CancelledError, Exception):
                        pass

    if static_dir is not None:
        path = Path(static_dir)
        if path.exists():
            fastapi_app.mount("/", StaticFiles(directory=path, html=True), name="static")

    config = uvicorn.Config(fastapi_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
