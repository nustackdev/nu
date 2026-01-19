"""Compliance tests for MemoryStorage implementation.

Runs the storage and observer compliance test suites against the
in-memory storage implementation to verify protocol compliance.
"""

from __future__ import annotations

import pytest

from everykv.testing import (
    ObserverCompliance,
    RegistryCompliance,
    StorageProtocolCompliance,
)

from .mem_storage import MemoryStorage


class TestMemoryStorageCompliance(StorageProtocolCompliance):
    """Run storage protocol compliance tests against MemoryStorage."""

    @pytest.fixture
    def storage(self):
        """Provide MemoryStorage instance for testing."""
        storage = MemoryStorage()
        yield storage
        storage.close()


class TestMemoryStorageRegistryCompliance(RegistryCompliance):
    """Run observer registry compliance tests."""

    pass  # Uses default registry fixture from RegistryCompliance


class TestMemoryStorageObserverCompliance(ObserverCompliance):
    """Run observer protocol compliance tests against MemoryStorage."""

    @pytest.fixture
    def observable_storage(self):
        """Provide MemoryStorage instance with observer support."""
        storage = MemoryStorage()
        yield storage
        storage.close()
