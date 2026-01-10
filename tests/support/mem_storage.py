"""Minimal in-memory storage for testing.

This is a lightweight storage implementation used exclusively for testing
everyshape's container and view operations. It implements the StorageProtocol
with just enough functionality to verify behavior.

NOT intended for production use - use everybase adapters for real storage.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from everyshape.storage import (
    StorageClosedError,
    StorageKeyError,
    StorageScanOptions,
    StorageTransactionAbortedError,
)


if TYPE_CHECKING:
    from collections.abc import Iterator

    from everyshape.loc import key
    from everyshape.storage import (
        SnapshotProtocol,
        TransactionProtocol,
        WriteBatchProtocol,
    )
    from everyshape.types import Value


class MemoryTransaction:
    """In-memory transaction with basic isolation."""

    def __init__(
        self,
        data: dict[key.Key, Value],
        read_only: bool = False,
        write_only: bool = False,
    ) -> None:
        self._storage_data = data
        self._read_only = read_only
        self._write_only = write_only
        self._writes: dict[key.Key, Value] = {}
        self._deletes: set[key.Key] = set()
        self._committed = False
        self._aborted = False
        self._closed = False

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def is_active(self) -> bool:
        return not self._closed and not self._committed and not self._aborted

    @property
    def storage(self):
        return None  # Not needed for tests

    def get(self, key: key.Key) -> Value:
        """Get value at key."""
        if self._write_only:
            raise StorageClosedError("Cannot read from write-only batch")

        if self._closed:
            raise StorageClosedError("Transaction is closed")

        # Check writes first (read your own writes)
        if key in self._writes:
            return self._writes[key]

        # Check if deleted
        if key in self._deletes:
            raise StorageKeyError(f"Key not found: {key}")

        # Check storage
        if key in self._storage_data:
            return self._storage_data[key]

        raise StorageKeyError(f"Key not found: {key}")

    def has(self, key: key.Key) -> bool:
        """Check if key exists."""
        if self._write_only:
            raise StorageClosedError("Cannot read from write-only batch")

        try:
            self.get(key)
            return True
        except StorageKeyError:
            return False

    def multiget(self, keys: list[key.Key]) -> dict[key.Key, Value]:
        """Get multiple keys."""
        result = {}
        for k in keys:
            try:
                result[k] = self.get(k)
            except StorageKeyError:
                pass
        return result

    def put(self, key: key.Key, value: Value) -> None:
        """Put value at key."""
        if self._read_only:
            raise StorageClosedError("Cannot write to read-only snapshot")

        if self._closed:
            raise StorageClosedError("Transaction is closed")

        self._writes[key] = value
        self._deletes.discard(key)

    def delete(self, key: key.Key) -> bool:
        """Delete key."""
        if self._read_only:
            raise StorageClosedError("Cannot write to read-only snapshot")

        if self._closed:
            raise StorageClosedError("Transaction is closed")

        existed = key in self._storage_data or key in self._writes
        self._deletes.add(key)
        self._writes.pop(key, None)
        return existed

    def scan(self, options: StorageScanOptions):
        """Scan is not implemented for minimal test storage."""
        raise NotImplementedError("Scan not implemented in test storage")

    def commit(self) -> None:
        """Commit transaction."""
        if self._read_only:
            raise StorageClosedError("Cannot commit read-only snapshot")

        if self._closed:
            raise StorageClosedError("Transaction already closed")

        if self._aborted:
            raise StorageTransactionAbortedError("Transaction was aborted")

        # Apply writes
        for k, v in self._writes.items():
            self._storage_data[k] = v

        # Apply deletes
        for k in self._deletes:
            self._storage_data.pop(k, None)

        self._committed = True
        self._closed = True

    def write(self) -> None:
        """Commit write batch (alias for commit)."""
        self.commit()

    def abort(self) -> None:
        """Abort transaction."""
        if self._closed:
            raise StorageClosedError("Transaction already closed")

        self._aborted = True
        self._closed = True
        self._writes.clear()
        self._deletes.clear()

    def close(self) -> None:
        """Close snapshot (for read-only)."""
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._closed:
            if self._read_only:
                self.close()
            elif exc_type is not None:
                self.abort()
            else:
                self.commit()


class MemoryStorage:
    """Minimal in-memory storage implementing StorageProtocol.

    This is a simple dict-based storage for testing. It provides basic
    transaction support with snapshot isolation.

    Example:
        >>> storage = MemoryStorage()
        >>> with storage.begin() as tx:
        ...     tx.put(("key",), "value")
        ...     tx.commit()
    """

    def __init__(self) -> None:
        self._data: dict[key.Key, Value] = {}
        self._closed = False

    @property
    def read_only(self) -> bool:
        return False

    def open(self) -> None:
        """Open storage (no-op for memory storage)."""
        pass

    def close(self) -> None:
        """Close storage."""
        self._closed = True
        self._data.clear()

    def begin(
        self,
        *,
        read_only: bool = False,
        write_only: bool = False,
    ) -> SnapshotProtocol | WriteBatchProtocol | TransactionProtocol:
        """Begin transaction."""
        if self._closed:
            raise StorageClosedError("Storage is closed")

        return MemoryTransaction(self._data, read_only, write_only)

    def begin_snapshot(self) -> SnapshotProtocol:
        """Begin read-only snapshot."""
        return self.begin(read_only=True)  # type: ignore

    def begin_transaction(self) -> TransactionProtocol:
        """Begin read-write transaction."""
        return self.begin()  # type: ignore

    def begin_write_batch(self) -> WriteBatchProtocol:
        """Begin write-only batch."""
        return self.begin(write_only=True)  # type: ignore

    @contextmanager
    def transaction(self) -> Iterator[TransactionProtocol]:
        """Context manager for transactions."""
        tx = self.begin_transaction()
        try:
            yield tx
            if not tx.is_closed:
                tx.commit()
        except Exception:
            if not tx.is_closed:
                tx.abort()
            raise

    @contextmanager
    def snapshot(self) -> Iterator[SnapshotProtocol]:
        """Context manager for snapshots."""
        snap = self.begin_snapshot()
        try:
            yield snap
        finally:
            if not snap.is_closed:
                snap.close()

    @contextmanager
    def batch_write(self) -> Iterator[WriteBatchProtocol]:
        """Context manager for write batches."""
        batch = self.begin_write_batch()
        try:
            yield batch
            if not batch.is_closed:
                batch.write()
        except Exception:
            if not batch.is_closed:
                batch.abort()
            raise

    def subscribe(self, options):
        """Subscribe not implemented for test storage."""
        raise NotImplementedError("Subscribe not implemented in test storage")
