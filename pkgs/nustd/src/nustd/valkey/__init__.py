"""nustd.valkey - a private Valkey server, as one fabric.

Cross-process kv change notifications ride Redis pub/sub
(``nustd.kv.sqlite_navigator_redis`` and friends). This fabric makes sure
there is a Redis-protocol server to ride on without anyone installing one: the
host brings up the ``valkey-server`` binary bundled in the ``valkeylite``
wheel, private to one data dir, on a unix socket.

- ``ValkeyServer`` - the resource. Setup reaps a server a crashed owner left
  behind, starts a fresh one and returns once it answers ``PING``. Cleanup
  stops it. A watchdog stops it too if the owner dies without cleanup.
- ``ValkeyRef`` - the fabric ref, with the fluent ``url()`` / ``ping()``.
- ``Url`` / ``Ping`` - the interactions, both reads.
- ``server(data_dir)`` - the preset ``Provide``.
- ``url_for(data_dir)`` - the server's address, known before it starts::

    d = ".nu/valkey"
    app = nu.With(
        nustd.valkey.server(d),
        nustd.kv.sqlite_navigator_redis(".nu/kv.sqlite", redis_url=nustd.valkey.url_for(d)),
        body=program,
    )

Importing this module pulls nothing beyond the stdlib; ``valkeylite`` is
reached for only when a server starts, so a worker that only needs the URL
does not need the extra installed.
"""

from __future__ import annotations

from . import presets
from .interactions import Ping, Url
from .presets import server
from .refs import ValkeyRef
from .resources import ValkeyInUse, ValkeyServer, ValkeyStartupError, socket_path_for, url_for


__all__ = [
    "Ping",
    "Url",
    "ValkeyInUse",
    "ValkeyRef",
    "ValkeyServer",
    "ValkeyStartupError",
    "presets",
    "server",
    "socket_path_for",
    "url_for",
]
