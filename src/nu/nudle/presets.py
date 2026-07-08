"""Nudle topological presets.

Bracket factories that drop into a ``nu.With(...)`` tree. Same shape as
``nu.v.presets``: each returns a ``Provide(...)`` wired to the right fabric
so callers don't repeat the boilerplate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import Provide

from .fabric import NudleServer


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["server"]


def server(
    app: Nu,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    log_level: str = "info",
    ready_timeout: float = 10.0,
    shutdown_timeout: float = 5.0,
) -> Provide:
    """Boot a nudle ws server around a body: ``Provide(NudleServer, {...})``.

    Args:
        app: the nudle Nu program (Index + Refs + reactive flow).
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level.
        ready_timeout: how long ``asetup`` waits for uvicorn to signal
            ``started`` before giving up.
        shutdown_timeout: how long ``acleanup`` waits for graceful exit
            before cancelling the task.

    Example:
        >>> nu.With(
        ...     nu.v.presets.rocksdb_navigator_inmemory(".db"),
        ...     nu.nd.presets.server(app, host="127.0.0.1", port=8080),
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
            "ready_timeout": ready_timeout,
            "shutdown_timeout": shutdown_timeout,
        },
    )
