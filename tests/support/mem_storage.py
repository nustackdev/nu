"""Minimal in-memory storage for testing.

This is a lightweight storage implementation used exclusively for testing
everyshape's container and view operations. It implements the StorageProtocol
and ObserverProtocol with just enough functionality to verify behavior.

NOT intended for production use - use everybase adapters for real storage.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from everyshape.storage import (
    StorageClosedError,
    StorageScanOptions,
    StorageTransactionAbortedError,
)
from everyshape.storage.observer.registry import SubscriptionRegistry
from everyshape.storage.storage.exceptions import StorageInterfaceError
from everyshape.types import EMPTY, Empty


if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from everyshape.loc import key
    from everyshape.storage import (
        SnapshotProtocol,
        TransactionProtocol,
        WriteBatchProtocol,
    )
    from everyshape.storage.observer.options import SubscriptionOptions
    from everyshape.storage.observer.types import SubscriptionCallback
    from everyshape.storage.storage.scan import ScanProtocol
    from everyshape.types import Value


class MemoryScan:
    """In-memory scan implementation."""

    def __init__(
        self,
        data: list[tuple[key.Key, Value]],
    ) -> None:
        self._data = data
        self._index = 0

    def items(self) -> Generator[tuple[key.Key, Value], None, None]:
        """Iterate over (key, value) tuples."""
        yield from self._data

    def keys(self) -> Generator[key.Key, None, None]:
        """Iterate over keys only."""
        for k, _ in self._data:
            yield k

    def values(self) -> Generator[Value, None, None]:
        """Iterate over values only."""
        for _, v in self._data:
            yield v


@dataclass(eq=False)
class MemorySubscription:
    """In-memory subscription implementation."""

    _options: SubscriptionOptions
    _observer: MemoryObserver
    _receivers: list[SubscriptionCallback] = field(default_factory=list, init=False)
    _closed: bool = field(default=False, init=False)

    def __hash__(self) -> int:
        return id(self)

    @property
    def options(self) -> SubscriptionOptions:
        return self._options

    @property
    def filter(self):
        return self._options.filter

    @property
    def receivers(self) -> tuple[SubscriptionCallback, ...]:
        return tuple(self._receivers)

    @property
    def is_closed(self) -> bool:
        return self._closed

    def bind(self, receiver: SubscriptionCallback) -> None:
        if self._closed:
            raise ValueError("Cannot bind to a closed subscription")
        if receiver not in self._receivers:
            self._receivers.append(receiver)

    def unbind(self, receiver: SubscriptionCallback) -> None:
        try:
            self._receivers.remove(receiver)
        except ValueError as e:
            raise ValueError("Receiver is not bound to this subscription") from e

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._receivers.clear()
            self._observer._close_subscription(self)

    def notify(self, key: key.Key) -> Generator[Exception, None, None]:
        for receiver in self._receivers:
            try:
                receiver(key)
            except Exception as e:
                yield e


class MemoryObserver:
    """In-memory observer implementation."""

    def __init__(self) -> None:
        self._registry = SubscriptionRegistry()
        self._codec = None  # Not needed for tests

    @property
    def codec(self):
        return self._codec

    def subscribe(self, options: SubscriptionOptions) -> MemorySubscription:
        sub = MemorySubscription(_options=options, _observer=self)
        self._registry.add(sub)
        return sub

    def notify(self, topic: key.Key) -> None:
        matches = self._registry.match(topic)
        for sub in matches:
            # Collect errors but don't stop notification
            list(sub.notify(topic))

    def _close_subscription(self, subscription: MemorySubscription) -> None:
        self._registry.remove(subscription)


class MemoryTransaction:
    """In-memory transaction with basic isolation."""

    def __init__(
        self,
        data: dict[key.Key, Value],
        observer: MemoryObserver | None = None,
        read_only: bool = False,
        write_only: bool = False,
        storage: MemoryStorage | None = None,
    ) -> None:
        self._storage_data = data
        self._observer = observer
        self._read_only = read_only
        self._write_only = write_only
        self._storage = storage
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
        return self._storage

    def get(self, key: key.Key) -> Value | Empty:
        """Get value at key.

        Returns:
            Value at key, or EMPTY if not found.
        """
        if self._closed:
            raise StorageClosedError("Transaction is closed")

        if self._write_only:
            raise StorageInterfaceError("Cannot read from write-only batch")

        # Check writes first (read your own writes)
        if key in self._writes:
            return self._writes[key]

        # Check if deleted
        if key in self._deletes:
            return EMPTY

        # Check storage
        if key in self._storage_data:
            return self._storage_data[key]

        return EMPTY

    def exists(self, key: key.Key) -> bool:
        """Check if key exists."""
        # get() handles closed and write_only checks
        return self.get(key) is not EMPTY

    def multiget(self, keys: list[key.Key]) -> dict[key.Key, Value]:
        """Get multiple keys. Missing keys are omitted."""
        result = {}
        for k in keys:
            value = self.get(k)
            if value is not EMPTY:
                result[k] = value
        return result

    def put(self, key: key.Key, value: Value) -> None:
        """Put value at key."""
        if self._closed:
            raise StorageClosedError("Transaction is closed")

        if self._read_only:
            raise StorageInterfaceError("Cannot write to read-only snapshot")

        self._writes[key] = value
        self._deletes.discard(key)

    def delete(self, key: key.Key) -> None:
        """Delete key (idempotent). Silent if key doesn't exist."""
        if self._closed:
            raise StorageClosedError("Transaction is closed")

        if self._read_only:
            raise StorageInterfaceError("Cannot write to read-only snapshot")

        self._deletes.add(key)
        self._writes.pop(key, None)

    def scan(self, options: StorageScanOptions) -> ScanProtocol:
        """Scan keys with filtering support.

        Args:
            options: Scan options including start, reverse, limit, filter, break_filter.

        Returns:
            ScanProtocol instance for iteration.
        """
        if self._closed:
            raise StorageClosedError("Transaction is closed")

        if self._write_only:
            raise StorageInterfaceError("Cannot read from write-only batch")

        # Build effective data view (storage + writes - deletes)
        effective: dict[key.Key, Value] = {}
        for k, v in self._storage_data.items():
            if k not in self._deletes:
                effective[k] = v
        for k, v in self._writes.items():
            effective[k] = v

        # Sort keys
        all_keys = sorted(effective.keys())
        if options.reverse:
            all_keys = list(reversed(all_keys))

        # Find start position
        if options.start is not None:
            if options.reverse:
                # For reverse, start from keys <= start
                all_keys = [k for k in all_keys if k <= options.start]
            else:
                # For forward, start from keys >= start
                all_keys = [k for k in all_keys if k >= options.start]

        # Apply filters and collect results
        results: list[tuple[key.Key, Value]] = []
        count = 0

        for k in all_keys:
            # Check break_filter first - stop if key doesn't match
            if options.break_filter is not None:
                if not options.break_filter.matches(k):
                    break

            # Check filter - skip if key doesn't match
            if options.filter is not None:
                if not options.filter.matches(k):
                    continue

            # Check limit
            if options.limit is not None and count >= options.limit:
                break

            results.append((k, effective[k]))
            count += 1

        return MemoryScan(results)

    def commit(self) -> None:
        """Commit transaction."""
        if self._closed:
            raise StorageClosedError("Transaction already closed")

        if self._read_only:
            raise StorageInterfaceError("Cannot commit read-only snapshot")

        if self._aborted:
            raise StorageTransactionAbortedError("Transaction was aborted")

        # Collect changed keys for notification
        changed_keys = set(self._writes.keys()) | self._deletes

        # Apply writes
        for k, v in self._writes.items():
            self._storage_data[k] = v

        # Apply deletes
        for k in self._deletes:
            self._storage_data.pop(k, None)

        self._committed = True
        self._closed = True

        # Notify observer of all changes
        if self._observer is not None:
            for k in changed_keys:
                self._observer.notify(k)

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
    """Minimal in-memory storage implementing StorageProtocol and ObserverProtocol.

    This is a simple dict-based storage for testing. It provides basic
    transaction support with snapshot isolation and observer notifications.

    Example:
        >>> storage = MemoryStorage()
        >>> with storage.begin() as tx:
        ...     tx.put(("key",), "value")
        ...     tx.commit()
    """

    def __init__(self) -> None:
        self._data: dict[key.Key, Value] = {}
        self._observer = MemoryObserver()
        self._closed = False

    @property
    def read_only(self) -> bool:
        return False

    @property
    def codec(self):
        """Get key codec (not used in memory storage)."""
        return self._observer.codec

    def open(self) -> None:
        """Open storage (no-op for memory storage)."""
        pass

    def close(self) -> None:
        """Close storage."""
        self._closed = True
        self._data.clear()
        self._observer._registry.clear()

    def begin(
        self,
        *,
        read_only: bool = False,
        write_only: bool = False,
    ) -> SnapshotProtocol | WriteBatchProtocol | TransactionProtocol:
        """Begin transaction."""
        if self._closed:
            raise StorageClosedError("Storage is closed")

        return MemoryTransaction(
            self._data,
            observer=self._observer,
            read_only=read_only,
            write_only=write_only,
            storage=self,
        )

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

    def subscribe(self, options: SubscriptionOptions) -> MemorySubscription:
        """Subscribe to key changes with flexible filtering.

        Args:
            options: Subscription options including filter specification.

        Returns:
            Subscription object for binding callbacks and managing lifecycle.
        """
        if self._closed:
            raise StorageClosedError("Storage is closed")
        return self._observer.subscribe(options)

    def notify(self, topic: key.Key) -> None:
        """Notify observers of a change at the specified topic.

        Args:
            topic: Topic identifying changed state.
        """
        self._observer.notify(topic)
