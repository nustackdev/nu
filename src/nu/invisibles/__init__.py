"""nu.invisibles - transparent RPC transport for fabrics.

Pure transport. No new refs, no new interactions - method calls on a client
proxy go over the wire and land on the server-side bound fabric. Same
fabric dispatch (``FabricRef`` + ``method_query`` / ``method_action`` /
``method_command``) that works locally works remotely.

- ``InvisiblesServer`` - reads the root fabric from ctx (by type + optional
  tag) and serves it over TCP / Unix socket.
- ``InvisiblesClient`` - connects and exposes the remote root as ``.root``.
- ``InvisiblesProxy`` - bracket sugar that provisions a client and binds its
  ``.root`` under a caller-named fabric type in one step.

Typical topology, using ``feed_run``'s ledger-main pattern::

    # Server side (inside a Ray worker actor typically)
    Provide(RocksDBStorage, {"path": "/data/ledger-main", "codec": ...},
        Provide(Navigator, {"root_view": DictView},
            Provide(InvisiblesServer, {"target": Navigator,
                                       "address": "10.0.0.1:19000"},
                serve_forever_body,
            ),
        ),
    )

    # Client side (driver)
    InvisiblesProxy(Navigator, address="10.0.0.1:19000",
        driver_body,
    )
"""

from __future__ import annotations

from .client import InvisiblesClient
from .proxy import InvisiblesProxy
from .server import InvisiblesServer


__all__ = ["InvisiblesClient", "InvisiblesProxy", "InvisiblesServer"]
