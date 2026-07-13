"""Storage topological presets.

Two forms, both live and independent:

- Imperative context managers (``memory_storage``, ``rocksdb_storage_redis``,
  ``rocksdb_storage``, ``lmdb_storage``, ``text_storage``) yield a
  ready ``StorageProtocol`` for hand-wired Contexts. Same as before.
- Bracket factories (``memory_navigator``, ``rocksdb_navigator_redis``,
  ``rocksdb_navigator``, ``text_navigator``) return a single
  ``_LifecycleBracket`` that drops into a ``nu.With(...)`` tree and binds
  the whole Codec + Observer + Storage + Navigator stack on ctx. Internally
  they compose ``Provide`` peers under a ``With``, so ctx-bind order and
  LIFO teardown come for free.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from nu.context.fabric import With
    from virtuals.tkv.storage import StorageProtocol


__all__ = [
    "lmdb_navigator",
    "lmdb_storage",
    "memory_navigator",
    "memory_storage",
    "rocksdb_navigator_redis",
    "rocksdb_navigator",
    "rocksdb_storage_redis",
    "rocksdb_storage",
    "text_navigator",
    "text_storage",
]


@contextmanager
def memory_storage() -> Generator[StorageProtocol, None, None]:
    """Create in-memory storage with no-op codec and in-memory observer.

    No persistence, no serialization — Python objects stored as-is.
    Useful for testing, prototyping, and ephemeral service handles.

    Yields:
        Configured in-memory storage instance

    Example:
        >>> with memory_storage() as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put("key", value)
    """
    from virtuals.codecs import NoOpCodec
    from virtuals.observers.mem import InMemoryObserver
    from virtuals.storages.mem import InMemoryStorage

    with (
        InMemoryObserver(codec=NoOpCodec()) as observer,
        InMemoryStorage(
            codec=NoOpCodec(),
            observer=observer,
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
    """Create LMDB storage with binary codec and in-memory observer.

    Args:
        path: Path to LMDB env (directory if subdir=True, file otherwise).
        read_only: Open the environment read-only.
        map_size: Maximum on-disk size in bytes. Default 10 GiB.
        max_readers: Maximum concurrent reader slots.
        subdir: If True, treat `path` as a directory; if False, as the env file.
        sync: If True, fsync data pages after each commit.

    Yields:
        Configured LMDB storage instance.

    Example:
        >>> with lmdb_storage("/mnt/nvme4/.db_blocks_lmdb") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.observers.mem import InMemoryObserver
    from virtuals.storages.lmdb import LMDBStorage

    with (
        InMemoryObserver(codec=BinaryCodec()) as observer,
        LMDBStorage(
            path=path,
            codec=BinaryCodec(),
            observer=observer,
            read_only=read_only,
            map_size=map_size,
            max_readers=max_readers,
            subdir=subdir,
            sync=sync,
        ) as storage,
    ):
        yield storage


@contextmanager
def text_storage(path: str, read_only: bool = False) -> Generator[StorageProtocol, None, None]:
    """Create text storage with text codec and in-memory observer.

    Args:
        path: Path for text storage directory
        read_only: Permissions

    Yields:
        Configured text storage instance

    Example:
        >>> with text_storage("/tmp/data") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put("key", "value")
    """
    from virtuals.codecs import TextCodec
    from virtuals.observers.mem import InMemoryObserver
    from virtuals.storages.textdb import TextStorage

    with (
        InMemoryObserver(codec=TextCodec()) as observer,
        TextStorage(
            path=path,
            codec=TextCodec(),
            observer=observer,
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
    """Create RocksDB storage with binary codec and in-memory observer.

    Args:
        path: Path to RocksDB database directory
        read_only: Open database in read-only mode
        secondary_path: Path to secondary RocksDB instance
        secondary_refresh_interval: Interval in seconds for background
            try_catch_up_with_primary on secondary DBs. None disables.

    Yields:
        Configured RocksDB storage instance

    Example:
        >>> with rocksdb_storage("/mnt/nvme4/.db_blocks_bin") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.observers.mem import InMemoryObserver
    from virtuals.storages.rocksdb import RocksDBStorage

    with (
        InMemoryObserver(codec=BinaryCodec()) as observer,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            observer=observer,
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
    """Create RocksDB storage with binary codec and in-memory observer.

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

    Example:
        >>> with rocksdb_storage_redis("/mnt/nvme4/.db_blocks_bin") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """
    from virtuals.codecs import BinaryCodec, TextCodec
    from virtuals.observers.redis_pubsub import RedisObserver
    from virtuals.storages.rocksdb import RocksDBStorage

    with (
        RedisObserver(
            codec=TextCodec(),
            redis_url=redis_url,
            channel_prefix=channel_prefix,
        ) as observer,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            observer=observer,
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
# whole Codec + Observer + Storage (+ Navigator) stack. Same order and LIFO
# teardown as a hand-written ``With(Provide(Codec, ...), Provide(Observer, ...),
# Provide(Storage, ...), Provide(Navigator, ...))``.
#
# ``tags=`` folds onto both the Storage and Navigator bindings so a shard
# picks its storage via ``storage_tags=`` and binds the Navigator under the
# same tag - matching the citadel per-shard pattern.
# =========================================================================


def memory_navigator(
    *,
    tags: Sequence[object] = (),
) -> With:
    """In-memory Codec + Observer + Storage + Navigator as one bracket.

    No persistence, no serialization -- Python objects go through NoOpCodec.
    Useful for tests, examples, and ephemeral service handles.

    Args:
        tags: fold onto the Storage and Navigator bindings.

    Example:
        >>> nu.With(
        ...     memory_navigator(),
        ...     body=Counter.value.store(1),
        ... )
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryStorage,
        Navigator,
        noop_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, noop_kwargs()),
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
    """RocksDB + in-memory Observer + Navigator as one bracket.

    Binary codec, in-process observer, transactional persistence. The 99%
    site for a per-shard rocksdb stack when you don't need cross-process
    change notifications.

    Args:
        path: RocksDB database directory.
        tags: fold onto the Storage and Navigator bindings.
        read_only: open the database in read-only mode.
        secondary_path: open as a secondary rocksdb instance.
        secondary_refresh_interval: seconds between background
            try_catch_up_with_primary on secondary DBs. None disables.
        disable_wal: skip the write-ahead log; faster but less durable.
        options: extra RocksDB options dict.

    Example:
        >>> nu.With(
        ...     rocksdb_navigator(".dbtest"),
        ...     body=Counter.value.store(1),
        ... )
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        Navigator,
        RocksDBStorage,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
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
    """RocksDB + Redis Observer + Navigator as one bracket.

    Same as ``rocksdb_navigator`` but with the Redis observer for
    cross-process change notifications. Requires a reachable Redis at
    ``redis_url`` at asetup time.

    Args:
        path: RocksDB database directory.
        tags: fold onto the Storage and Navigator bindings.
        read_only: open the database in read-only mode.
        secondary_path: open as a secondary rocksdb instance.
        secondary_refresh_interval: seconds between background
            try_catch_up_with_primary on secondary DBs. None disables.
        disable_wal: skip the write-ahead log; faster but less durable.
        options: extra RocksDB options dict.
        redis_url: Redis service URL for the observer.
        channel_prefix: Redis channel prefix for change events.
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        Navigator,
        RedisObserver,
        RocksDBStorage,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RocksDBStorage,
            {
                "path": path,
                "observer_type": RedisObserver,
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
    """Text (JSON) storage + in-memory Observer + Navigator as one bracket.

    Human-readable JSON on disk. For debugging, learning, or tiny
    hand-inspectable stores.

    Args:
        path: text storage directory.
        tags: fold onto the Storage and Navigator bindings.
        read_only: open the storage in read-only mode.
        log_operations: log each read / write to the storage (debug aid).
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        Navigator,
        TextStorage,
        text_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, text_kwargs()),
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
    """LMDB + in-memory Observer + Navigator as one bracket.

    Binary codec, in-process observer, single-writer memory-mapped LMDB env.
    Kwargs mirror the imperative ``lmdb_storage`` CM. LMDB is single-process
    so there's no Redis-observer sibling here; use rocksdb for that shape.

    Args:
        path: LMDB env path (directory when ``subdir=True``, file otherwise).
        tags: fold onto the Storage and Navigator bindings.
        read_only: open the env read-only.
        map_size: maximum on-disk size in bytes. Default 10 GiB.
        max_readers: maximum concurrent reader slots.
        subdir: if True, treat ``path`` as a directory; if False, as the env file.
        sync: if True, fsync data pages after each commit.

    Example:
        >>> nu.With(
        ...     lmdb_navigator("/mnt/nvme4/.db"),
        ...     body=Counter.value.store(1),
        ... )
    """
    from nu.context.fabric import Provide, With
    from nu.virtuals.fabrics import (
        Codec,
        InMemoryObserver,
        LMDBStorage,
        Navigator,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
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
