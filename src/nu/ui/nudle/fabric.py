"""``NudleServer`` -- fabric that runs a nudle UI over ws for a body's duration.

Additive shape over ``build_fastapi_app`` -- same FastAPI + uvicorn stack,
wrapped as a plain FabricLifecycle so it drops into any ``Provide`` bracket.
``asetup`` builds the FastAPI app against the current ctx and boots uvicorn
on a background task, waiting until it's serving. ``acleanup`` signals
uvicorn to exit and awaits the task with a bounded timeout, falling back
to cancel.

Per-connection ctx binding (``Session`` on ws) stays inside ``ws_endpoint``.

Typical use goes through ``server(app, ...)`` (defined here) which wraps
a ``Provide(NudleServer, {...})`` for you.
"""

from __future__ import annotations

import asyncio
import webbrowser
from typing import TYPE_CHECKING

import uvicorn
from rich.console import Console
from rich.text import Text

from nu._branding import BLUE, PURPLE, render_header
from nu.context.fabric import Provide

from .serve import build_fastapi_app


_console = Console()


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["NudleServer", "server"]


class NudleServer:
    """Boot a nudle ws server through Provide's lifecycle.

    ``_nu_async_only = True``: uvicorn is booted on an ``asyncio.create_task``
    and the readiness poll awaits its ``started`` flag. There is no sync
    variant, so ``Provide(NudleServer, ...)`` refuses to enter a sync tree.

    Args:
        app: the nudle Nu program (Index + Refs + reactive flow).
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. Defaults to ``"warning"`` -- we print
            our own ready/stopped banner, so uvicorn's info chatter and
            per-request access log are silenced by default.
        open_browser: open the bound URL in the default browser once the
            server signals ready.
        ready_timeout: how long ``asetup`` waits for uvicorn to signal
            ``started`` before giving up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nu.kv.presets.rocksdb_navigator(".db"),
        ...     nu.ui.nudle.server(app, host="127.0.0.1", port=8080),
        ...     body=background_worker,
        ... )
    """

    _nu_async_only = True

    def __init__(
        self,
        app: Nu,
        *,
        host: str = "127.0.0.1",
        port: int = 8080,
        log_level: str = "warning",
        open_browser: bool = True,
        ready_timeout: float = 10.0,
        shutdown_timeout: float = 5.0,
    ) -> None:
        self._app = app
        self._host = host
        self._port = port
        self._log_level = log_level
        self._open_browser = open_browser
        self._ready_timeout = ready_timeout
        self._shutdown_timeout = shutdown_timeout
        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None

    async def asetup(self, ctx: Context) -> None:
        """Build the FastAPI app, boot uvicorn, wait for ``started``.

        A boot failure surfaces here instead of hanging: if the serve task
        finishes before ``server.started`` flips, we re-raise its exception.
        """
        fastapi_app = build_fastapi_app(self._app, ctx)
        config = uvicorn.Config(
            fastapi_app,
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
                msg = f"NudleServer failed to start within {self._ready_timeout}s"
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
        self._print_stopped()

    def _url(self) -> str:
        host = "localhost" if self._host in ("0.0.0.0", "127.0.0.1") else self._host  # noqa: S104
        return f"http://{host}:{self._port}"

    def _print_ready(self) -> None:
        render_header(_console)
        _console.print(
            Text.assemble(
                ("● ", f"bold {PURPLE}"),
                ("Nu UI server running at ", "bold"),
                (self._url(), f"{BLUE} underline"),
            ),
        )
        _console.print("[dim]Ctrl+C to stop[/dim]")

    def _print_stopped(self) -> None:
        _console.print()
        _console.print(Text("Nu UI server stopped", style="bold"))

    def __repr__(self) -> str:
        return f"NudleServer(host={self._host!r}, port={self._port!r})"


def server(
    app: Nu,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    log_level: str = "warning",
    open_browser: bool = True,
    ready_timeout: float = 10.0,
    shutdown_timeout: float = 5.0,
) -> Provide:
    """Boot a nudle ws server around a body: ``Provide(NudleServer, {...})``.

    Args:
        app: the nudle Nu program (Index + Refs + reactive flow).
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. Default silences uvicorn's info chatter
            so only nudle's own ready/stopped banner is printed.
        open_browser: open the bound URL in the default browser once ready.
        ready_timeout: how long ``asetup`` waits for uvicorn to signal
            ``started`` before giving up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nu.kv.presets.rocksdb_navigator(".db"),
        ...     nu.ui.nudle.server(app, host="127.0.0.1", port=8080),
        ...     body=background_worker,
        ... )
    """
    return Provide(
        NudleServer,
        {
            "app": app,
            "host": host,
            "port": port,
            "log_level": log_level,
            "open_browser": open_browser,
            "ready_timeout": ready_timeout,
            "shutdown_timeout": shutdown_timeout,
        },
    )
