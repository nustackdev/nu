"""``serve`` -- the host's four layers stacked into one tree.

A store for the session registry, the ws server, a driver that turns sockets
into rows, and a fold that runs one arm of the ui program per row. Each layer
is public on its own for a hand-assembled tree; this is the arrangement that
covers the normal case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nustd.ui.server import (
    SID_ATTR,
    run_once,
    seed_sessions,
    session_driver,
    session_for,
    sessions_fold,
    sessions_store,
    web_server,
)


if TYPE_CHECKING:
    from nu.lang import Nu

    from .page import Index, Page


__all__ = ["serve"]


def serve(
    index: type[Index] | type[Page],
    program: Nu,
    *,
    static: str | None = "nudle",
    host: str = "127.0.0.1",
    port: int = 8080,
    log_level: str = "warning",
    open_browser: bool = True,
    ready_timeout: float = 10.0,
    shutdown_timeout: float = 5.0,
) -> Nu:
    """Serve ``program`` in the browser, one live arm per open tab.

    Never returns on its own -- the fold holds the tree open, so background
    work belongs in a sibling arm of a ``nu.ParallelAsync``. Goes in a
    ``body=`` slot and never in a ``nu.With`` spec slot, which would discard
    everything under it.

    Args:
        index: the Index, or the lone Page, whose slots seed the browser's
            tree.
        program: the ui program. Runs once per connection, with that tab's
            Session bound. Returning or raising stops that tab; a raise is
            reported on stdout.
        static: the wheel shipping the compiled SPA. None serves ``/ws``
            alone, for a headless run or a separate vite dev server.
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. The default silences uvicorn's own
            chatter so only the ready / stopped banner is printed.
        open_browser: open the bound URL once the server signals ready.
        ready_timeout: how long to wait for uvicorn to come up.
        shutdown_timeout: how long to wait for it to go down gracefully.

    Example:
        >>> app = nu.With(
        ...     nustd.kv.rocksdb_navigator(".db"),
        ...     body=nu.ParallelAsync(
        ...         nustd.ui.serve(App, ui),
        ...         nustd.kv.auto_flow_atomic(tick),
        ...     ),
        ... )
    """
    return nu.With(
        # Order is for the banner only: the store opens first and the server
        # last, so "running at http://..." is the last line before the body.
        sessions_store(),
        web_server(
            static=static,
            host=host,
            port=port,
            log_level=log_level,
            open_browser=open_browser,
            ready_timeout=ready_timeout,
            shutdown_timeout=shutdown_timeout,
        ),
        body=seed_sessions()
        >> nu.ParallelAsync(
            session_driver(),
            sessions_fold(session_for(SID_ATTR, run_once(index.boot() >> program))),
        ),
    )
