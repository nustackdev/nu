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
    - Basic CRUD operations (put, get, delete, exists)
    - Multiget operations
    - Scan operations with filters
    - Transaction lifecycle (commit, abort)
    - Error cases (closed transactions, read-only violations)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from everyshape.loc import key
from everyshape.storage import StorageScanOptions
from everyshape.storage.filter import LengthFilter, PrefixFilter
from everyshape.storage.storage.exceptions import (
    StorageClosedError,
    StorageInterfaceError,
)
from everyshape.types import EMPTY


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
            assert not snap.exists(test_key)

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
            assert not snap.exists(test_key)

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
            txn.delete(test_key)  # Returns None, silent and idempotent

        # Verify key is gone
        with storage.snapshot() as snap:
            assert not snap.exists(test_key)

    def test_delete_nonexistent(self, storage: StorageProtocol) -> None:
        """Test deleting a non-existent key is silent (idempotent)."""
        test_key = key.from_tuple(("test", "crud", "delete_missing"))

        with storage.transaction() as txn:
            # Should not raise - delete is idempotent
            txn.delete(test_key)

    def test_exists(self, storage: StorageProtocol) -> None:
        """Test exists() key existence check."""
        test_key = key.from_tuple(("test", "crud", "exists"))
        test_value = b"exists"

        with storage.snapshot() as snap:
            assert not snap.exists(test_key)

        with storage.transaction() as txn:
            txn.put(test_key, test_value)

        with storage.snapshot() as snap:
            assert snap.exists(test_key)

    def test_get_missing_key_returns_empty(self, storage: StorageProtocol) -> None:
        """Test get() returns EMPTY for missing keys (never raises)."""
        test_key = key.from_tuple(("test", "crud", "missing"))

        with storage.snapshot() as snap:
            result = snap.get(test_key)
            assert result is EMPTY

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
            assert not snap.exists(test_key)

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
            assert not snap.exists(test_key)

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

    # ========================================================================
    # Scan Operations
    # ========================================================================

    def test_scan_empty_storage(self, storage: StorageProtocol) -> None:
        """Test scanning empty storage returns no results."""
        with storage.snapshot() as snap:
            scan = snap.scan(StorageScanOptions())
            results = list(scan.items())
            assert results == []

    def test_scan_all_keys(self, storage: StorageProtocol) -> None:
        """Test scanning all keys without filters."""
        keys = [
            key.from_tuple(("a",)),
            key.from_tuple(("b",)),
            key.from_tuple(("c",)),
        ]
        values = [b"v1", b"v2", b"v3"]

        with storage.transaction() as txn:
            for k, v in zip(keys, values, strict=True):
                txn.put(k, v)

        with storage.snapshot() as snap:
            scan = snap.scan(StorageScanOptions())
            results = list(scan.items())
            assert len(results) == 3
            # Results should be sorted
            result_keys = [k for k, _ in results]
            assert result_keys == sorted(result_keys)

    def test_scan_keys_only(self, storage: StorageProtocol) -> None:
        """Test scan keys() method."""
        keys = [
            key.from_tuple(("scan", "keys", "a")),
            key.from_tuple(("scan", "keys", "b")),
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("scan", "keys")),
                    break_filter=PrefixFilter(prefix=("scan", "keys")),
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 2

    def test_scan_values_only(self, storage: StorageProtocol) -> None:
        """Test scan values() method."""
        test_key = key.from_tuple(("scan", "values", "test"))

        with storage.transaction() as txn:
            txn.put(test_key, b"test_value")

        with storage.snapshot() as snap:
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("scan", "values")),
                    break_filter=PrefixFilter(prefix=("scan", "values")),
                )
            )
            result_values = list(scan.values())
            assert b"test_value" in result_values

    def test_scan_with_start(self, storage: StorageProtocol) -> None:
        """Test scanning from a start key."""
        keys = [
            key.from_tuple(("scan", "start", "a")),
            key.from_tuple(("scan", "start", "b")),
            key.from_tuple(("scan", "start", "c")),
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            # Start from ("scan", "start", "b")
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("scan", "start", "b")),
                    break_filter=PrefixFilter(prefix=("scan", "start")),
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 2
            assert keys[0] not in result_keys
            assert keys[1] in result_keys
            assert keys[2] in result_keys

    def test_scan_with_limit(self, storage: StorageProtocol) -> None:
        """Test scanning with result limit."""
        keys = [key.from_tuple(("scan", "limit", str(i))) for i in range(10)]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("scan", "limit")),
                    break_filter=PrefixFilter(prefix=("scan", "limit")),
                    limit=3,
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 3

    def test_scan_reverse(self, storage: StorageProtocol) -> None:
        """Test reverse scanning."""
        keys = [
            key.from_tuple(("scan", "reverse", "a")),
            key.from_tuple(("scan", "reverse", "b")),
            key.from_tuple(("scan", "reverse", "c")),
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("scan", "reverse", "c")),
                    reverse=True,
                    break_filter=PrefixFilter(prefix=("scan", "reverse")),
                )
            )
            result_keys = list(scan.keys())
            # Should be in reverse order
            assert result_keys == sorted(result_keys, reverse=True)

    def test_scan_with_prefix_filter(self, storage: StorageProtocol) -> None:
        """Test scanning with prefix filter."""
        keys = [
            key.from_tuple(("users", "alice")),
            key.from_tuple(("users", "bob")),
            key.from_tuple(("posts", "123")),
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            # Filter to only users
            scan = snap.scan(
                StorageScanOptions(
                    filter=PrefixFilter(prefix=("users",)),
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 2
            for k in result_keys:
                assert k[0] == "users"

    def test_scan_with_break_filter(self, storage: StorageProtocol) -> None:
        """Test scanning with break filter for efficient prefix scans."""
        keys = [
            key.from_tuple(("a", "1")),
            key.from_tuple(("b", "1")),
            key.from_tuple(("b", "2")),
            key.from_tuple(("c", "1")),
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            # Break when we leave prefix ("b",)
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("b",)),
                    break_filter=PrefixFilter(prefix=("b",)),
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 2
            for k in result_keys:
                assert k[0] == "b"

    def test_scan_with_length_filter(self, storage: StorageProtocol) -> None:
        """Test scanning with length filter."""
        keys = [
            key.from_tuple(("scan", "length")),  # length 2
            key.from_tuple(("scan", "length", "child")),  # length 3
            key.from_tuple(("scan", "length", "child", "deep")),  # length 4
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            # Filter to only length 3
            scan = snap.scan(
                StorageScanOptions(
                    start=key.from_tuple(("scan", "length")),
                    break_filter=PrefixFilter(prefix=("scan", "length")),
                    filter=LengthFilter(length=3),
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 1
            assert len(result_keys[0]) == 3

    def test_scan_with_composite_filter(self, storage: StorageProtocol) -> None:
        """Test scanning with composite filter (prefix AND length)."""
        keys = [
            key.from_tuple(("users", "alice")),  # length 2
            key.from_tuple(("users", "alice", "profile")),  # length 3
            key.from_tuple(("users", "bob")),  # length 2
            key.from_tuple(("posts", "123")),  # length 2
        ]

        with storage.transaction() as txn:
            for k in keys:
                txn.put(k, b"value")

        with storage.snapshot() as snap:
            # Filter to users with length 2 (direct children of users)
            scan = snap.scan(
                StorageScanOptions(
                    filter=PrefixFilter(prefix=("users",)) & LengthFilter(length=2),
                )
            )
            result_keys = list(scan.keys())
            assert len(result_keys) == 2
            for k in result_keys:
                assert k[0] == "users"
                assert len(k) == 2

    def test_scan_closed_transaction_raises(self, storage: StorageProtocol) -> None:
        """Test scanning closed transaction raises error."""
        txn = storage.begin_transaction()
        txn.abort()

        with pytest.raises(StorageClosedError):
            txn.scan(StorageScanOptions())

    def test_scan_write_batch_raises(self, storage: StorageProtocol) -> None:
        """Test scanning write-only batch raises error."""
        batch = storage.begin_write_batch()

        with pytest.raises((StorageClosedError, AttributeError)):
            batch.scan(StorageScanOptions())  # type: ignore[attr-defined]

        batch.abort()
