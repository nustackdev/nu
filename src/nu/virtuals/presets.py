"""Storage topological presets.

Two forms, both live and independent:

- Imperative context managers (``memory_storage``, ``rocksdb_storage_redis``,
  ``rocksdb_storage``, ``lmdb_storage``, ``text_storage``) yield a
  ready ``StorageProtocol`` for hand-wired Contexts.
- Bracket factories (``memory_navigator``, ``rocksdb_navigator_redis``,
  ``rocksdb_navigator``, ``text_navigator``, ``inmem_observer``,
  ``redis_observer``) return a single ``_LifecycleBracket`` that drops
  into a ``nu.With(...)`` tree and binds the whole Codec + Transport +
  Publisher + Observer + Storage + Navigator stack on ctx. Internally
  they compose ``Provide`` peers under a ``With``, so ctx-bind order and
  LIFO teardown come for free.

Every navigator preset binds the triple (Transport + Publisher + Observer)
plus Storage (with matching ``publisher_type=``) plus Navigator. Redis presets
bind Redis Publisher + Redis Observer alongside the InMemoryTransport (LMDB
envs living in the same actor may still resolve their default in-mem
publisher).

Standalone observer presets (``inmem_observer``, ``redis_observer``) exist
for read-only actors that consume notifications without owning a
publishing storage.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from nu.context.fabric import With
    from virtuals.tkv.storage import StorageProtocol


__all__ = [
    "inmem_observer",
    "lmdb_navigator",
    "lmdb_navigator_redis",
    "lmdb_storage",
    "memory_navigator",
    "memory_storage",
    "redis_observer",
    "rocksdb_navigator",
    "rocksdb_navigator_redis",
    "rocksdb_storage",
    "rocksdb_storage_redis",
    "text_navigator",
    "text_storage",
]


@contextmanager
def memory_storage() -> Generator[StorageProtocol, None, None]:
    """Create in-memory storage with no-op codec and in-memory publisher.

    No persistence, no serialization: Python objects stored as-is.
    Useful for testing, prototyping, and ephemeral service handles.

    Yields:
        Configured in-memory storage instance
    """
    from virtuals.codecs import NoOpCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.mem import InMemoryStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        InMemoryStorage(
            codec=NoOpCodec(),
            publisher=publisher,
        ) as storage,
    ):
        yield storage


@contextmanager
def lmdb_storage(
    path: str,
    read_only: bool = False,
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_readers: int = 126,
    subdir: bool = True,
    sync: bool = True,
) -> Generator[StorageProtocol, None, None]:
    """Create LMDB storage with binary codec and in-memory publisher.

    Args:
        path: Path to LMDB env (directory if subdir=True, file otherwise).
        read_only: Open the environment read-only.
        map_size: Maximum on-disk size in bytes. Default 10 GiB.
        max_readers: Maximum concurrent reader slots.
        subdir: If True, treat `path` as a directory; if False, as the env file.
        sync: If True, fsync data pages after each commit.

    Yields:
        Configured LMDB storage instance.
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.lmdb import LMDBStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        LMDBStorage(
            path=path,
            codec=BinaryCodec(),
            publisher=publisher,
            read_only=read_only,
            map_size=map_size,
            max_readers=max_readers,
            subdir=subdir,
            sync=sync,
        ) as storage,
    ):
        yield storage


@contextmanager
def text_storage(path: str) -> Generator[StorageProtocol, None, None]:
    """Create text storage with text codec and in-memory publisher.

    Args:
        path: Path for text storage directory

    Yields:
        Configured text storage instance
    """
    from virtuals.codecs import TextCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.textdb import TextStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        TextStorage(
            path=path,
            codec=TextCodec(),
            publisher=publisher,
        ) as storage,
    ):
        yield storage


@contextmanager
def rocksdb_storage(
    path: str,
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and in-memory publisher.

    Args:
        path: Path to RocksDB database directory
        read_only: Open database in read-only mode
        secondary_path: Path to secondary RocksDB instance
        secondary_refresh_interval: Interval in seconds for background
            try_catch_up_with_primary on secondary DBs. None disables.

    Yields:
        Configured RocksDB storage instance
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.rocksdb import RocksDBStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            publisher=publisher,
            read_only=read_only,
            secondary_path=secondary_path,
            secondary_refresh_interval=secondary_refresh_interval,
        ) as storage,
    ):
        yield storage


@contextmanager
def rocksdb_storage_redis(
    path: str,
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "__every__",
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and Redis publisher.

    Args:
        path: Path to RocksDB database directory
        read_only: Permissions
        secondary_path: Open as secondary rocksdb storage
        secondary_refresh_interval: Interval in seconds for background
            try_catch_up_with_primary on secondary DBs. None disables.
        redis_url: Redis service url
        channel_prefix: Redis channel prefix

    Yields:
        Configured RocksDB storage instance
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.publishers.redis_pubsub import RedisPublisher
    from virtuals.storages.rocksdb import RocksDBStorage

    with (
        RedisPublisher(
            redis_url=redis_url,
            channel_prefix=channel_prefix,
        ) as publisher,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            publisher=publisher,
            read_only=read_only,
            secondary_path=secondary_path,
            secondary_refresh_interval=secondary_refresh_interval,
        ) as storage,
    ):
        yield storage


# =========================================================================
# Bracket-form presets: drop into a ``nu.With(...)`` tree.
#
# Each factory returns a single ``With`` bracket that peers ``Provide``s the
# whole Codec + Transport + Publisher + Observer + Storage (+ Navigator)
# stack. Same order and LIFO teardown as a hand-written
# ``With(Provide(Codec, ...), Provide(InMemoryTransport, ...), ...)``.
#
# ``tags=`` folds onto both the Storage and Navigator bindings so a shard
# picks its storage via ``storage_tags=`` and binds the Navigator under the
# same tag - matching the citadel per-shard pattern.
# =========================================================================


def memory_navigator(
    *,
    tags: Sequence[object] = (),
) -> With:
    """In-mem Codec + Transport + Publisher + Observer + Storage + Navigator as one bracket.

    No persistence, no serialization -- Python objects go through NoOpCodec.
    Useful for tests, examples, and ephemeral service handles.

    Args:
        tags: fold onto the Storage and Navigator bindings.
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryStorage,
        InMemoryTransport,
        Navigator,
        noop_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, noop_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(InMemoryStorage, {}, tags=tags),
        Provide(
            Navigator,
            {"storage_type": InMemoryStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def rocksdb_navigator(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
    disable_wal: bool = False,
    options: dict | None = None,
) -> With:
    """RocksDB + in-mem Transport/Publisher/Observer + Navigator as one bracket.

    Binary codec, in-process publisher/observer, transactional persistence.
    The 99% site for a per-shard rocksdb stack when you don't need
    cross-process change notifications.
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryTransport,
        Navigator,
        RocksDBStorage,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(
            RocksDBStorage,
            {
                "path": path,
                "read_only": read_only,
                "secondary_path": secondary_path,
                "secondary_refresh_interval": secondary_refresh_interval,
                "disable_wal": disable_wal,
                "options": options,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": RocksDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def rocksdb_navigator_redis(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
    disable_wal: bool = False,
    options: dict | None = None,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "__every__",
) -> With:
    """RocksDB + Redis Publisher/Observer + Navigator as one bracket.

    Same as ``rocksdb_navigator`` but with the Redis publisher/observer pair
    for cross-process change notifications. Requires a reachable Redis at
    ``redis_url`` at asetup time.
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        Navigator,
        RedisObserver,
        RedisPublisher,
        RocksDBStorage,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(
            RedisPublisher,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RocksDBStorage,
            {
                "path": path,
                "publisher_type": RedisPublisher,
                "read_only": read_only,
                "secondary_path": secondary_path,
                "secondary_refresh_interval": secondary_refresh_interval,
                "disable_wal": disable_wal,
                "options": options,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": RocksDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def text_navigator(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    log_operations: bool = False,
) -> With:
    """Text (JSON) storage + in-mem Transport/Publisher/Observer + Navigator as one bracket."""
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryTransport,
        Navigator,
        TextStorage,
        text_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, text_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(
            TextStorage,
            {
                "path": path,
                "read_only": read_only,
                "log_operations": log_operations,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": TextStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def lmdb_navigator(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_readers: int = 126,
    subdir: bool = True,
    sync: bool = True,
) -> With:
    """LMDB + in-mem Transport/Publisher/Observer + Navigator as one bracket."""
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryTransport,
        LMDBStorage,
        Navigator,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(
            LMDBStorage,
            {
                "path": path,
                "read_only": read_only,
                "map_size": map_size,
                "max_readers": max_readers,
                "subdir": subdir,
                "sync": sync,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": LMDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def lmdb_navigator_redis(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_readers: int = 126,
    subdir: bool = True,
    sync: bool = True,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "nu",
) -> With:
    """LMDB + Redis Publisher/Observer + Navigator as one bracket."""
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        LMDBStorage,
        Navigator,
        RedisObserver,
        RedisPublisher,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(
            RedisPublisher,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            LMDBStorage,
            {
                "path": path,
                "publisher_type": RedisPublisher,
                "read_only": read_only,
                "map_size": map_size,
                "max_readers": max_readers,
                "subdir": subdir,
                "sync": sync,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": LMDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


# =========================================================================
# Standalone Observer presets: read-only actors that consume notifications
# without owning a publishing storage.
# =========================================================================


def inmem_observer() -> With:
    """In-process Transport + Observer as one bracket.

    Provides the transport + observer without a Publisher or Storage. Bind
    at process scope in an actor that only consumes notifications from
    same-process publishers (rare -- Redis is the usual cross-process case).
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import InMemoryObserver, InMemoryTransport

    return With(
        Provide(InMemoryTransport, {}),
        Provide(InMemoryObserver, {}),
    )


def redis_observer(
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "nu",
) -> With:
    """Redis Observer as one bracket.

    Read-only cross-process subscriber. Actors that don't write to any
    storage but need to react to cluster-wide changes (e.g. reactive
    counters, notification handlers) bind this at process scope.
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import RedisObserver

    return With(
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
    )
