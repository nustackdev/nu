"""Functional test configuration and shared fixtures."""

from collections.abc import Generator

import pytest

from everyshape.storage import SnapshotProtocol, TransactionProtocol
from tests.support.mem_storage import MemoryStorage


@pytest.fixture
def storage() -> Generator[MemoryStorage, None, None]:
    """Memory storage instance for functional tests.

    Provides a clean storage instance for each test with automatic cleanup.
    """
    storage = MemoryStorage()
    storage.open()
    try:
        yield storage
    finally:
        storage.close()


@pytest.fixture
def tx(storage: MemoryStorage) -> Generator[TransactionProtocol, None, None]:
    """Read-write transaction context.

    Auto-commits on successful completion, rolls back on exception.
    """
    with storage.transaction() as transaction:
        yield transaction


@pytest.fixture
def snapshot(storage: MemoryStorage) -> Generator[SnapshotProtocol, None, None]:
    """Read-only snapshot context.

    Useful for testing isolation and concurrent read scenarios.
    """
    with storage.snapshot() as snap:
        yield snap
