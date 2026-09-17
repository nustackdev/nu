"""nudle -- the browser host: Index / Page, the boot term, the serve preset.

The python host is three layers now. A server fabric boots uvicorn and owns
the sockets, and never sees the program. A Nu driver relays connections into
a kv shape, one row per live tab. And the program runs as one arm per row,
under a fold, with that tab's session bound.

``Index`` / ``Page`` / ``PageRef`` and the ``Boot`` term live here, and
``serve`` stacks the three layers into one tree. The wire protocol and the
shared ws session live in ``nustd.ui.core``; the server side lives in
``nustd.ui.server``. The Vite SPA + PyPI wheel that ships the compiled
bundle live under ``nu/ui/web/nudle/``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nustd.ui.core import Append, Changed, Frame, Subscription, Write, decode, encode
from nustd.ui.server import (
    SID_ATTR,
    seed_sessions,
    session_driver,
    session_for,
    sessions_fold,
    sessions_store,
    web_server,
)

from .page import Boot, Index, Page, PageRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
    "Append",
    "Boot",
    "Changed",
    "Frame",
    "Index",
    "Page",
    "PageRef",
    "Subscription",
    "Write",
    "decode",
    "encode",
    "serve",
]


#: How long a finished program's arm sits idle before it would wake up. The
#: number barely matters -- what matters is that the arm outlives the program,
#: see the comment in ``serve``.
_PARK = 3600.0


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

    The program is a child of this tree, not a payload of a bracket. What
    that buys: anything walking the tree can see it, one connection's arm
    dying cannot touch another's socket, and a closed socket cancels exactly
    the arm that was drawing it.

    Args:
        index: the Index (or the lone Page) whose slots seed the browser's
            tree. Named rather than searched for -- the fabric never sees
            the program, so there is nothing to walk.
        program: the ui program. Runs once per connection, with that tab's
            Session bound.
        static: the wheel shipping the compiled SPA. None serves ``/ws``
            alone, for a headless run or a separate vite dev server.
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. The default silences uvicorn's own
            chatter so only the ready / stopped banner is printed.
        open_browser: open the bound URL once the server signals ready.
        ready_timeout: how long to wait for uvicorn to come up.
        shutdown_timeout: how long to wait for it to go down gracefully.

    Notes:
        - Never returns on its own. The fold holds the tree open, so a
          caller wanting background work runs it as a sibling arm of a
          ``nu.ParallelAsync``, not as a ``body=``.
        - Goes in a ``body=`` slot, never a ``nu.With`` spec slot. It is a
          whole tree, and ``With`` discards a nested bracket's own body.

    Example:
        >>> app = nu.With(
        ...     nustd.kv.rocksdb_navigator(".db"),
        ...     body=nu.ParallelAsync(
        ...         nustd.ui.serve(App, ui),
        ...         nustd.kv.auto_flow_atomic(tick),
        ...     ),
        ... )
    """
    arm = session_for(
        SID_ATTR,
        # Parked on purpose: the arm's life is the connection's, not the
        # program's. A program that returns would be swept as done and born
        # again on the next reconcile -- so opening a second tab would re-boot
        # the first one, clearing its tree and re-running it from the top.
        index.boot() >> program >> nu.ForeverDo(nu.Delay(_PARK)),
    )
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
        body=seed_sessions() >> nu.ParallelAsync(session_driver(), sessions_fold(arm)),
    )
