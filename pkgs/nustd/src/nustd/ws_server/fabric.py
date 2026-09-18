"""``WebServer`` -- the uvicorn lifecycle and the registry of live connections.

Boots uvicorn behind a FastAPI app with a ``/ws`` endpoint and a static mount,
binds itself to the Context, and stops uvicorn on the way out. It never sees
the program a connection runs: that is a child of the tree, one arm per live
connection, and the protocol on the wire is the session class's business.

The two halves it does own:

- the connection book, ``sid -> _Connection``, holding each live transport and
  whether the program for it has ended. The whole registry is this dict: it is
  process-local, it dies with the process, and the fold reads it directly.
- one ordered channel announcing every move of that book, which is what wakes
  the fold.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
import uuid
import warnings
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from nu._config.branding import BLUE, PURPLE, color_enabled, paint, render_header


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Context


__all__ = ["SessionProtocol", "WebServer"]


class SessionProtocol(Protocol):
    """All the server asks of a session: a read loop that ends with the socket.

    The session owns the wire format, so ``run_intake`` returning is what the
    server reads as "this connection is over". A class carrying ``_nu_bind_as``
    is bound under that type inside an arm, otherwise under itself.
    """

    async def run_intake(self) -> None: ...


async def _adrain(task: asyncio.Task) -> None:
    """Await a task we just cancelled, swallowing its outcome and nothing else.

    A ``CancelledError`` is re-raised unless the task itself is the one that
    was cancelled, so being cancelled while waiting here still ends us.
    """
    try:
        await task
    except asyncio.CancelledError:
        if not task.cancelled():
            raise
    except Exception:  # uvicorn is on its way out either way
        pass


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
            "bundle package). SPA mount skipped; only /ws is exposed. Rename "
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


class _Connection:
    """One live ws connection: its transport, and whether its program has ended.

    Presence in the book is what the fold folds over; ``done`` is what a
    respawned arm reads to become a no-op.
    """

    __slots__ = ("done", "session")

    def __init__(self, session: SessionProtocol) -> None:
        self.session = session
        self.done = False


class _Subscription:
    """One subscriber's handle on the connection channel.

    ``bind`` / ``unbind`` / ``close`` is the whole reactive contract Nu's
    atoms drive, so a plain fan-out object is a first-class change source.
    Closing detaches this handle alone. Callbacks are compared by identity and
    a raising one is dropped -- the far end is usually a queue in a loop that
    may already be gone.
    """

    def __init__(self, channel: _Channel) -> None:
        self._channel = channel
        self._callbacks: list[Callable[[object], None]] = []
        self._closed = False

    def bind(self, cb: Callable[[object], None]) -> None:
        """Register ``cb`` to fire on every event this channel carries."""
        if self._closed:
            return
        if not any(cb is bound for bound in self._callbacks):
            self._callbacks.append(cb)

    def unbind(self, cb: Callable[[object], None]) -> None:
        """Drop a previously bound callback (idempotent, by identity)."""
        self._callbacks = [bound for bound in self._callbacks if bound is not cb]

    def close(self) -> None:
        """Detach from the channel; further ``bind`` calls no-op."""
        if self._closed:
            return
        self._closed = True
        self._callbacks = []
        self._channel._drop(self)

    def _fire(self, event: object) -> None:
        dead: list[Callable[[object], None]] = []
        for cb in tuple(self._callbacks):
            try:
                cb(event)
            except Exception:  # the far end is a dead loop or a dead process
                dead.append(cb)
        if dead:
            self._callbacks = [cb for cb in self._callbacks if not any(cb is gone for gone in dead)]


class _Channel:
    """Fan-out over the one moment the server announces: the book moved.

    Opening and closing ride the same ordered channel, so the two events for
    one sid reach every subscriber in the order they happened. Nothing is
    buffered and nothing is replayed: a subscriber reconciles against the
    book, which already holds whatever landed before it subscribed.
    """

    def __init__(self) -> None:
        self._subs: list[_Subscription] = []

    def subscribe(self) -> _Subscription:
        """A fresh handle, independent of every other subscriber's."""
        sub = _Subscription(self)
        self._subs.append(sub)
        return sub

    def emit(self, event: object) -> None:
        """Announce one sid to everyone currently subscribed."""
        for sub in tuple(self._subs):
            sub._fire(event)

    def _drop(self, sub: _Subscription) -> None:
        self._subs = [s for s in self._subs if s is not sub]


class WebServer:
    """Boot a ws server for the body's duration; bind it; stop it on the way out.

    Owns the sockets and nothing else -- there is no ``app`` kwarg, the program
    a connection runs is a child of the tree.

    Args:
        session_cls: built once per accepted socket, with the ``WebSocket`` as
            its only argument. Its ``run_intake`` is what holds the connection
            open, and its ``_nu_bind_as`` is what an arm binds it under.
        static: the importable wheel that ships a compiled SPA under
            ``build/``. None mounts nothing and exposes ``/ws`` alone.
        log_level: uvicorn log level. Defaults to ``"warning"`` -- we print
            our own ready/stopped banner.
        banner: what the ready and stopped lines call this server.
        ready_timeout: how long ``asetup`` waits for uvicorn to come up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nustd.ws_server.listen(session_cls=EchoSession, port=8080),
        ...     body=program,
        ... )
    """

    # Uvicorn is booted on a task and readiness is awaited, so there is no
    # sync variant: a `Provide(WebServer, ...)` refuses to enter a sync tree.
    _nu_async_only = True

    def __init__(
        self,
        *,
        session_cls: Callable[[WebSocket], SessionProtocol],
        static: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        log_level: str = "warning",
        banner: str = "Nu ws server",
        open_browser: bool = True,
        ready_timeout: float = 10.0,
        shutdown_timeout: float = 5.0,
    ) -> None:
        self._session_cls = session_cls
        self._static = static
        self._host = host
        self._port = port
        self._log_level = log_level
        self._banner = banner
        self._open_browser = open_browser
        self._ready_timeout = ready_timeout
        self._shutdown_timeout = shutdown_timeout
        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None
        self._connections: dict[str, _Connection] = {}
        self._channel = _Channel()

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
                await _adrain(task)
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
                await _adrain(task)
        self._server = None
        self._task = None
        self._connections.clear()
        self._print_stopped()

    # ---- the connection book ------------------------------------------------

    def session(self, sid: str) -> SessionProtocol | None:
        """The live transport for ``sid``, or None once the client is gone."""
        conn = self._connections.get(sid)
        return None if conn is None else conn.session

    def live_ids(self) -> list[str]:
        """The sid of every connection currently open, in arrival order."""
        return list(self._connections)

    def is_done(self, sid: str) -> bool:
        """Whether the program for ``sid`` has already ended."""
        conn = self._connections.get(sid)
        return conn is not None and conn.done

    def mark_done(self, sid: str) -> None:
        """Record that the program for ``sid`` has ended. A closed sid is a miss."""
        conn = self._connections.get(sid)
        if conn is not None:
            conn.done = True

    def subscribe(self) -> _Subscription:
        """A handle firing one sid every time a connection opens or closes."""
        return self._channel.subscribe()

    # ---- the http surface ---------------------------------------------------

    def _build_app(self) -> FastAPI:
        """The FastAPI app: ``/ws``, the telemetry config, and the SPA mount."""
        fastapi_app = FastAPI(title="nustd.ws_server")

        @fastapi_app.websocket("/ws")
        async def ws_endpoint(ws: WebSocket) -> None:
            # A session lives exactly as long as this coroutine: FastAPI closes
            # the socket the moment the handler returns. So accept, register,
            # drain intake until the client goes away, unregister.
            await ws.accept()
            conn = _Connection(self._session_cls(ws))
            sid = uuid.uuid4().hex
            self._connections[sid] = conn
            self._channel.emit(sid)
            try:
                await conn.session.run_intake()
            finally:
                self._connections.pop(sid, None)
                self._channel.emit(sid)

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
            + paint(f"{self._banner} running at ", bold=True, enabled=color)
            + paint(self._url(), fg=BLUE, underline=True, enabled=color)
        )
        print(ready, file=sys.stdout)  # noqa: T201
        print(paint("Ctrl+C to stop", dim=True, enabled=color), file=sys.stdout, flush=True)  # noqa: T201

    def _print_stopped(self) -> None:
        color = color_enabled()
        print(file=sys.stdout)  # noqa: T201
        stopped = paint(f"{self._banner} stopped", bold=True, enabled=color)
        print(stopped, file=sys.stdout, flush=True)  # noqa: T201

    def __repr__(self) -> str:
        return f"WebServer(host={self._host!r}, port={self._port!r})"
