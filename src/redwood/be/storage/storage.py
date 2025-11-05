"""Storage protocol definitions.

Defines the abstract interfaces for storage operations, transactions,
and iteration. Implementations must conform to these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import TracebackType

    from redwood.abc import TupleKey, Value

    from .types import ScanOptions, SubscriptionCallback, SubscriptionHandle


@runtime_checkable
class IteratorProtocol(Protocol):
    """Low-level iterator interface for range scans.

    Provides cursor-like navigation over key ranges with bidirectional
    movement and positioning. Similar to LMDB cursors or RocksDB iterators.
    """

    def seek(self, key: TupleKey) -> bool:
        """Seek to key position.

        Args:
            key: Key to seek to.

        Returns:
            True if positioned successfully, False otherwise.
        """
        ...

    def seek_to_first(self) -> bool:
        """Seek to first key.

        Returns:
            True if positioned successfully, False if empty.
        """
        ...

    def seek_to_last(self) -> bool:
        """Seek to last key.

        Returns:
            True if positioned successfully, False if empty.
        """
        ...

    def next(self) -> bool:
        """Move to next key.

        Returns:
            True if moved successfully, False if at end.
        """
        ...

    def prev(self) -> bool:
        """Move to previous key.

        Returns:
            True if moved successfully, False if at beginning.
        """
        ...

    def key(self) -> TupleKey:
        """Get current key.

        Returns:
            Current key at iterator position.

        Raises:
            StorageIteratorError: If iterator is not valid.
        """
        ...

    def value(self) -> Value:
        """Get current value.

        Returns:
            Current value at iterator position.

        Raises:
            StorageIteratorError: If iterator is not valid.
        """
        ...

    def is_valid(self) -> bool:
        """Check if iterator is positioned at valid data.

        Returns:
            True if positioned at valid key/value, False otherwise.
        """
        ...

    def close(self) -> None:
        """Close iterator and release resources."""
        ...

    def __enter__(self) -> IteratorProtocol:
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and close iterator."""
        ...


@runtime_checkable
class TransactionProtocol(Protocol):
    """Transaction interface for atomic operations.

    Provides ACID guarantees for read and write operations with support
    for point, batch, and range access patterns.
    """

    # ========================================================================
    # Point Access
    # ========================================================================

    def get(self, key: TupleKey) -> Value:
        """Get value at key.

        Args:
            key: Key to retrieve.

        Returns:
            Value at key.

        Raises:
            StorageKeyError: If key not found.
            StorageOperationError: If operation fails.
        """
        ...

    def put(self, key: TupleKey, value: Value) -> None:
        """Put value at key.

        Args:
            key: Key to set.
            value: Value to store.

        Raises:
            StorageWriteError: If write fails.
            StorageClosedError: If transaction is closed.
        """
        ...

    def rm(self, key: TupleKey) -> bool:
        """Remove key.

        Args:
            key: Key to remove.

        Returns:
            True if key was removed, False if key didn't exist.

        Raises:
            StorageDeleteError: If deletion fails.
            StorageClosedError: If transaction is closed.
        """
        ...

    def has(self, key: TupleKey) -> bool:
        """Check if key exists.

        Args:
            key: Key to check.

        Returns:
            True if key exists, False otherwise.

        Raises:
            StorageOperationError: If check fails.
        """
        ...

    # ========================================================================
    # Batch Access
    # ========================================================================

    def multiget(self, keys: Iterable[TupleKey]) -> dict[TupleKey, Value]:
        """Get multiple keys.

        Args:
            keys: Keys to retrieve.

        Returns:
            Dict mapping keys to values. Missing keys are omitted.

        Raises:
            StorageOperationError: If operation fails.
        """
        ...

    # ========================================================================
    # Range Access
    # ========================================================================

    def iterator(self) -> IteratorProtocol:
        """Create iterator over all keys.

        Returns:
            New iterator instance.

        Raises:
            StorageOperationError: If iterator creation fails.
        """
        ...

    def range_scan(self, options: ScanOptions) -> IteratorProtocol:
        """Create iterator with scan options.

        Args:
            options: Scan configuration.

        Returns:
            New iterator instance configured with options.

        Raises:
            StorageOperationError: If iterator creation fails.
        """
        ...

    def range_delete(
        self,
        start: TupleKey,
        end: TupleKey,
    ) -> int:
        """Delete all keys in range.

        Args:
            start: Start of range.
            end: End of range.

        Returns:
            Number of keys deleted.

        Raises:
            StorageDeleteError: If deletion fails.
            StorageClosedError: If transaction is closed.
        """
        ...

    # ========================================================================
    # Transaction Control
    # ========================================================================

    def commit(self) -> None:
        """Commit transaction.

        Makes all changes permanent and releases locks.

        Raises:
            StorageTransactionError: If commit fails.
            StorageTransactionConflictError: If optimistic lock conflict.
            StorageClosedError: If already committed or aborted.
        """
        ...

    def abort(self) -> None:
        """Abort transaction.

        Discards all changes and releases locks.

        Raises:
            StorageTransactionError: If abort fails.
        """
        ...

    # ========================================================================
    # Context Manager
    # ========================================================================

    def __enter__(self) -> TransactionProtocol:
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager.

        Commits on success, aborts on exception.
        """
        ...


@runtime_checkable
class StorageProtocol(Protocol):
    """Storage interface with transactions and subscriptions.

    Top-level interface for storage operations. Provides transaction
    management and subscription capabilities.
    """

    # ========================================================================
    # Transaction Management
    # ========================================================================

    def begin(self, *, write: bool = False) -> TransactionProtocol:
        """Begin new transaction.

        Args:
            write: Whether transaction allows writes.

        Returns:
            New transaction instance.

        Raises:
            StorageOperationError: If transaction creation fails.
        """
        ...

    # ========================================================================
    # Subscriptions
    # ========================================================================

    def subscribe(
        self,
        pattern: TupleKey,
        callback: SubscriptionCallback,
    ) -> SubscriptionHandle:
        """Subscribe to key pattern changes.

        Args:
            pattern: Key prefix pattern to match.
            callback: Function called on matching mutations.

        Returns:
            Handle for unsubscribing.

        Raises:
            StorageOperationError: If subscription fails.
        """
        ...

    def unsubscribe(self, handle: SubscriptionHandle) -> None:
        """Unsubscribe from changes.

        Args:
            handle: Subscription handle from subscribe().

        Raises:
            StorageOperationError: If handle invalid or unsubscribe fails.
        """
        ...

    # ========================================================================
    # Lifecycle
    # ========================================================================

    def open(self) -> None:
        """Open storage and initialize resources.

        Raises:
            StorageOperationError: If open fails.
        """
        ...

    def close(self) -> None:
        """Close storage and release resources.

        All transactions must be completed before closing.

        Raises:
            StorageOperationError: If close fails.
        """
        ...


__all__ = [
    "IteratorProtocol",
    "StorageProtocol",
    "TransactionProtocol",
]
