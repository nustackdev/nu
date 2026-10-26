"""``serve`` -- the host's two layers stacked into one tree.

The ws server carrying the ui wire protocol, and a fold that runs one arm of
the ui program per connection the server holds open. Each layer is public on
its own for a hand-assembled tree; this is the arrangement that covers the
normal case. nudle adds its own telemetry route to the server and fires its
first-run ping when the tree is entered (see ``telemetry``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nustd.ui.core.session import WsSession
from nustd.ws_server import SID_ATTR, listen, run_once, session_for, sessions_fold

from . import telemetry


if TYPE_CHECKING:
    from collections.abc import Sequence

    from starlette.routing import BaseRoute

    from nu.lang import Nu


__all__ = ["serve"]


def serve(
    program: Nu,
    *,
    static: str | None = "nudle",
    routes: Sequence[BaseRoute] = (),
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

    The program draws the whole tab, so it starts with ``nustd.ui.boot``,
    which clears what the browser held from an earlier connection and brings
    up what is always there. Until something lands, the browser shows
    "waiting for the tree...".

    Args:
        program: the ui program. Runs once per connection, with that tab's
            Session bound. Returning or raising stops that tab; a raise is
            reported on stdout.
        static: the wheel shipping the compiled SPA. None serves ``/ws``
            alone, for a headless run or a separate vite dev server.
        routes: extra Starlette routes for the server, served after nudle's
            own ``/api/telemetry-config`` and before the SPA mount.
        host: uvicorn bind host.
        port: uvicorn bind port.
        log_level: uvicorn log level. The default silences uvicorn's own
            chatter so only the ready / stopped banner is printed.
        open_browser: open the bound URL once the server signals ready.
        ready_timeout: how long to wait for uvicorn to come up.
        shutdown_timeout: how long to wait for it to go down gracefully.

    Example:
        app = nu.With(
            nustd.kv.rocksdb_navigator(".db"),
            body=nu.ParallelAsync(
                nustd.ui.serve(nustd.ui.boot(App.home) >> ui),
                nustd.kv.auto_flow_atomic(tick),
            ),
        )
    """
    return nu.With(
        nu.Provide(telemetry.FirstRun),
        listen(
            session_cls=WsSession,
            static=static,
            routes=(telemetry.route(), *routes),
            host=host,
            port=port,
            log_level=log_level,
            banner="Nu UI server",
            open_browser=open_browser,
            ready_timeout=ready_timeout,
            shutdown_timeout=shutdown_timeout,
        ),
        body=sessions_fold(
            session_for(
                SID_ATTR,
                run_once(program),
            ),
        ),
    )
