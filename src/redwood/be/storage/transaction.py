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

    from .iterator import IteratorProtocol
    from .types import ScanOptions


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


__all__ = [
    "TransactionProtocol",
]
