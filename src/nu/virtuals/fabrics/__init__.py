"""nu.virtuals.fabrics - ``FabricLifecycle`` classes for the virtuals stack.

Nu-tree provisioning for the four virtuals concepts:

- ``Codec`` (plain Fabric, no lifecycle) - key + value serialization.
  Preset kwargs helpers: ``binary_kwargs``, ``noop_kwargs``, ``text_kwargs``,
  ``msgpack_kwargs``.
- ``InMemoryObserver`` / ``RedisObserver`` - change notifications. Read
  ``Codec`` from ctx at setup.
- ``InMemoryStorage`` / ``RocksDBStorage`` / ``TextStorage`` - backing
  stores. Read ``Codec`` and observer from ctx at setup.
- ``Navigator`` - top-level entry to storage. Reads Storage from ctx by
  ``storage_type`` (defaults to RocksDB).

Typical stack::

    Provide(Codec, binary_kwargs(),
        Provide(InMemoryObserver, {},
            Provide(RocksDBStorage, {"path": "/data/main"},
                Provide(Navigator, {},
                    body,   # ctx.get(Navigator) available here
                ),
            ),
        ),
    )
"""

from __future__ import annotations

from .codec import Codec, binary_kwargs, msgpack_kwargs, noop_kwargs, text_kwargs
from .navigator import Navigator
from .observer import InMemoryObserver, RedisObserver
from .storage import InMemoryStorage, LMDBStorage, RocksDBStorage, TextStorage


__all__ = [
    "Codec",
    "InMemoryObserver",
    "InMemoryStorage",
    "LMDBStorage",
    "Navigator",
    "RedisObserver",
    "RocksDBStorage",
    "TextStorage",
    "binary_kwargs",
    "msgpack_kwargs",
    "noop_kwargs",
    "text_kwargs",
]
