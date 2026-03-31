"""Fixtures for eb_virtuals testing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from virtuals.codecs import NoOpCodec
from virtuals.storages.mem import InMemoryStorage
from virtuals.views import DictView


if TYPE_CHECKING:
    from collections.abc import Generator

    from virtuals.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol


@pytest.fixture
def storage() -> Generator[StorageProtocol, None, None]:
    """Memory storage instance for functional tests."""
    storage = InMemoryStorage(codec=NoOpCodec())
    storage.open()
    try:
        yield storage
    finally:
        storage.close()


@pytest.fixture
def tx(storage: StorageProtocol) -> Generator[TransactionProtocol, None, None]:
    """Read-write transaction context."""
    with storage.transaction() as transaction:
        yield transaction


@pytest.fixture
def snapshot(storage: StorageProtocol) -> Generator[SnapshotProtocol, None, None]:
    """Read-only snapshot context."""
    with storage.snapshot() as snap:
        yield snap


@pytest.fixture
def root_view(tx: TransactionProtocol) -> DictView:
    """Create a DictView at root for testing."""
    return DictView.open_root(tx)
