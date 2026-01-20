"""Storage topological presets."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from everybase.view import DictView

# from everyflow import FlowState, StorageProvider
from pv.loc import key
from pv.storage import StorageProtocol
from term.shape import Shape


__all__ = [
    "text_storage",
    "rocksdb_storage",
    "regular_provider",
    "sharded_provider",
    "rocksdb_storage_inmemory",
]


@contextmanager
def text_storage(path: str, read_only: bool = False) -> Generator[StorageProtocol, None, None]:
    """Create text storage with text codec and in-memory observer.

    Args:
        path: Path for text storage directory

    Yields:
        Configured text storage instance

    Example:
        >>> with text_storage("/tmp/data") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put("key", "value")
    """
    from everybase.adapters.codecs import TextCodec
    from everybase.adapters.observers.in_memory import InMemoryObserver
    from everybase.adapters.storages.textdb import TextStorage

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

    from everybase.adapters.codecs import BinaryCodec
    from everybase.adapters.observers.in_memory import InMemoryObserver
    from everybase.adapters.storages.rocksdb import RocksDBStorage

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
    channel_prefix: str = "everyshape",
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and in-memory observer.

    Args:
        path: Path to RocksDB database directory

    Yields:
        Configured RocksDB storage instance

    Example:
        >>> with rocksdb_storage("/mnt/nvme4/.db_blocks_bin") as storage:
        ...     with storage.transaction() as txn:
        ...         txn.put(b"key", b"value")
    """

    from everybase.adapters.codecs import BinaryCodec, TextCodec
    from everybase.adapters.observers.redis_pubsub import RedisObserver
    from everybase.adapters.storages.rocksdb import RocksDBStorage

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


def regular_provider(storage: StorageProtocol):
    return StorageProvider(
        (storage,),
        {
            None: (DictView, ("/",), 0),
            FlowState: (DictView, ("/", "__flow__"), 0),
        },
    )


def sharded_provider(storage: StorageProtocol, *ext: tuple[type[Shape], key.Key, StorageProtocol]):
    config = {
        None: (DictView, ("/",), 0),
        FlowState: (DictView, ("/", "__flow__"), 0),
    }

    storages: list[StorageProtocol] = []

    storages.append(storage)

    for shape, shape_key, shape_storage in ext:
        if shape_storage not in storages:
            storages.append(shape_storage)
        config.setdefault(shape, (DictView, shape_key, storages.index(shape_storage)))

    return StorageProvider(
        tuple(storages),
        config,
    )
