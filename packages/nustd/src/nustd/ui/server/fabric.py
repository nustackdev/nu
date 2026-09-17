"""``WebServer`` -- the uvicorn lifecycle, and nothing else.

Boots uvicorn behind a FastAPI app with a ``/ws`` endpoint and a static mount,
binds itself to the Context, and stops uvicorn on the way out. It never sees
the UI program: that is a child of the tree, one arm per live connection.

The two halves it does own:

- the connection book, ``sid -> WsSession``, which the session bracket reads
  to hand one arm its transport.
- two channels, connect and disconnect, which announce those moments to
  whoever is subscribed. The endpoint has no Nu runtime around it, so it
  emits here and a Nu term does the kv write.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
import uuid
import warnings
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from nu._config.branding import BLUE, PURPLE, color_enabled, paint, render_header
from nu.context.fabric import Provide
from nustd.ui.core.session import WsSession


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Context


__all__ = ["WebServer", "web_server"]


def _bundled_static(package: str) -> Path | None:
    """Resolve the compiled web bundle shipped by ``package``.

    The wheel packages its vite output under ``build/``, so importing the
    package is how the directory is found at runtime. None when the wheel is
    not installed -- the backend still boots headless with only ``/ws``.
    """
    try:
        mod = importlib.import_module(package)
    except ImportError:
        return None
    paths = getattr(mod, "__path__", None)
    if not paths:
        warnings.warn(
            f"`import {package}` resolved to {mod.__file__!r} (a module, not the "
            "ui wheel package). SPA mount skipped; only /ws is exposed. Rename "
            f"the shadowing file or run from a directory that doesn't shadow "
            f"the `{package}` package.",
            stacklevel=2,
        )
        return None
    build = Path(next(iter(paths))) / "build"
    if not (build / "index.html").exists():
        return None
    return build


class _SPAStatic(StaticFiles):
    """StaticFiles that falls back to index.html on 404.

    Lets the browser hit deep URLs (/feed, /portfolio/...) directly: the SPA
    renders the right page from window.location.
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


class _Channel:
    """A subscription over a moment the server can only announce once.

    ``bind`` / ``unbind`` / ``close`` is the whole reactive contract Nu's
    atoms drive, so a plain fan-out object is a first-class change source.

    Events emitted while nobody is bound are held in a backlog: uvicorn opens
    the browser before the driver arm has had a chance to subscribe, so the
    very first connect would otherwise be dropped. Callbacks are compared by
    identity and a raising one is dropped -- the far end is usually a queue in
    a loop that may already be gone.
    """

    def __init__(self) -> None:
        self._callbacks: list[Callable[[object], None]] = []
        self._backlog: list[object] = []

    def emit(self, event: object) -> None:
        """Announce one event, or hold it until somebody binds."""
        if not self._callbacks:
            self._backlog.append(event)
            return
        self._fire(event)

    def bind(self, cb: Callable[[object], None]) -> None:
        """Register ``cb``, then hand it everything emitted while nobody listened."""
        if not any(cb is bound for bound in self._callbacks):
            self._callbacks.append(cb)
        if not self._backlog:
            return
        # Swapped out before firing: a callback that emits re-entrantly must
        # not see a list being drained underneath it.
        backlog, self._backlog = self._backlog, []
        for event in backlog:
            self._fire(event)

    def unbind(self, cb: Callable[[object], None]) -> None:
        """Drop a previously bound callback (idempotent, by identity)."""
        self._callbacks = [bound for bound in self._callbacks if bound is not cb]

    def close(self) -> None:
        """Detach every callback. The channel stays usable.

        No ``_closed`` flag: ``ReactForever`` closes its subscription in a
        ``finally``, and a permanently dead channel would mean a driver that
        restarts never hears another connection.
        """
        self._callbacks = []

    def _fire(self, event: object) -> None:
        dead: list[Callable[[object], None]] = []
        for cb in tuple(self._callbacks):
            try:
                cb(event)
            except Exception:  # the far end is a dead loop or a dead process
                dead.append(cb)
        if dead:
            self._callbacks = [cb for cb in self._callbacks if not any(cb is gone for gone in dead)]


class WebServer:
    """Boot a ws server for the body's duration; bind it; stop it on the way out.

    Owns the sockets and nothing else -- there is no ``app`` kwarg, the UI
    program is a child of the tree.

    Args:
        static: the wheel that ships the compiled SPA, e.g. ``"nudle"``.
            None mounts nothing and exposes ``/ws`` alone.
        log_level: uvicorn log level. Defaults to ``"warning"`` -- we print
            our own ready/stopped banner.
        ready_timeout: how long ``asetup`` waits for uvicorn to come up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nustd.ui.web_server(static="nudle", port=8080),
        ...     body=program,
        ... )
    """

    # Uvicorn is booted on a task and readiness is awaited, so there is no
    # sync variant: a `Provide(WebServer, ...)` refuses to enter a sync tree.
    _nu_async_only = True

    def __init__(
        self,
        *,
        static: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        log_level: str = "warning",
        open_browser: bool = True,
        ready_timeout: float = 10.0,
        shutdown_timeout: float = 5.0,
    ) -> None:
        self._static = static
        self._host = host
        self._port = port
        self._log_level = log_level
        self._open_browser = open_browser
        self._ready_timeout = ready_timeout
        self._shutdown_timeout = shutdown_timeout
        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None
        self._sessions: dict[str, WsSession] = {}
        # Created once and handed out by reference. The backlog only works if
        # every caller of `on_connect()` gets the same object.
        self._connects = _Channel()
        self._disconnects = _Channel()

    # ---- lifecycle ----------------------------------------------------------

    async def asetup(self, ctx: Context) -> None:
        """Build the FastAPI app, boot uvicorn, wait for ``started``.

        A boot failure surfaces here instead of hanging: if the serve task
        finishes before ``server.started`` flips, we re-raise its exception.
        """
        del ctx
        config = uvicorn.Config(
            self._build_app(),
            host=self._host,
            port=self._port,
            log_level=self._log_level,
            access_log=False,
        )
        server = uvicorn.Server(config)
        task = asyncio.create_task(server.serve())
        deadline = asyncio.get_event_loop().time() + self._ready_timeout
        while not server.started and not task.done():
            if asyncio.get_event_loop().time() > deadline:
                # Try to shut down the half-booted server before propagating.
                server.should_exit = True
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
                msg = f"WebServer failed to start within {self._ready_timeout}s"
                raise TimeoutError(msg)
            await asyncio.sleep(0.05)
        if task.done():
            exc = task.exception()
            if exc is not None:
                raise exc
        self._server = server
        self._task = task
        self._print_ready()
        if self._open_browser:
            webbrowser.open(self._url())

    async def acleanup(self) -> None:
        """Signal ``should_exit``, await graceful stop, fall back to cancel."""
        server = self._server
        task = self._task
        if server is None or task is None:
            return
        server.should_exit = True
        if not task.done():
            try:
                await asyncio.wait_for(task, timeout=self._shutdown_timeout)
            except TimeoutError:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._server = None
        self._task = None
        self._sessions.clear()
        self._print_stopped()

    # ---- the connection book ------------------------------------------------

    def session(self, sid: str) -> WsSession | None:
        """The live transport for ``sid``, or None once the browser is gone."""
        return self._sessions.get(sid)

    def on_connect(self) -> _Channel:
        """The channel firing one sid per accepted ws connection."""
        return self._connects

    def on_disconnect(self) -> _Channel:
        """The channel firing one sid per closed ws connection."""
        return self._disconnects

    # ---- the http surface ---------------------------------------------------

    def _build_app(self) -> FastAPI:
        """The FastAPI app: ``/ws``, the telemetry config, and the SPA mount."""
        fastapi_app = FastAPI(title="nustd.ui")

        @fastapi_app.websocket("/ws")
        async def ws_endpoint(ws: WebSocket) -> None:
            # A session lives exactly as long as this coroutine: FastAPI closes
            # the socket the moment the handler returns. So accept, register,
            # drain intake until the browser goes away, unregister.
            await ws.accept()
            session = WsSession(ws)
            sid = uuid.uuid4().hex
            self._sessions[sid] = session
            self._connects.emit(sid)
            try:
                await session.run_intake()
            finally:
                self._sessions.pop(sid, None)
                self._disconnects.emit(sid)

        @fastapi_app.get("/api/telemetry-config")
        async def telemetry_config() -> dict[str, object]:
            from nu._config.telemetry import config_for_browser

            return config_for_browser()

        if self._static is not None:
            static_dir = _bundled_static(self._static)
            if static_dir is not None and static_dir.exists():
                fastapi_app.mount(
                    "/",
                    _SPAStatic(directory=static_dir, html=True),
                    name="static",
                )
        return fastapi_app

    # ---- banner -------------------------------------------------------------

    def _url(self) -> str:
        host = "localhost" if self._host in ("0.0.0.0", "127.0.0.1") else self._host  # noqa: S104
        return f"http://{host}:{self._port}"

    def _print_ready(self) -> None:
        render_header()
        color = color_enabled()
        ready = (
            paint("● ", fg=PURPLE, bold=True, enabled=color)
            + paint("Nu UI server running at ", bold=True, enabled=color)
            + paint(self._url(), fg=BLUE, underline=True, enabled=color)
        )
        print(ready, file=sys.stdout)  # noqa: T201
        print(paint("Ctrl+C to stop", dim=True, enabled=color), file=sys.stdout, flush=True)  # noqa: T201

    def _print_stopped(self) -> None:
        color = color_enabled()
        print(file=sys.stdout)  # noqa: T201
        print(paint("Nu UI server stopped", bold=True, enabled=color), file=sys.stdout, flush=True)  # noqa: T201

    def __repr__(self) -> str:
        return f"WebServer(host={self._host!r}, port={self._port!r})"


def web_server(
    *,
    static: str | None = "nudle",
    host: str = "127.0.0.1",
    port: int = 8080,
    log_level: str = "warning",
    open_browser: bool = True,
    ready_timeout: float = 10.0,
    shutdown_timeout: float = 5.0,
) -> Provide:
    """The bare server bracket: ``Provide(WebServer, {...})``, no body.

    For hand-assembled trees. Most callers want ``nustd.ui.serve`` instead,
    which stacks this with the session registry, the driver and the fold.
    Bodyless, so it belongs in a ``nu.With`` spec slot and nowhere else -- run
    standalone it compiles that empty slot to a literal and yields None.

    Args:
        static: the wheel shipping the compiled SPA. None serves ``/ws``
            alone, for a headless run or a separate vite dev server.
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. Default silences uvicorn's info chatter
            so only our own ready/stopped banner is printed.
        open_browser: open the bound URL in the default browser once ready.
        ready_timeout: how long ``asetup`` waits for uvicorn to come up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nustd.ui.web_server(port=8080),
        ...     body=program,
        ... )
    """
    return Provide(
        WebServer,
        {
            "static": static,
            "host": host,
            "port": port,
            "log_level": log_level,
            "open_browser": open_browser,
            "ready_timeout": ready_timeout,
            "shutdown_timeout": shutdown_timeout,
        },
    )
