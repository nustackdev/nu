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
from starlette.exceptions import HTTPException as StarletteHTTPException

from .page import Index, Page
from .refs.base import NudleRef
from .session import NudleSession


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["serve"]


_BUNDLED_STATIC = Path(__file__).parent / "_static"


class _SPAStatic(StaticFiles):
    """StaticFiles that falls back to index.html on 404.

    Lets the browser hit deep URLs (/feed, /portfolio/...) directly: any
    path the bundle doesn't have a real file for returns index.html so
    the SPA can render the right page from window.location.
    """

    async def get_response(self, path: str, scope: object) -> object:
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as e:
            if e.status_code == 404:
                return await super().get_response("index.html", scope)
            raise
        if getattr(response, "status_code", 200) == 404:
            return await super().get_response("index.html", scope)
        return response


def _find_index(app: Nu) -> type[Index]:
    """Walk the Nu tree, find the Index whose structural Refs / pages it touches.

    Refs in the tree can root on either the Index (structural Refs) or on
    a Page subclass registered in some Index's `pages` map. We accept either
    and resolve back to the unique Index.
    """
    seen_indexes: set[type[Index]] = set()
    seen_pages: set[type[Page]] = set()
    for node in preorder(app):
        if not isinstance(node, NudleRef):
            continue
        root = node.get_root_shape()
        if root is None:
            continue
        if issubclass(root, Index):
            seen_indexes.add(root)
        elif issubclass(root, Page):
            seen_pages.add(root)
    # Resolve pages back to their Index.
    for page_cls in seen_pages:
        for idx_cls in _all_index_subclasses():
            if page_cls in idx_cls.pages.routes.values():
                seen_indexes.add(idx_cls)
                break
        else:
            raise RuntimeError(
                f"Page {page_cls.__name__} is used but not registered in any Index.pages",
            )
    if not seen_indexes:
        raise RuntimeError("no nudle.Index found in Nu tree")
    if len(seen_indexes) > 1:
        names = ", ".join(i.__name__ for i in seen_indexes)
        raise RuntimeError(f"multiple Index shapes found ({names}); one per app")
    return next(iter(seen_indexes))


def _all_index_subclasses() -> list[type[Index]]:
    """Walk Index's subclass tree (transitive)."""
    out: list[type[Index]] = []
    stack: list[type] = [Index]
    while stack:
        cls = stack.pop()
        for sub in cls.__subclasses__():
            out.append(sub)
            stack.append(sub)
    return out


async def serve(
    app: Nu,
    ctx: Context,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    static_dir: Path | str | None = None,
) -> None:
    """Run a nudle UI program."""
    index_cls = _find_index(app)
    fastapi_app = FastAPI(title="nudle")

    @fastapi_app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        session = NudleSession(ws)
        await session.mount(
            index_cls.__name__,
            index_cls.structural_fields(),
            index_cls.pages_payload(),
        )
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

    # Resolve static dir: explicit override wins; otherwise fall back to the
    # bundle baked into the wheel at nudle/_static.
    path = Path(static_dir) if static_dir is not None else _BUNDLED_STATIC
    if path.exists():
        fastapi_app.mount("/", _SPAStatic(directory=path, html=True), name="static")

    config = uvicorn.Config(fastapi_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
