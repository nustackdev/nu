"""Functional tests for storage layer (Layer 1).

Tests storage operations, transactions, snapshots, and scans across all
storage backends (parametrized via conftest.py fixtures).
"""

from redwood.storage import (
    StorageClosedError,
    StorageKeyError,
    StorageScanOptions,
)


# ============================================================================
# STORAGE LIFECYCLE
# ============================================================================


def test_storage_open_close(storage):
    """Test storage open/close lifecycle."""
    # Storage is already opened by fixture
    assert storage._opened is True

    # Close it
    storage.close()
    assert storage._opened is False

    # Reopen
    storage.open()
    assert storage._opened is True


def test_storage_context_manager(tmp_path, codec):
    """Test storage context manager auto open/close."""
    from rwstd.storage.storage_rocksdb import RocksDBStorage

    db_path = tmp_path / "ctx_test_db"

    with RocksDBStorage(path=db_path, codec=codec) as storage:
        assert storage._opened is True

    # After context exit, storage should be closed
    assert storage._opened is False


def test_storage_multiple_open_close_cycles(storage):
    """Test multiple open/close cycles."""
    for _ in range(3):
        storage.close()
        assert storage._opened is False

        storage.open()
        assert storage._opened is True


# ============================================================================
# TRANSACTION OPERATIONS
# ============================================================================


def test_transaction_basic_put_get(storage):
    """Test basic transaction put/get operations."""
    key = ("users", "alice")
    value = {"name": "Alice", "age": 30}

    with storage.transaction() as txn:
        txn.put(key, value)

    # Verify with new transaction
    with storage.transaction() as txn:
        result = txn.get(key)
        assert result == value


def test_transaction_has_key(storage):
    """Test transaction has() operation."""
    key = ("users", "bob")

    with storage.transaction() as txn:
        assert not txn.has(key)

        txn.put(key, {"name": "Bob"})
        assert txn.has(key)


def test_transaction_delete(storage):
    """Test transaction delete operation."""
    key = ("users", "charlie")

    # Put key
    with storage.transaction() as txn:
        txn.put(key, {"name": "Charlie"})

    # Delete key
    with storage.transaction() as txn:
        deleted = txn.delete(key)
        assert deleted is True

    # Verify deletion
    with storage.transaction() as txn:
        assert not txn.has(key)


def test_transaction_delete_nonexistent(storage):
    """Test deleting non-existent key returns False."""
    key = ("users", "nonexistent")

    with storage.transaction() as txn:
        deleted = txn.delete(key)
        assert deleted is False


def test_transaction_get_nonexistent_raises(storage):
    """Test getting non-existent key raises StorageKeyError."""
    key = ("users", "missing")

    try:
        with storage.transaction() as txn:
            txn.get(key)
        assert False, "Should have raised StorageKeyError"
    except StorageKeyError:
        pass


def test_transaction_multiget(storage):
    """Test transaction multiget operation."""
    keys = [
        ("users", "alice"),
        ("users", "bob"),
        ("users", "missing"),
    ]

    # Put some data
    with storage.transaction() as txn:
        txn.put(keys[0], {"name": "Alice"})
        txn.put(keys[1], {"name": "Bob"})

    # Multiget
    with storage.transaction() as txn:
        results = txn.multiget(keys)

        assert len(results) == 2
        assert results[keys[0]]["name"] == "Alice"
        assert results[keys[1]]["name"] == "Bob"
        assert keys[2] not in results


def test_transaction_commit_persists(storage):
    """Test transaction commit persists changes."""
    key = ("persist", "test")

    txn = storage.begin_transaction()
    txn.put(key, {"data": "committed"})
    txn.commit()

    # Verify in new transaction
    with storage.transaction() as txn:
        result = txn.get(key)
        assert result == {"data": "committed"}


def test_transaction_abort_discards(storage):
    """Test transaction abort discards changes."""
    key = ("abort", "test")

    txn = storage.begin_transaction()
    txn.put(key, {"data": "aborted"})
    txn.abort()

    # Verify key doesn't exist
    with storage.transaction() as txn:
        assert not txn.has(key)


def test_transaction_exception_auto_abort(storage):
    """Test transaction auto-aborts on exception."""
    key = ("exception", "test")

    try:
        with storage.transaction() as txn:
            txn.put(key, {"data": "should_not_persist"})
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify key doesn't exist
    with storage.transaction() as txn:
        assert not txn.has(key)


def test_transaction_update_value(storage):
    """Test updating existing value."""
    key = ("update", "test")

    # Initial value
    with storage.transaction() as txn:
        txn.put(key, {"version": 1})

    # Update value
    with storage.transaction() as txn:
        txn.put(key, {"version": 2})

    # Verify update
    with storage.transaction() as txn:
        result = txn.get(key)
        assert result == {"version": 2}


def test_transaction_isolation(storage):
    """Test uncommitted writes not visible to other transactions."""
    key = ("isolation", "test")

    # Start transaction but don't commit
    txn1 = storage.begin_transaction()
    txn1.put(key, {"data": "uncommitted"})

    # Start second transaction - shouldn't see uncommitted write
    with storage.transaction() as txn2:
        assert not txn2.has(key)

    # Commit first transaction
    txn1.commit()

    # Now should be visible
    with storage.transaction() as txn3:
        assert txn3.has(key)


# ============================================================================
# SNAPSHOT OPERATIONS
# ============================================================================


def test_snapshot_read_operations(storage):
    """Test snapshot read operations."""
    key = ("snapshot", "read")

    # Put data
    with storage.transaction() as txn:
        txn.put(key, {"data": "snapshot_test"})

    # Read with snapshot
    with storage.snapshot() as snap:
        result = snap.get(key)
        assert result == {"data": "snapshot_test"}
        assert snap.has(key)


def test_snapshot_multiget(storage):
    """Test snapshot multiget operation."""
    keys = [
        ("snapshot", "multi1"),
        ("snapshot", "multi2"),
    ]

    # Put data
    with storage.transaction() as txn:
        txn.put(keys[0], {"id": 1})
        txn.put(keys[1], {"id": 2})

    # Multiget with snapshot
    with storage.snapshot() as snap:
        results = snap.multiget(keys)
        assert len(results) == 2
        assert results[keys[0]]["id"] == 1
        assert results[keys[1]]["id"] == 2


def test_snapshot_read_only(storage):
    """Test snapshot doesn't have write methods."""
    with storage.snapshot() as snap:
        # Snapshot should not have put/delete methods
        assert not snap.writable


def test_snapshot_after_close_raises(storage):
    """Test snapshot operations after close raise error."""
    snap = storage.begin_snapshot()
    snap.close()

    try:
        snap.get(("any", "key"))
        assert False, "Should have raised StorageClosedError"
    except StorageClosedError:
        pass


# ============================================================================
# SCAN OPERATIONS
# ============================================================================


def test_scan_forward_keys(storage):
    """Test forward scan returning keys."""
    # Put test data
    with storage.transaction() as txn:
        txn.put(("scan", "a"), 1)
        txn.put(("scan", "b"), 2)
        txn.put(("scan", "c"), 3)

    # Scan forward
    with storage.snapshot() as snap:
        scan = snap.scan(
            StorageScanOptions(
                start=("scan",),
                end=("scan", "\xff"),
                start_inclusive=True,
                end_inclusive=True,
            )
        )

        keys = list(scan.keys())
        assert len(keys) == 3
        assert keys[0] == ("scan", "a")
        assert keys[1] == ("scan", "b")
        assert keys[2] == ("scan", "c")


def test_scan_reverse_keys(storage):
    """Test reverse scan returning keys."""
    # TODO: add reverse
    # Put test data
    # with storage.transaction() as txn:
    #     txn.put(("scan", "a"), 1)
    #     txn.put(("scan", "b"), 2)
    #     txn.put(("scan", "c"), 3)

    # # Scan reverse
    # with storage.snapshot() as snap:
    #     scan = snap.scan(
    #         StorageScanOptions(
    #             start=("scan", ),
    #             end=("scan","\xff"),
    #             reverse=True,
    #             start_inclusive=True,
    #             end_inclusive=True,
    #         )
    #     )

    #     keys = list(scan.keys())
    #     assert len(keys) == 3
    #     assert keys[0] == ("scan", "c")
    #     assert keys[1] == ("scan", "b")
    #     assert keys[2] == ("scan", "a")


def test_scan_values(storage):
    """Test scan returning values."""
    # Put test data
    with storage.transaction() as txn:
        txn.put(("scan", "v1"), {"id": 1})
        txn.put(("scan", "v2"), {"id": 2})
        txn.put(("scan", "v3"), {"id": 3})

    # Scan values
    with storage.snapshot() as snap:
        scan = snap.scan(
            StorageScanOptions(
                start=("scan",),
                end=("scan", "\xff"),
                start_inclusive=True,
                end_inclusive=True,
            )
        )

        values = list(scan.values())
        assert len(values) == 3
        assert values[0]["id"] == 1
        assert values[1]["id"] == 2
        assert values[2]["id"] == 3


def test_scan_items(storage):
    """Test scan returning (key, value) items."""
    # Put test data
    with storage.transaction() as txn:
        txn.put(("scan", "i1"), {"id": 1})
        txn.put(("scan", "i2"), {"id": 2})

    # Scan items
    with storage.snapshot() as snap:
        scan = snap.scan(
            StorageScanOptions(
                start=("scan",),
                end=("scan", "\xff"),
                start_inclusive=True,
                end_inclusive=True,
            )
        )

        items = list(scan.items())
        assert len(items) == 2
        assert items[0][0] == ("scan", "i1")
        assert items[0][1]["id"] == 1
        assert items[1][0] == ("scan", "i2")
        assert items[1][1]["id"] == 2


def test_scan_with_limit(storage):
    """Test scan with limit."""
    # Put test data
    with storage.transaction() as txn:
        for i in range(10):
            txn.put(("scan", f"item{i:02d}"), i)

    # Scan with limit
    with storage.snapshot() as snap:
        scan = snap.scan(
            StorageScanOptions(
                start=("scan",),
                end=("scan", "\xff"),
                limit=5,
                start_inclusive=True,
                end_inclusive=True,
            )
        )

        keys = list(scan.keys())
        assert len(keys) == 5


def test_scan_bounds_exclusive(storage):
    """Test scan with exclusive bounds."""
    # Put test data
    with storage.transaction() as txn:
        txn.put(("scan", "a"), 1)
        txn.put(("scan", "b"), 2)
        txn.put(("scan", "c"), 3)
        txn.put(("scan", "d"), 4)

    # Scan with exclusive bounds (should skip "a" and "d")
    with storage.snapshot() as snap:
        scan = snap.scan(
            StorageScanOptions(
                start=("scan", "a"),
                end=("scan", "d"),
                start_inclusive=False,
                end_inclusive=False,
            )
        )

        keys = list(scan.keys())
        assert len(keys) == 2
        assert keys[0] == ("scan", "b")
        assert keys[1] == ("scan", "c")


def test_scan_in_transaction(storage):
    """Test scan within a transaction."""
    # Put test data
    with storage.transaction() as txn:
        txn.put(("txn_scan", "a"), 1)
        txn.put(("txn_scan", "b"), 2)

    # Scan within transaction
    with storage.transaction() as txn:
        scan = txn.scan(
            StorageScanOptions(
                start=("txn_scan",),
                end=("txn_scan", "\xff"),
                start_inclusive=True,
                end_inclusive=True,
            )
        )

        keys = list(scan.keys())
        assert len(keys) == 2


# ============================================================================
# WRITE BATCH OPERATIONS
# ============================================================================


def test_write_batch_basic_put(storage):
    """Test basic write batch put operation."""
    key = ("batch", "put_test")
    value = {"data": "batch_write"}

    # Write batch with context manager
    with storage.begin_write_batch() as batch:
        batch.put(key, value)
        # Auto-writes on exit

    # Verify data persisted
    with storage.transaction() as txn:
        result = txn.get(key)
        assert result == value


def test_write_batch_explicit_write(storage):
    """Test write batch with explicit write() call."""
    key = ("batch", "explicit")
    value = {"method": "explicit_write"}

    batch = storage.begin_write_batch()
    batch.put(key, value)
    batch.write()

    # Verify data persisted
    with storage.transaction() as txn:
        result = txn.get(key)
        assert result == value


def test_write_batch_delete(storage):
    """Test write batch delete operation."""
    key = ("batch", "delete_test")

    # Put initial data
    with storage.transaction() as txn:
        txn.put(key, {"data": "to_delete"})

    # Delete via write batch
    with storage.begin_write_batch() as batch:
        deleted = batch.delete(key)
        assert deleted is True

    # Verify deletion
    with storage.transaction() as txn:
        assert not txn.has(key)


def test_write_batch_delete_nonexistent(storage):
    """Test write batch delete of nonexistent key returns False."""
    key = ("batch", "nonexistent")

    with storage.begin_write_batch() as batch:
        deleted = batch.delete(key)
        assert deleted is False


def test_write_batch_abort(storage):
    """Test write batch abort discards changes."""
    key = ("batch", "abort_test")

    batch = storage.begin_write_batch()
    batch.put(key, {"data": "should_not_persist"})
    batch.abort()

    # Verify key doesn't exist
    with storage.transaction() as txn:
        assert not txn.has(key)


def test_write_batch_exception_auto_abort(storage):
    """Test write batch auto-aborts on exception."""
    key = ("batch", "exception_test")

    try:
        with storage.begin_write_batch() as batch:
            batch.put(key, {"data": "should_not_persist"})
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify key doesn't exist
    with storage.transaction() as txn:
        assert not txn.has(key)


def test_write_batch_multiple_operations(storage):
    """Test write batch with multiple put/delete operations."""
    keys = [
        ("batch", "multi1"),
        ("batch", "multi2"),
        ("batch", "multi3"),
    ]

    # Setup: put multi3
    with storage.transaction() as txn:
        txn.put(keys[2], {"old": "value"})

    # Batch: put multi1, put multi2, delete multi3
    with storage.begin_write_batch() as batch:
        batch.put(keys[0], {"id": 1})
        batch.put(keys[1], {"id": 2})
        batch.delete(keys[2])

    # Verify all operations
    with storage.transaction() as txn:
        assert txn.get(keys[0])["id"] == 1
        assert txn.get(keys[1])["id"] == 2
        assert not txn.has(keys[2])


def test_write_batch_update_value(storage):
    """Test write batch updating existing value."""
    key = ("batch", "update_test")

    # Initial value
    with storage.transaction() as txn:
        txn.put(key, {"version": 1})

    # Update via write batch
    with storage.begin_write_batch() as batch:
        batch.put(key, {"version": 2})

    # Verify update
    with storage.transaction() as txn:
        result = txn.get(key)
        assert result == {"version": 2}


def test_write_batch_isolation(storage):
    """Test write batch changes not visible until written."""
    key = ("batch", "isolation_test")

    # Start write batch but don't write yet
    batch = storage.begin_write_batch()
    batch.put(key, {"data": "uncommitted"})

    # Verify not visible in transaction
    with storage.transaction() as txn:
        assert not txn.has(key)

    # Write the batch
    batch.write()

    # Now should be visible
    with storage.transaction() as txn:
        assert txn.has(key)

def test_write_batch_operations_after_close_raise(storage):
    """Test write batch operations after close raise error."""
    from redwood.storage import StorageClosedError

    batch = storage.begin_write_batch()
    batch.abort()  # Close the batch

    # Operations after close should raise
    try:
        batch.put(("any", "key"), {"data": "test"})
        assert False, "Should have raised StorageClosedError"
    except StorageClosedError:
        pass


def test_write_batch_bulk_writes(storage):
    """Test write batch efficient bulk write operations."""
    # Write batch should be efficient for bulk operations
    keys = [(f"batch", f"bulk_{i:03d}") for i in range(100)]

    with storage.begin_write_batch() as batch:
        for i, key in enumerate(keys):
            batch.put(key, {"index": i})

    # Verify all written
    with storage.transaction() as txn:
        for i, key in enumerate(keys):
            result = txn.get(key)
            assert result["index"] == i
