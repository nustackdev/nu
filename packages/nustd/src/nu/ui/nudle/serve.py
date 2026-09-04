"""FastAPI app builder for a nudle Nu program.

Not a Nu. A plain builder that takes a nudle app tree + Context and returns
a `FastAPI` instance with `/ws` wired up: each connection gets a fresh
`NudleSession` bound on ctx, and the user's Nu evaluates in parallel with
`session.run_intake` draining inbound frames.

Called from ``NudleServer.asetup`` -- the bracket owns the uvicorn lifecycle.
"""

from __future__ import annotations

import asyncio
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from nu.lang.helpers import arun
from nu.tree.walk import preorder
from nu.ui.core import Ref, Session

from .page import Index, Page, _wire_type
from .session import NudleSession


if TYPE_CHECKING:
    from nu.lang import Context, Nu


__all__ = ["build_fastapi_app"]


def _bundled_static() -> Path | None:
    """Resolve the compiled web bundle shipped by the sibling `nudle` wheel.

    Returns None when the wheel is not installed -- the backend still boots
    (headless / dev / tests); the browser mount is just skipped.

    If ``import nudle`` resolves to a plain ``.py`` file (e.g. a local script
    on ``sys.path[0]`` shadowing the wheel) or to a package that lacks a
    ``build/index.html``, emit a warning and return None -- otherwise the SPA
    mount is silently dropped and every HTTP GET returns 404.
    """
    try:
        import nudle
    except ImportError:
        return None
    if not hasattr(nudle, "__path__"):
        warnings.warn(
            f"`import nudle` resolved to {nudle.__file__!r} (a module, not the "
            "ui wheel package). SPA mount skipped; only /ws is exposed. Rename "
            "the shadowing file or run from a directory that doesn't shadow "
            "the `nudle` package.",
            stacklevel=2,
        )
        return None
    build = Path(nudle.__file__).parent / "build"
    if not (build / "index.html").exists():
        return None
    return build


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


def _resolve_mount(app: Nu) -> tuple[str, list[dict[str, object]], list[dict[str, object]], bool]:
    """Return ``(name, structural_fields, pages_payload, sidebar)`` for ``session.mount``.

    Two paths, chosen by what the tree contains:

    - **Shape path**: at least one UI Ref roots on an ``Index`` or ``Page``.
      Resolves back to the unique Index (synthesizing one for a Page not
      registered anywhere) and returns its mount payload.
    - **Orphan path**: every UI Ref has ``_root_shape=None`` (shape-less
      refs like ``nu.ui.TextRef("count")``). Synthesizes a single-page
      ``_AutoIndex`` / ``_AutoPage`` mount from those refs' addresses.
    """
    seen_indexes: set[type[Index]] = set()
    seen_pages: set[type[Page]] = set()
    orphan_refs: dict[str, type[Ref]] = {}
    for node in preorder(app):
        if not isinstance(node, Ref):
            continue
        root = node._root_shape
        if root is None:
            addr = node._payload.get("segment")
            if isinstance(addr, str):
                orphan_refs.setdefault(addr, type(node))
            continue
        if issubclass(root, Index):
            seen_indexes.add(root)
        elif issubclass(root, Page):
            seen_pages.add(root)
    # Resolve pages back to their Index. Skip pages already covered by an
    # Index we've seen structurally -- otherwise a library default Index
    # that also registers the page would falsely get added and conflict.
    # A Page not registered in any Index is auto-mounted at "/" -- its
    # payload is emitted directly below, no synthesized Index class.
    auto_pages: list[type[Page]] = []
    for page_cls in seen_pages:
        if any(page_cls in idx.pages.routes.values() for idx in seen_indexes):
            continue
        for idx_cls in _all_index_subclasses():
            if page_cls in idx_cls.pages.routes.values():
                seen_indexes.add(idx_cls)
                break
        else:
            auto_pages.append(page_cls)
    if (seen_indexes or auto_pages) and orphan_refs:
        addrs = ", ".join(sorted(orphan_refs))
        raise RuntimeError(
            f"shape-less UI Refs ({addrs}) coexist with shape-rooted Refs; "
            "either wrap them in a Page or drop the shapes",
        )
    if seen_indexes and auto_pages:
        names = ", ".join(p.__name__ for p in auto_pages)
        raise RuntimeError(
            f"unmounted Page(s) ({names}) alongside an Index; register them or drop the Index",
        )
    if seen_indexes:
        if len(seen_indexes) > 1:
            names = ", ".join(i.__name__ for i in seen_indexes)
            raise RuntimeError(f"multiple Index shapes found ({names}); one per app")
        idx_cls = next(iter(seen_indexes))
        return (
            idx_cls.__name__,
            idx_cls._structural_fields(),
            idx_cls._pages_payload(),
            idx_cls._sidebar_enabled(),
        )
    if auto_pages:
        if len(auto_pages) > 1:
            names = ", ".join(p.__name__ for p in auto_pages)
            raise RuntimeError(
                f"multiple unmounted Pages ({names}); wrap them in an Index",
            )
        (page_cls,) = auto_pages
        pages_payload = [
            {
                "route": "/",
                "name": page_cls.__name__,
                "label": page_cls.nav_label or "home",
                "fields": page_cls._mount_fields(),
            },
        ]
        return ("_AutoIndex", [], pages_payload, False)
    if orphan_refs:
        fields: list[dict[str, object]] = [
            {"path": addr, "type": _wire_type(ref_cls)} for addr, ref_cls in orphan_refs.items()
        ]
        pages_payload = [
            {"route": "/", "name": "_AutoPage", "label": "home", "fields": fields},
        ]
        return ("_AutoIndex", [], pages_payload, False)
    raise RuntimeError("no nudle.Index, Page, or UI Ref found in Nu tree")


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


def build_fastapi_app(app: Nu, ctx: Context) -> FastAPI:
    """Build the FastAPI app for a nudle program (without starting uvicorn).

    Static assets (the compiled web bundle) come from the sibling `nudle`
    wheel: it packages the vite build output under `nudle/build/`, and we
    locate it at runtime via `import nudle`. If that wheel is not installed
    (or its build/ directory is empty), the static mount is skipped and only
    `/ws` is exposed -- run vite separately for the frontend in that case.
    """
    index_name, structural_fields, pages_payload, sidebar = _resolve_mount(app)
    fastapi_app = FastAPI(title="nudle")

    @fastapi_app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        session = NudleSession(ws)
        await session.mount(
            index_name,
            structural_fields,
            pages_payload,
            sidebar=sidebar,
        )
        per_conn_ctx = ctx.bind(Session, session)
        intake_task = asyncio.create_task(session.run_intake())
        eval_task = asyncio.create_task(arun(app, per_conn_ctx))
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

    @fastapi_app.get("/api/telemetry-config")
    async def telemetry_config() -> dict[str, object]:
        from nu._config.telemetry import config_for_browser

        return config_for_browser()

    static_dir = _bundled_static()
    if static_dir is not None and static_dir.exists():
        fastapi_app.mount(
            "/",
            _SPAStatic(directory=static_dir, html=True),
            name="static",
        )
    return fastapi_app
