"""Example usage of StorageProtocolCompliance test suite.

This file demonstrates how to use the compliance test framework
to test your storage adapter implementation.

DO NOT RUN THIS FILE - it's a documentation example showing the pattern.
"""

# ruff: noqa: S108  # Example code uses /tmp for demonstration

from __future__ import annotations

import pytest

from tests.compliance import StorageProtocolCompliance


# Example 1: Testing a RocksDB adapter
class TestRocksDBAdapter(StorageProtocolCompliance):
    """Test RocksDB storage adapter compliance."""

    @pytest.fixture
    def storage(self):
        """Provide RocksDB storage instance for testing."""
        # This is just an example - adjust imports and setup for your implementation
        from everyshape.adapters import RocksDBStorage  # type: ignore[import-not-found]

        db_path = "/tmp/test_rocksdb"
        storage = RocksDBStorage(path=db_path)
        storage.open()

        yield storage

        storage.close()


# Example 2: Testing with pytest tmp_path fixture
class TestRocksDBAdapterWithTmpPath(StorageProtocolCompliance):
    """Test RocksDB with temporary directory."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Provide RocksDB storage with temporary path."""
        from everyshape.adapters import RocksDBStorage  # type: ignore[import-not-found]

        db_path = tmp_path / "test.db"
        storage = RocksDBStorage(path=db_path)
        storage.open()

        yield storage

        storage.close()


# Example 3: Adding custom tests alongside compliance tests
class TestMyStorageWithCustomTests(StorageProtocolCompliance):
    """Test storage adapter with both compliance and custom tests."""

    @pytest.fixture
    def storage(self):
        """Provide storage instance."""
        from my_storage import MyStorage  # type: ignore[import-not-found]

        storage = MyStorage("/tmp/test.db")
        storage.open()

        yield storage

        storage.close()

    # All 30 compliance tests run automatically!

    # You can also add custom tests specific to your implementation:
    def test_my_custom_feature(self, storage):
        """Test a custom feature specific to this storage implementation."""
        # Your custom test here
        pass

    def test_my_special_optimization(self, storage):
        """Test implementation-specific optimization."""
        # Your custom test here
        pass


# Example 4: Testing an in-memory storage adapter
class TestInMemoryAdapter(StorageProtocolCompliance):
    """Test in-memory storage adapter compliance."""

    @pytest.fixture
    def storage(self):
        """Provide in-memory storage instance."""
        from my_storage import InMemoryStorage  # type: ignore[import-not-found]

        storage = InMemoryStorage()
        storage.open()

        yield storage

        storage.close()


# Note: To actually run these tests, you would:
# 1. Ensure your storage implementation is importable
# 2. Run: pytest tests/integration/test_my_storage.py
# 3. All 30 compliance tests will run automatically
# 4. Plus any custom tests you added
