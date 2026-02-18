"""Storage topological presets."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator

    from tkv.tkv.storage import StorageProtocol


__all__ = [
    "memory_storage",
    "rocksdb_storage",
    "rocksdb_storage_inmemory",
    "text_storage",
]


@contextmanager
def memory_storage() -> Generator[StorageProtocol, None, None]:
    """Create in-memory storage with binary codec and in-memory observer.

    No persistence — all data lost on close. Useful for testing,
    prototyping, and ephemeral computations.

    Yields:
        Configured in-memory storage instance

    Example:
        >>> with memory_storage() as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """
    from tkv.codecs import BinaryCodec
    from tkv.observers.mem import InMemoryObserver
    from tkv.storages.mem import InMemoryStorage

    with (
        InMemoryObserver(codec=BinaryCodec()) as observer,
        InMemoryStorage(
            codec=BinaryCodec(),
            observer=observer,
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
    from tkv.codecs import TextCodec
    from tkv.observers.mem import InMemoryObserver
    from tkv.storages.textdb import TextStorage

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
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and in-memory observer.

    Args:
        path: Path to RocksDB database directory
        read_only: Open database in read-only mode
        secondary_path: Path to secondary RocksDB instance

    Yields:
        Configured RocksDB storage instance

    Example:
        >>> with rocksdb_storage_inmemory("/mnt/nvme4/.db_blocks_bin") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """
    from tkv.codecs import BinaryCodec
    from tkv.observers.mem import InMemoryObserver
    from tkv.storages.rocksdb import RocksDBStorage

    with (
        InMemoryObserver(codec=BinaryCodec()) as observer,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            observer=observer,
            read_only=read_only,
            secondary_path=secondary_path,
        ) as storage,
    ):
        yield storage


@contextmanager
def rocksdb_storage(
    path: str,
    read_only: bool = False,
    secondary_path: str | None = None,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "__every__",
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and in-memory observer.

    Args:
        path: Path to RocksDB database directory
        read_only: Permissions
        secondary_path: Open as secondary rocksdb storage
        redis_url: Redis service url
        channel_prefix: Redis channel prefix

    Yields:
        Configured RocksDB storage instance

    Example:
        >>> with rocksdb_storage("/mnt/nvme4/.db_blocks_bin") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """
    from tkv.codecs import BinaryCodec, TextCodec
    from tkv.observers.redis_pubsub import RedisObserver
    from tkv.storages.rocksdb import RocksDBStorage

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
        ) as storage,
    ):
        yield storage
