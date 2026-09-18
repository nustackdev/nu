"""``listen`` -- the server bracket, ready to drop in a ``nu.With`` spec slot."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import Provide

from .fabric import SessionProtocol, WebServer


if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import WebSocket


__all__ = ["listen"]


def listen(
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
) -> Provide:
    """The bare server bracket: ``Provide(WebServer, {...})``, no body.

    For hand-assembled trees. Stack it with ``sessions_fold`` to get one live
    arm per connection. Bodyless, so it belongs in a ``nu.With`` spec slot and
    nowhere else -- run standalone it compiles that empty slot to a literal and
    yields None.

    Args:
        session_cls: built once per accepted socket, with the ``WebSocket`` as
            its only argument. Owns the wire format end to end.
        static: the wheel shipping the compiled SPA. None serves ``/ws``
            alone, for a headless run or a separate vite dev server.
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. Default silences uvicorn's info chatter
            so only our own ready/stopped banner is printed.
        banner: what the ready and stopped lines call this server.
        open_browser: open the bound URL in the default browser once ready.
        ready_timeout: how long ``asetup`` waits for uvicorn to come up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nustd.ws_server.listen(session_cls=EchoSession, port=8080),
        ...     body=program,
        ... )
    """
    return Provide(
        WebServer,
        {
            "session_cls": session_cls,
            "static": static,
            "host": host,
            "port": port,
            "log_level": log_level,
            "banner": banner,
            "open_browser": open_browser,
            "ready_timeout": ready_timeout,
            "shutdown_timeout": shutdown_timeout,
        },
    )
