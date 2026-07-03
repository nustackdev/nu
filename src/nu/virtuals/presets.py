"""Storage topological presets."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator

    from virtuals.tkv.storage import StorageProtocol


__all__ = [
    "lmdb_storage",
    "memory_storage",
    "rocksdb_storage",
    "rocksdb_storage_inmemory",
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
def rocksdb_storage_inmemory(
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
        >>> with rocksdb_storage_inmemory("/mnt/nvme4/.db_blocks_bin") as storage:
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
def rocksdb_storage(
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
        >>> with rocksdb_storage("/mnt/nvme4/.db_blocks_bin") as storage:
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
