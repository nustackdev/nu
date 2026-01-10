"""Abstract compliance test suite for StorageProtocol implementations.

This module provides a thin test framework for verifying that storage adapters
correctly implement the StorageProtocol interface. These are "smoke tests" -
basic checks that verify protocol compliance without exercising advanced features
like parallelism, isolation levels, or performance characteristics.

Usage:
    Inherit from StorageProtocolCompliance and override the storage fixture:

    ```python
    from tests.compliance.test_storage_protocol import StorageProtocolCompliance


    class TestMyStorageAdapter(StorageProtocolCompliance):
        @pytest.fixture
        def storage(self):
            # Set up your storage implementation
            db = MyStorage("/tmp/test.db")
            db.open()
            yield db
            db.close()
    ```

    The test suite will automatically run all compliance tests against your
    storage implementation.

Test Coverage:
    - Transaction creation methods (begin, begin_transaction, begin_snapshot, begin_write_batch)
    - Context managers (transaction(), snapshot(), batch_write())
    - Basic CRUD operations (put, get, delete, has)
    - Multiget operations
    - Transaction lifecycle (commit, abort)
    - Error cases (closed transactions, read-only violations)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from everyshape.loc import key
from everyshape.storage.storage.exceptions import (
    StorageClosedError,
    StorageInterfaceError,
    StorageKeyError,
)


if TYPE_CHECKING:
    from everyshape.storage.storage.storage import StorageProtocol


class StorageProtocolCompliance:
    """Abstract test suite for StorageProtocol compliance.

    Subclasses must override the `storage` fixture to provide their
    storage implementation. All tests in this class will run against
    the provided storage instance.
    """

    @pytest.fixture
    def storage(self) -> StorageProtocol:
        """Provide storage implementation to test.

        Override this fixture in subclasses to provide your storage implementation.

        Returns:
            StorageProtocol: A storage instance that implements StorageProtocol.

        Raises:
            NotImplementedError: If not overridden in subclass.

        Example:
            ```python
            @pytest.fixture
            def storage(self):
                db = RocksDBStorage("/tmp/test.db")
                db.open()
                yield db
                db.close()
            ```
        """
        raise NotImplementedError(
            "Subclass must override the 'storage' fixture to provide a StorageProtocol implementation"
        )

    # ========================================================================
    # Transaction Creation Tests
    # ========================================================================

    def test_begin_transaction(self, storage: StorageProtocol) -> None:
        """Test begin_transaction creates a read-write transaction."""
        txn = storage.begin_transaction()
        assert not txn.is_closed
        assert txn.is_active
        txn.abort()
        assert txn.is_closed
        assert not txn.is_active

    def test_begin_snapshot(self, storage: StorageProtocol) -> None:
        """Test begin_snapshot creates a read-only snapshot."""
        snapshot = storage.begin_snapshot()
        assert not snapshot.is_closed
        assert snapshot.is_active
        snapshot.close()
        assert snapshot.is_closed
        assert not snapshot.is_active

    def test_begin_write_batch(self, storage: StorageProtocol) -> None:
        """Test begin_write_batch creates a write-only batch."""
        batch = storage.begin_write_batch()
        assert not batch.is_closed
        assert batch.is_active
        batch.abort()
        assert batch.is_closed
        assert not batch.is_active

    def test_begin_with_read_only(self, storage: StorageProtocol) -> None:
        """Test begin(read_only=True) creates a snapshot."""
        snapshot = storage.begin(read_only=True)
        assert not snapshot.is_closed
        assert snapshot.is_active
        snapshot.close()

    def test_begin_with_write_only(self, storage: StorageProtocol) -> None:
        """Test begin(write_only=True) creates a write batch."""
        batch = storage.begin(write_only=True)
        assert not batch.is_closed
        assert batch.is_active
        batch.abort()

    def test_begin_with_no_flags(self, storage: StorageProtocol) -> None:
        """Test begin() with no flags creates a full transaction."""
        txn = storage.begin()
        assert not txn.is_closed
        assert txn.is_active
        txn.abort()

    # ========================================================================
    # Context Manager Tests
    # ========================================================================

    def test_transaction_context_manager_commit(self, storage: StorageProtocol) -> None:
        """Test transaction() context manager commits on success."""
        test_key = key.from_tuple(("test", "ctx", "commit"))
        test_value = b"committed"

        with storage.transaction() as txn:
            txn.put(test_key, test_value)
            # Transaction should still be active inside context
            assert txn.is_active

        # Transaction should be closed after context
        assert txn.is_closed

        # Verify data was committed
        with storage.snapshot() as snap:
            assert snap.get(test_key) == test_value

    def test_transaction_context_manager_abort(self, storage: StorageProtocol) -> None:
        """Test transaction() context manager aborts on exception."""
        test_key = key.from_tuple(("test", "ctx", "abort"))
        test_value = b"aborted"

        try:
            with storage.transaction() as txn:
                txn.put(test_key, test_value)
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # Transaction should be closed
        assert txn.is_closed

        # Verify data was not committed
        with storage.snapshot() as snap:
            assert not snap.has(test_key)

    def test_snapshot_context_manager(self, storage: StorageProtocol) -> None:
        """Test snapshot() context manager closes on exit."""
        with storage.snapshot() as snap:
            assert snap.is_active
            assert not snap.is_closed

        # Snapshot should be closed after exit
        assert snap.is_closed

    def test_batch_write_context_manager_commit(self, storage: StorageProtocol) -> None:
        """Test batch_write() context manager commits on success."""
        test_key = key.from_tuple(("test", "batch", "commit"))
        test_value = b"batch_committed"

        with storage.batch_write() as batch:
            batch.put(test_key, test_value)
            assert batch.is_active

        # Batch should be closed after context
        assert batch.is_closed

        # Verify data was committed
        with storage.snapshot() as snap:
            assert snap.get(test_key) == test_value

    def test_batch_write_context_manager_abort(self, storage: StorageProtocol) -> None:
        """Test batch_write() context manager aborts on exception."""
        test_key = key.from_tuple(("test", "batch", "abort"))
        test_value = b"batch_aborted"

        try:
            with storage.batch_write() as batch:
                batch.put(test_key, test_value)
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # Batch should be closed
        assert batch.is_closed

        # Verify data was not committed
        with storage.snapshot() as snap:
            assert not snap.has(test_key)

    # ========================================================================
    # Basic CRUD Operations
    # ========================================================================

    def test_put_get(self, storage: StorageProtocol) -> None:
        """Test basic put and get operations."""
        test_key = key.from_tuple(("test", "crud", "put_get"))
        test_value = b"test_value"

        with storage.transaction() as txn:
            txn.put(test_key, test_value)

        with storage.snapshot() as snap:
            assert snap.get(test_key) == test_value

    def test_put_update_get(self, storage: StorageProtocol) -> None:
        """Test updating an existing key."""
        test_key = key.from_tuple(("test", "crud", "update"))
        initial_value = b"initial"
        updated_value = b"updated"

        with storage.transaction() as txn:
            txn.put(test_key, initial_value)

        with storage.transaction() as txn:
            txn.put(test_key, updated_value)

        with storage.snapshot() as snap:
            assert snap.get(test_key) == updated_value

    def test_delete(self, storage: StorageProtocol) -> None:
        """Test delete operation."""
        test_key = key.from_tuple(("test", "crud", "delete"))
        test_value = b"to_be_deleted"

        # Put then delete
        with storage.transaction() as txn:
            txn.put(test_key, test_value)

        with storage.transaction() as txn:
            result = txn.delete(test_key)
            assert result is True  # Key existed and was deleted

        # Verify key is gone
        with storage.snapshot() as snap:
            assert not snap.has(test_key)

    def test_delete_nonexistent(self, storage: StorageProtocol) -> None:
        """Test deleting a non-existent key."""
        test_key = key.from_tuple(("test", "crud", "delete_missing"))

        with storage.transaction() as txn:
            result = txn.delete(test_key)
            assert result is False  # Key didn't exist

    def test_has(self, storage: StorageProtocol) -> None:
        """Test has() key existence check."""
        test_key = key.from_tuple(("test", "crud", "has"))
        test_value = b"exists"

        with storage.snapshot() as snap:
            assert not snap.has(test_key)

        with storage.transaction() as txn:
            txn.put(test_key, test_value)

        with storage.snapshot() as snap:
            assert snap.has(test_key)

    def test_get_missing_key(self, storage: StorageProtocol) -> None:
        """Test get() raises StorageKeyError for missing keys."""
        test_key = key.from_tuple(("test", "crud", "missing"))

        with storage.snapshot() as snap:
            with pytest.raises(StorageKeyError):
                snap.get(test_key)

    # ========================================================================
    # Multiget Operations
    # ========================================================================

    def test_multiget(self, storage: StorageProtocol) -> None:
        """Test multiget retrieves multiple keys."""
        keys = [
            key.from_tuple(("test", "multiget", "key1")),
            key.from_tuple(("test", "multiget", "key2")),
            key.from_tuple(("test", "multiget", "key3")),
        ]
        values = [b"value1", b"value2", b"value3"]

        # Put test data
        with storage.transaction() as txn:
            for k, v in zip(keys, values, strict=True):
                txn.put(k, v)

        # Multiget
        with storage.snapshot() as snap:
            result = snap.multiget(keys)
            assert len(result) == 3
            for k, v in zip(keys, values, strict=True):
                assert result[k] == v

    def test_multiget_partial(self, storage: StorageProtocol) -> None:
        """Test multiget with some missing keys."""
        key1 = key.from_tuple(("test", "multiget", "exists"))
        key2 = key.from_tuple(("test", "multiget", "missing"))
        value1 = b"exists"

        # Put only first key
        with storage.transaction() as txn:
            txn.put(key1, value1)

        # Multiget both keys
        with storage.snapshot() as snap:
            result = snap.multiget([key1, key2])
            assert len(result) == 1
            assert result[key1] == value1
            assert key2 not in result

    def test_multiget_empty(self, storage: StorageProtocol) -> None:
        """Test multiget with empty key list."""
        with storage.snapshot() as snap:
            result = snap.multiget([])
            assert result == {}

    # ========================================================================
    # Transaction Lifecycle
    # ========================================================================

    def test_commit(self, storage: StorageProtocol) -> None:
        """Test explicit transaction commit."""
        test_key = key.from_tuple(("test", "lifecycle", "commit"))
        test_value = b"committed"

        txn = storage.begin_transaction()
        txn.put(test_key, test_value)
        txn.commit()

        assert txn.is_closed

        with storage.snapshot() as snap:
            assert snap.get(test_key) == test_value

    def test_abort(self, storage: StorageProtocol) -> None:
        """Test explicit transaction abort."""
        test_key = key.from_tuple(("test", "lifecycle", "abort"))
        test_value = b"aborted"

        txn = storage.begin_transaction()
        txn.put(test_key, test_value)
        txn.abort()

        assert txn.is_closed

        with storage.snapshot() as snap:
            assert not snap.has(test_key)

    def test_write_batch_write(self, storage: StorageProtocol) -> None:
        """Test explicit write batch write."""
        test_key = key.from_tuple(("test", "lifecycle", "batch_write"))
        test_value = b"batch_written"

        batch = storage.begin_write_batch()
        batch.put(test_key, test_value)
        batch.write()

        assert batch.is_closed

        with storage.snapshot() as snap:
            assert snap.get(test_key) == test_value

    def test_write_batch_abort(self, storage: StorageProtocol) -> None:
        """Test explicit write batch abort."""
        test_key = key.from_tuple(("test", "lifecycle", "batch_abort"))
        test_value = b"batch_aborted"

        batch = storage.begin_write_batch()
        batch.put(test_key, test_value)
        batch.abort()

        assert batch.is_closed

        with storage.snapshot() as snap:
            assert not snap.has(test_key)

    # ========================================================================
    # Error Cases
    # ========================================================================

    def test_closed_transaction_read(self, storage: StorageProtocol) -> None:
        """Test reading from closed transaction raises error."""
        test_key = key.from_tuple(("test", "error", "closed_read"))

        txn = storage.begin_transaction()
        txn.abort()

        with pytest.raises(StorageClosedError):
            txn.get(test_key)

    def test_closed_transaction_write(self, storage: StorageProtocol) -> None:
        """Test writing to closed transaction raises error."""
        test_key = key.from_tuple(("test", "error", "closed_write"))
        test_value = b"fail"

        txn = storage.begin_transaction()
        txn.abort()

        with pytest.raises(StorageClosedError):
            txn.put(test_key, test_value)

    def test_snapshot_write_forbidden(self, storage: StorageProtocol) -> None:
        """Test that snapshots cannot perform write operations."""
        test_key = key.from_tuple(("test", "error", "snapshot_write"))
        test_value = b"forbidden"

        snapshot = storage.begin_snapshot()

        # Snapshots should not have put/delete methods or should raise error
        with pytest.raises((AttributeError, StorageInterfaceError)):
            snapshot.put(test_key, test_value)  # type: ignore[attr-defined]

        snapshot.close()

    def test_write_batch_read_forbidden(self, storage: StorageProtocol) -> None:
        """Test that write batches cannot perform read operations."""
        test_key = key.from_tuple(("test", "error", "batch_read"))

        batch = storage.begin_write_batch()

        # Write batches should not have get/has methods or should raise error
        with pytest.raises((AttributeError, StorageInterfaceError)):
            batch.get(test_key)  # type: ignore[attr-defined]

        batch.abort()

    def test_double_commit(self, storage: StorageProtocol) -> None:
        """Test that committing twice raises error."""
        txn = storage.begin_transaction()
        txn.commit()

        with pytest.raises(StorageClosedError):
            txn.commit()

    def test_commit_after_abort(self, storage: StorageProtocol) -> None:
        """Test that commit after abort raises error."""
        txn = storage.begin_transaction()
        txn.abort()

        with pytest.raises(StorageClosedError):
            txn.commit()
