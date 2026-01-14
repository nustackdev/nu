"""Transaction protocol definitions.

Defines composable transaction interfaces with different access patterns
and isolation strategies. Protocols are broken down into orthogonal concerns
for maximum flexibility and type safety.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Literal, Protocol, overload, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import TracebackType

    from everyshape.loc import key
    from everyshape.typing import Empty, Value

    from .scan import ScanProtocol
    from .storage import StorageProtocol
    from .types import StorageScanOptions

__all__ = [  # noqa: RUF022
    # Base
    "BaseContextProtocol",
    # Access
    "ReadAccessProtocol",
    "WriteAccessProtocol",
    "ReadWriteAccessProtocol",
    # Composed
    "SnapshotProtocol",
    "WriteBatchProtocol",
    "TransactionProtocol",
    # Storage
    "TransactionalStorageProtocol",
]


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

    @property
    def storage(self) -> StorageProtocol:
        """Get the storage instance.

        Returns:
            Storage this context was initiated from.
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
    def get(self, key: key.Key) -> Value | Empty:
        """Get value at key.

        Args:
            key: Key to retrieve.

        Returns:
            Value at key, or EMPTY if key not found.

        Raises:
            StorageOperationError: If operation fails.
        """
        ...

    def exists(self, key: key.Key) -> bool:
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
    def multiget(self, keys: list[key.Key]) -> dict[key.Key, Value]:
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
    def scan(self, options: StorageScanOptions) -> ScanProtocol:
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
    def put(self, key: key.Key, value: Value) -> None:
        """Put value at key.

        Args:
            key: Key to set.
            value: Value to store.

        Raises:
            StorageWriteError: If write fails.
            StorageClosedError: If context is closed.
        """
        ...

    def delete(self, key: key.Key) -> None:
        """Delete key (idempotent).

        Silent if key doesn't exist.

        Args:
            key: Key to delete.

        Raises:
            StorageDeleteError: If deletion fails.
            StorageClosedError: If context is closed.
        """
        ...


@runtime_checkable
class ReadWriteAccessProtocol(ReadAccessProtocol, WriteAccessProtocol, Protocol):
    """Protocol supporting both read and write operations."""


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
    Protocol,
):
    """Write-only batch protocol.

    Accumulates writes without read capabilities for efficient bulk operations.
    Must be explicitly committed.

    Composition:
        - BaseContextProtocol: Lifecycle management
        - WriteAccessProtocol: Write operations
        - Write/abort
    """

    def write(self) -> None:
        """Write batch.

        Persist all writes.

        Raises:
            StorageTransactionError: If commit fails.
            StorageTransactionConflictError: If optimistic lock conflict.
            StorageClosedError: If already committed or aborted.
        """
        ...

    def abort(self) -> None:
        """Abort write batch.

        Discards all writes.

        Raises:
            StorageTransactionError: If abort fails.
        """
        ...


@runtime_checkable
class TransactionProtocol(
    BaseContextProtocol,
    ReadAccessProtocol,
    WriteAccessProtocol,
    Protocol,
):
    """Full read-write transaction protocol.

    Provides ACID guarantees with both read and write capabilities.
    Supports optimistic and pessimistic locking strategies.

    Composition:
        - BaseContextProtocol: Lifecycle management
        - ReadAccessProtocol: Read operations
        - WriteAccessProtocol: Write operations
        - Commit/abort
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

    @contextmanager
    def transaction(self) -> Iterator[TransactionProtocol]:
        """Context manager for transactions: commit on success, abort on exception."""
        ...

    @contextmanager
    def snapshot(self) -> Iterator[SnapshotProtocol]:
        """Context manager for read-only snapshots: always closes snapshot on exit."""
        ...

    @contextmanager
    def batch_write(self) -> Iterator[WriteBatchProtocol]:
        """Context manager for write batches: commit on success, abort on exception."""
        ...
