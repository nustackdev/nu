"""nu.kv.fabrics - ``FabricLifecycle`` classes for the virtuals stack.

Nu-tree provisioning for the virtuals concepts:

- ``Codec`` (plain Fabric, no lifecycle) - key + value serialization.
  Preset kwargs helpers: ``binary_kwargs``, ``noop_kwargs``, ``text_kwargs``,
  ``msgpack_kwargs``.
- ``InMemoryTransport`` - shared in-process pub/sub bus for the mem
  publisher/observer pair. Trivial lifecycle.
- ``InMemoryPublisher`` / ``RedisPublisher`` - write-side change routers.
  Attached to Storage via ``publisher_type=``.
- ``InMemoryObserver`` / ``RedisObserver`` - read-side change consumers.
  Bound at process scope; ``nu.reactive`` queries look them up under
  ``ObserverProtocol``.
- ``InMemoryStorage`` / ``RocksDBStorage`` / ``LMDBStorage`` / ``TextStorage``
  - backing stores. Read ``Codec`` and their publisher from ctx.
- ``Navigator`` - top-level entry to storage. Reads Storage from ctx by
  ``storage_type`` (defaults to RocksDB).

Typical stack::

    Provide(Codec, binary_kwargs(),
        Provide(InMemoryTransport, {},
            Provide(InMemoryPublisher, {},
                Provide(InMemoryObserver, {},
                    Provide(RocksDBStorage, {"path": "/data/main"},
                        Provide(Navigator, {},
                            body,   # ctx.get(Navigator) available here
                        ),
                    ),
                ),
            ),
        ),
    )
"""

from __future__ import annotations

from .codec import Codec, binary_kwargs, msgpack_kwargs, noop_kwargs, text_kwargs
from .navigator import Navigator
from .observer import InMemoryObserver, RedisObserver
from .publisher import InMemoryPublisher, RedisPublisher
from .storage import InMemoryStorage, LMDBStorage, RocksDBStorage, TextStorage
from .transport import InMemoryTransport


__all__ = [
    "Codec",
    "InMemoryObserver",
    "InMemoryPublisher",
    "InMemoryStorage",
    "InMemoryTransport",
    "LMDBStorage",
    "Navigator",
    "RedisObserver",
    "RedisPublisher",
    "RocksDBStorage",
    "TextStorage",
    "binary_kwargs",
    "msgpack_kwargs",
    "noop_kwargs",
    "text_kwargs",
]
