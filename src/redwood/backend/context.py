"""Context protocol definitions for unified transaction and snapshot handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import TupleKey, Value


__all__ = [
    "SnapshotProtocol",
    "StorageContextProtocol",
    "StorageContextType",
    "TransactionProtocol",
]


@runtime_checkable
class StorageContextProtocol(Protocol):
    """Base context protocol for storage operations.

    This protocol defines the minimal interface that all context types
    (transactions, snapshots) must support.
    """

    def get(self, key: TupleKey) -> Value:
        """Get value within transaction context.

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            TransactionError: If transaction is invalid or operation fails
            KeyError: If key not found
            StorageOperationError: If get operation fails
        """
        ...

    def exists(self, key: TupleKey) -> bool:
        """Check if key exists within transaction context.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If exists check fails
        """
        ...

    def list_keys(self, prefix: TupleKey, depth: int = ...) -> Generator[TupleKey, None, None]:
        """List all keys under prefix within transaction context.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching keys

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If list operation fails
        """
        ...

    def __hash__(self) -> int:
        """Get hash of the transaction.

        Returns:
            Hash value of the transaction
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Check equality of the transaction.

        Args:
            other: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


@runtime_checkable
class TransactionProtocol(StorageContextProtocol, Protocol):
    """Transaction context protocol extending base context with write operations.

    Transactions support both read and write operations and provide
    commit/rollback semantics for atomicity.
    """

    def set(self, key: TupleKey, value: Value) -> None:
        """Set value within transaction context.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If set operation fails
        """
        ...

    def delete(self, key: TupleKey) -> None:
        """Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    def commit(self) -> None:
        """Commit all changes in the transaction.

        Raises:
            TransactionError: If commit fails or transaction is invalid
            StorageOperationError: If storage operations fail during commit
        """
        ...

    def rollback(self) -> None:
        """Roll back all changes in the transaction.

        Raises:
            TransactionError: If rollback fails or transaction is invalid
        """
        ...


@runtime_checkable
class SnapshotProtocol(StorageContextProtocol, Protocol):
    """Snapshot context protocol for read-only operations with cleanup.

    Snapshots provide consistent read-only views of data and require
    explicit cleanup when no longer needed.
    """

    def close(self) -> None:
        """Close snapshot and release resources."""
        ...


# Union type for context attributes
type StorageContextType = TransactionProtocol | SnapshotProtocol
