"""Transaction protocol definitions.

Defines composable transaction interfaces with different access patterns
and isolation strategies. Protocols are broken down into orthogonal concerns
for maximum flexibility and type safety.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, overload, runtime_checkable


if TYPE_CHECKING:
    from types import TracebackType

    from redwood.abc import TupleKey, Value

    from .scan import ScanProtocol
    from .types import ScanOptions


# ============================================================================
# Base Protocol
# ============================================================================


@runtime_checkable
class BaseContextProtocol(Protocol):
    """Base protocol for all storage contexts.

    Provides lifecycle management and context manager support.
    All transaction types inherit from this protocol.
    """

    @property
    def is_closed(self) -> bool:
        """Check if context is closed.

        Returns:
            True if closed, False otherwise.
        """
        ...

    @property
    def is_active(self) -> bool:
        """Check if context is active.

        Returns:
            True if active and not closed, False otherwise.
        """
        ...

    def __enter__(self) -> BaseContextProtocol:
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager."""
        ...


# ============================================================================
# Access Protocols (Composable)
# ============================================================================


@runtime_checkable
class ReadAccessProtocol(Protocol):
    """Protocol for read operations.

    Provides point, batch, and range read access patterns.
    Can be composed with other protocols.
    """

    # Point access
    def get(self, key: TupleKey, default: Value | None = None) -> Value:
        """Get value at key.

        Args:
            key: Key to retrieve.
            default: Default value if key not found.

        Returns:
            Value at key, or default if not found.

        Raises:
            StorageKeyError: If key not found and no default provided.
            StorageOperationError: If operation fails.
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

    # Batch access
    def multiget(self, keys: list[TupleKey]) -> dict[TupleKey, Value]:
        """Get multiple keys.

        Args:
            keys: List of keys to retrieve.

        Returns:
            Dict mapping keys to values. Missing keys are omitted.

        Raises:
            StorageOperationError: If operation fails.
        """
        ...

    # Range access
    def scan(self, options: ScanOptions) -> ScanProtocol:
        """Create a Pythonic scan handle with configured options.

        Args:
            options: Scan configuration (bounds, direction, limits).

        Returns:
            A ScanProtocol that exposes dict-like iteration via
            .items(), .keys(), and .values().

        Raises:
            StorageOperationError: If scan creation fails.
        """
        ...


@runtime_checkable
class WriteAccessProtocol(Protocol):
    """Protocol for write operations.

    Provides point, batch, and range write access patterns.
    Can be composed with other protocols.
    """

    # Point access
    def put(self, key: TupleKey, value: Value) -> None:
        """Put value at key.

        Args:
            key: Key to set.
            value: Value to store.

        Raises:
            StorageWriteError: If write fails.
            StorageClosedError: If context is closed.
        """
        ...

    def delete(self, key: TupleKey) -> bool:
        """Delete key.

        Args:
            key: Key to delete.

        Returns:
            True if key was deleted, False if key didn't exist.

        Raises:
            StorageDeleteError: If deletion fails.
            StorageClosedError: If context is closed.
        """
        ...

    # Range access
    def range_delete(
        self,
        start: TupleKey,
        end: TupleKey,
        *,
        start_inclusive: bool = True,
        end_inclusive: bool = False,
    ) -> int:
        """Delete all keys in range.

        Args:
            start: Start of range.
            end: End of range.
            start_inclusive: Whether start is inclusive.
            end_inclusive: Whether end is inclusive.

        Returns:
            Number of keys deleted.

        Raises:
            StorageDeleteError: If deletion fails.
            StorageClosedError: If context is closed.
        """
        ...


@runtime_checkable
class TransactionControlProtocol(Protocol):
    """Protocol for transaction control operations.

    Provides commit and abort semantics for atomic operations.
    """

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


# ============================================================================
# Composed Transaction Protocols
# ============================================================================


@runtime_checkable
class SnapshotProtocol(BaseContextProtocol, ReadAccessProtocol, Protocol):
    """Read-only snapshot protocol.

    Provides consistent point-in-time read access without write capabilities.
    Automatically released on context exit.

    Composition:
        - BaseContextProtocol: Lifecycle management
        - ReadAccessProtocol: Read operations
    """

    def close(self) -> None:
        """Close snapshot.

        Releases resources associated with the snapshot.
        """
        ...


@runtime_checkable
class WriteBatchProtocol(
    BaseContextProtocol,
    WriteAccessProtocol,
    TransactionControlProtocol,
    Protocol,
):
    """Write-only batch protocol.

    Accumulates writes without read capabilities for efficient bulk operations.
    Must be explicitly committed.

    Composition:
        - BaseContextProtocol: Lifecycle management
        - WriteAccessProtocol: Write operations
        - TransactionControlProtocol: Commit/abort
    """


@runtime_checkable
class TransactionProtocol(
    BaseContextProtocol,
    ReadAccessProtocol,
    WriteAccessProtocol,
    TransactionControlProtocol,
    Protocol,
):
    """Full read-write transaction protocol.

    Provides ACID guarantees with both read and write capabilities.
    Supports optimistic and pessimistic locking strategies.

    Composition:
        - BaseContextProtocol: Lifecycle management
        - ReadAccessProtocol: Read operations
        - WriteAccessProtocol: Write operations
        - TransactionControlProtocol: Commit/abort
    """


# ============================================================================
# Storage Protocol with Transaction Management
# ============================================================================


@runtime_checkable
class TransactionalStorageProtocol(Protocol):
    """Storage protocol with typed transaction creation.

    Provides overloaded begin() methods with proper return types based on
    write parameter. Supports backend-specific transaction options.
    """

    @overload
    def begin(self, *, read_only: Literal[True]) -> SnapshotProtocol: ...

    @overload
    def begin(self, *, write_only: Literal[True]) -> WriteBatchProtocol: ...

    @overload
    def begin(
        self, *, read_only: Literal[False], write_only: Literal[False]
    ) -> TransactionProtocol: ...

    def begin(
        self,
        *,
        read_only: bool = False,
        write_only: bool = False,
    ) -> WriteBatchProtocol | SnapshotProtocol | TransactionProtocol:
        """Begin new transaction with specified access level.

        Args:
            read_only: If True, creates a read-only snapshot.
            write_only: If True, creates a write-only batch.

        Returns:
            SnapshotProtocol if read_only=True
            WriteBatchProtocol if write_only=True
            TransactionProtocol otherwise

        Raises:
            StorageOperationError: If transaction creation fails.
        """
        ...

    def begin_snapshot(self) -> SnapshotProtocol:
        """Begin read-only snapshot.

        Convenience method for creating snapshots.
        More efficient than full transactions when only reads are needed.

        Returns:
            New snapshot instance.

        Raises:
            StorageOperationError: If snapshot creation fails.
        """
        ...

    def begin_transaction(
        self,
    ) -> TransactionProtocol:
        """Begin read-write transaction.

        Convenience method for creating transactions.

        Returns:
            New transaction instance.

        Raises:
            StorageOperationError: If transaction creation fails.
        """
        ...

    def begin_write_batch(self) -> WriteBatchProtocol:
        """Begin write-only batch.

        Creates a write batch for bulk operations without read capabilities.
        More efficient than transactions when reads are not needed.

        Returns:
            New write batch instance.

        Raises:
            StorageOperationError: If batch creation fails.
        """
        ...


__all__ = [  # noqa: RUF022
    # Base
    "BaseContextProtocol",
    # Access
    "ReadAccessProtocol",
    "WriteAccessProtocol",
    "TransactionControlProtocol",
    # Composed
    "SnapshotProtocol",
    "WriteBatchProtocol",
    "TransactionProtocol",
    # Storage
    "TransactionalStorageProtocol",
]
