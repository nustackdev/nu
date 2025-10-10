from __future__ import annotations

from collections.abc import Generator
from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from .type_vars import ValueT, ValueT_co
from .types import Key


__all__ = [
    "StorageProtocol",
    "TransactionProtocol",
    "TransactionContextManagerProtocol",
    "TransactionalHandlerProtocol",
    "SnapshotProtocol",
    "SnapshotContextManagerProtocol",
    "SnapshotHandlerProtocol",
]


class StorageProtocol(Protocol[ValueT]):
    """Protocol for state storage adapters."""

    def get(self, key: Key) -> ValueT:
        """Get value by key.

        Args:
            key: State key to retrieve

        Returns:
            State value if found, None otherwise

        Raises:
            StateError: If value cannot be retrieved
        """
        ...

    def set(self, key: Key, value: ValueT) -> None:
        """Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    def delete(self, key: Key) -> None:
        """Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    def exists(self, key: Key) -> bool:
        """Check if key exists.

        Args:
            key: State key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StateError: If check fails
        """
        ...

    def list_keys(
        self,
        prefix: Key,
        depth: int = ...,
    ) -> Generator[Key, None, None]:
        """List all keys under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching state keys

        Raises:
            StateError: If listing fails
        """
        ...

    def begin_transaction(self) -> TransactionProtocol[ValueT]:
        """Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> TransactionContextManagerProtocol[ValueT]:
        """Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...

    def begin_snapshot(self) -> SnapshotProtocol[ValueT]:
        """Begin snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be started
        """
        ...

    def snapshot(self) -> SnapshotContextManagerProtocol[ValueT]:
        """Get snapshot context manager.

        Returns:
            Snapshot context manager
        """
        ...

    def __hash__(self) -> int:
        """Get hash of the storage.

        Returns:
            Hash value of the storage
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the storage.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


@runtime_checkable
class TransactionProtocol(Protocol[ValueT]):
    """Protocol defining the interface for transactions."""

    def get(self, key: Key) -> ValueT:
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

    def set(self, key: Key, value: ValueT) -> None:
        """Set value within transaction context.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If set operation fails
        """
        ...

    def delete(self, key: Key) -> None:
        """Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    def exists(self, key: Key) -> bool:
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

    def list_keys(
        self,
        prefix: Key,
        depth: int = ...,
    ) -> Generator[Key, None, None]:
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

    def __hash__(self) -> int:
        """Get hash of the transaction.

        Returns:
            Hash value of the transaction
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the transaction.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class TransactionContextManagerProtocol(Protocol[ValueT]):
    """Context manager for storage transactions."""

    def __enter__(self) -> TransactionProtocol[ValueT]:
        """Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit or rollback transaction based on context exit.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type if an error occurred.
            exc_val (Optional[BaseException]): Exception value if an error occurred.
            exc_tb (Optional[TracebackType]): Exception traceback if an error occurred.

        Returns:
            None
        """
        ...


class TransactionalHandlerProtocol(Protocol[ValueT]):
    """Protocol defining the interface for transactionable storage."""

    def begin_transaction(self) -> TransactionProtocol[ValueT]:
        """Begin a new transaction."""
        ...

    def transaction(self) -> TransactionContextManagerProtocol[ValueT]:
        """Get a typed transaction context manager."""
        ...


@runtime_checkable
class SnapshotProtocol(Protocol[ValueT_co]):
    """Protocol defining the interface for read-only snapshots."""

    def get(self, key: Key) -> ValueT_co:
        """Get value within snapshot context.

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            KeyError: If key not found
            StorageOperationError: If get operation fails
        """
        ...

    def exists(self, key: Key) -> bool:
        """Check if key exists within snapshot context.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageOperationError: If exists check fails
        """
        ...

    def list_keys(
        self,
        prefix: Key,
        depth: int = ...,
    ) -> Generator[Key, None, None]:
        """List all keys under prefix within snapshot context.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching keys

        Raises:
            StorageOperationError: If list operation fails
        """
        ...

    def close(self) -> None:
        """Close snapshot and clean up resources.

        Raises:
            StorageOperationError: If cleanup fails
        """
        ...

    def __hash__(self) -> int:
        """Get hash of the snapshot.

        Returns:
            Hash value of the snapshot
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the snapshot.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class SnapshotContextManagerProtocol(Protocol[ValueT_co]):
    """Context manager for storage snapshots."""

    def __enter__(self) -> SnapshotProtocol[ValueT_co]:
        """Create a new snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be created
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up snapshot resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        ...


class SnapshotHandlerProtocol(Protocol[ValueT_co]):
    """Protocol defining the interface for snapshot-capable storage."""

    def begin_snapshot(self) -> SnapshotProtocol[ValueT_co]:
        """Begin a new read-only snapshot."""
        ...

    def snapshot(self) -> SnapshotContextManagerProtocol[ValueT_co]:
        """Get a typed snapshot context manager."""
        ...
