"""Functional test configuration and shared fixtures."""

import pathlib
from collections.abc import Generator

import pytest

from redwood.storage import StorageProtocol, TransactionProtocol


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> Generator[StorageProtocol, None, None]:
    """Create temporary storage backend for functional testing."""
    from rwstd.storage.codecs import BinaryCodec
    from rwstd.storage.storage_rocksdb import RocksDBStorage

    db_path = tmp_path / "test_db"
    storage = RocksDBStorage(path=db_path, codec=BinaryCodec())
    storage.open()
    yield storage  # type: ignore
    storage.close()


@pytest.fixture
def tx(storage: StorageProtocol) -> Generator[TransactionProtocol, None, None]:
    """Create transaction context for functional tests."""
    with storage.transaction() as tx:
        yield tx
