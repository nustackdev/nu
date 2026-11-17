"""``serve`` -- the host's two layers stacked into one tree.

The ws server carrying the ui wire protocol, and a fold that runs one arm of
the ui program per connection the server holds open. Each layer is public on
its own for a hand-assembled tree; this is the arrangement that covers the
normal case. nudle adds its own telemetry config route to the server, which
the SPA reads before its one launch ping (see ``telemetry``), and by default
mounts the upload intake with its temp area (see ``nustd.ui.uploads``),
binding each arm its tab's view of that area.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nustd.blob.http.serving import serve_blobs
from nustd.ui.core.session import WsSession
from nustd.ui.uploads import upload_view
from nustd.ui.uploads import uploads as upload_pair
from nustd.ws_server import SID_ATTR, listen, run_once, session_for, sessions_fold

from . import telemetry


if TYPE_CHECKING:
    import os
    from collections.abc import Mapping, Sequence

    from starlette.routing import BaseRoute

    from nu.context.fabric import Provide
    from nu.lang import Nu
    from nustd.blob.http import BlobMount


__all__ = ["serve"]


def serve(
    program: Nu,
    *,
    static: str | None = "nudle",
    routes: Sequence[BaseRoute] = (),
    blobs: Mapping[BlobMount, Provide] | None = None,
    uploads: bool = True,
    upload_root: str | os.PathLike[str] | None = None,
    upload_cap: int | None = None,
    host: str = "127.0.0.1",
    port: int | None = None,
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
            own ``/api/telemetry-config`` and upload intake, and before the
            SPA mount.
        blobs: blob stores to serve too, each mount to the spec of its store
            (``nustd.blob.lmdb``, ``files`` or ``s3``): the server takes
            reads and uploads under each mount and holds each store open
            while it runs. The program binds the same specs to reach the
            stores. None serves no blobs.
        uploads: mount the upload intake and its temp area, and bind each
            arm its tab's view of it. False mounts no route, opens no area
            and binds no view, so the upload refs cannot read.
        upload_root: the folder the upload intake writes posted files to,
            made if missing and removed when the server stops. None picks a
            fresh ``nu-uploads-<hex>`` in the system temp dir.
        upload_cap: the most bytes one uploaded file may carry. None, the
            default, takes any size the disk holds.
        host: uvicorn bind host.
        port: the port to bind; taken, the server raises ``PortTaken``
            on the way up. None takes the first free one from 8080.
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
    blob_brackets, blob_routes = serve_blobs(blobs) if blobs else ([], [])
    arm = run_once(program)
    upload_brackets: list[Provide] = []
    upload_routes: Sequence[BaseRoute] = ()
    if uploads:
        upload_area, upload_routes = upload_pair(upload_root, cap=upload_cap)
        upload_brackets.append(upload_area)
        arm = upload_view(SID_ATTR, arm)
    return nu.With(
        *blob_brackets,
        listen(
            session_cls=WsSession,
            static=static,
            routes=(telemetry.route(), *upload_routes, *routes, *blob_routes),
            host=host,
            port=port,
            log_level=log_level,
            banner="Nu UI server",
            open_browser=open_browser,
            ready_timeout=ready_timeout,
            shutdown_timeout=shutdown_timeout,
        ),
        *upload_brackets,
        body=sessions_fold(session_for(SID_ATTR, arm)),
    )
