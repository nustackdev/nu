"""nu.proxy - transparent RPC transport for fabrics.

Pure transport. No new refs, no new interactions - method calls on a client
proxy go over the wire and land on the server-side bound fabric. Same
fabric dispatch (``FabricRef``) that works locally works remotely.

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

from invisibles.core.boxing import register_value_type

from .client import InvisiblesClient
from .proxy import InvisiblesProxy
from .server import InvisiblesServer


# Register nu.kv path types as invisibles value types so they serialize by value.
try:
    from nu.kv.paths import ValuePathSer, ViewPathSer

    register_value_type(ViewPathSer, ValuePathSer)
except ImportError:
    pass


__all__ = ["InvisiblesClient", "InvisiblesProxy", "InvisiblesServer"]
