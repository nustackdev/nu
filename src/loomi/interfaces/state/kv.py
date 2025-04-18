from __future__ import annotations

from types import TracebackType
from typing import AsyncGenerator, Generator, Protocol, runtime_checkable

from .observer import AsyncObservableProtocol, SyncObservableProtocol
from .type_vars import StorageValueT
from .types import StorageKey

__all__ = [
    "AsyncStorageProtocol",
    "AsyncObservableProtocol",
    "AsyncObservableStorageProtocol",
    "AsyncTransactionProtocol",
    "AsyncTransactionContextManagerProtocol",
    "AsyncTransactionalHandlerProtocol",
    "SyncStorageProtocol",
    "SyncObservableProtocol",
    "SyncObservableStorageProtocol",
    "SyncTransactionProtocol",
    "SyncTransactionContextManagerProtocol",
    "SyncTransactionalHandlerProtocol",
]

# --- Protocols for asynchronous state handling --- #


class AsyncStorageProtocol(Protocol[StorageValueT]):
    """Protocol for asynchronous state storage adapters."""

    async def get(self, key: StorageKey) -> StorageValueT:
        """
        Get value by key.

        Args:
            key: State key to retrieve

        Returns:
            State value if found, None otherwise

        Raises:
            StateError: If value cannot be retrieved
        """
        ...

    async def set(self, key: StorageKey, value: StorageValueT) -> None:
        """
        Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    async def delete(self, key: StorageKey) -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    async def exists(self, key: StorageKey) -> bool:
        """
        Check if key exists.

        Args:
            key: State key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StateError: If check fails
        """
        ...

    async def list_keys(
        self, prefix: StorageKey, depth: int = ...
    ) -> AsyncGenerator[StorageKey, None]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            AsyncGenerator of matching state keys

        Raises:
            StateError: If listing fails
        """
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true async generator

    async def begin_transaction(self) -> AsyncTransactionProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    async def transaction(self) -> AsyncTransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...


class AsyncObservableStorageProtocol(
    AsyncStorageProtocol[StorageValueT], AsyncObservableProtocol, Protocol
):
    """Protocol for asynchronous observable state storage adapters."""

    pass


@runtime_checkable
class AsyncTransactionProtocol(Protocol[StorageValueT]):
    """Protocol defining the interface for asynchronous transactions."""

    async def get(self, key: StorageKey) -> StorageValueT:
        """
        Get value within transaction context.

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageKeyError: If key not found
            StorageOperationError: If get operation fails
        """
        ...

    async def set(self, key: StorageKey, value: StorageValueT) -> None:
        """
        Set value within transaction context.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If set operation fails
        """
        ...

    async def delete(self, key: StorageKey) -> None:
        """
        Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    async def exists(self, key: StorageKey) -> bool:
        """
        Check if key exists within transaction context.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If exists check fails
        """
        ...

    async def list_keys(
        self, prefix: StorageKey, depth: int = ...
    ) -> AsyncGenerator[StorageKey, None]:
        """
        List all keys under prefix within transaction context.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            AsyncGenerator of matching keys

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If list operation fails
        """
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true async generator

    async def commit(self) -> None:
        """
        Commit all changes in the transaction.

        Raises:
            TransactionError: If commit fails or transaction is invalid
            StorageOperationError: If storage operations fail during commit
        """
        ...

    async def rollback(self) -> None:
        """
        Roll back all changes in the transaction.

        Raises:
            TransactionError: If rollback fails or transaction is invalid
        """
        ...


class AsyncTransactionContextManagerProtocol(Protocol[StorageValueT]):
    """Async context manager for storage transactions."""

    async def __aenter__(self) -> AsyncTransactionProtocol[StorageValueT]:
        """
        Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """
        Commit or rollback transaction based on context exit.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type if an error occurred.
            exc_val (Optional[BaseException]): Exception value if an error occurred.
            exc_tb (Optional[TracebackType]): Exception traceback if an error occurred.

        Returns:
            bool
        """
        ...


class AsyncTransactionalHandlerProtocol(Protocol[StorageValueT]):
    """Protocol defining the interface for asynchronous transactionable storage."""

    async def begin_transaction(self) -> AsyncTransactionProtocol[StorageValueT]:
        """Begin a new transaction."""
        ...

    async def transaction(self) -> AsyncTransactionContextManagerProtocol[StorageValueT]:
        """Get a typed transaction context manager."""
        ...


# --- Protocols for synchronous state handling --- #


class SyncStorageProtocol(Protocol[StorageValueT]):
    """Protocol for synchronous state storage adapters."""

    def get(self, key: StorageKey) -> StorageValueT:
        """
        Get value by key.

        Args:
            key: State key to retrieve

        Returns:
            State value if found, None otherwise

        Raises:
            StateError: If value cannot be retrieved
        """
        ...

    def set(self, key: StorageKey, value: StorageValueT) -> None:
        """
        Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    def delete(self, key: StorageKey) -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    def exists(self, key: StorageKey) -> bool:
        """
        Check if key exists.

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
        prefix: StorageKey,
        depth: int = ...,
    ) -> Generator[StorageValueT, None, None]:
        """
        List all keys under prefix.

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

    def begin_transaction(self) -> SyncTransactionProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> SyncTransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...


class SyncObservableStorageProtocol(
    SyncStorageProtocol[StorageValueT], SyncObservableProtocol, Protocol
):
    """Protocol for synchronous observable state storage adapters."""

    pass


class SyncTransactionProtocol(Protocol[StorageValueT]):
    """Protocol defining the interface for synchronous transactions."""

    def get(self, key: StorageKey) -> StorageValueT:
        """
        Get value within transaction context.

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageKeyError: If key not found
            StorageOperationError: If get operation fails
        """
        ...

    def set(self, key: StorageKey, value: StorageValueT) -> None:
        """
        Set value within transaction context.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If set operation fails
        """
        ...

    def delete(self, key: StorageKey) -> None:
        """
        Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    def exists(self, key: StorageKey) -> bool:
        """
        Check if key exists within transaction context.

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
        prefix: StorageKey,
        depth: int = ...,
    ) -> Generator[StorageValueT, None, None]:
        """
        List all keys under prefix within transaction context.

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
        """
        Commit all changes in the transaction.

        Raises:
            TransactionError: If commit fails or transaction is invalid
            StorageOperationError: If storage operations fail during commit
        """
        ...

    def rollback(self) -> None:
        """
        Roll back all changes in the transaction.

        Raises:
            TransactionError: If rollback fails or transaction is invalid
        """
        ...


class SyncTransactionContextManagerProtocol(Protocol[StorageValueT]):
    """Synchronous context manager for storage transactions."""

    def __enter__(self) -> SyncTransactionProtocol[StorageValueT]:
        """
        Start a new transaction.

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
        """
        Commit or rollback transaction based on context exit.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type if an error occurred.
            exc_val (Optional[BaseException]): Exception value if an error occurred.
            exc_tb (Optional[TracebackType]): Exception traceback if an error occurred.

        Returns:
            None
        """
        ...


class SyncTransactionalHandlerProtocol(Protocol[StorageValueT]):
    """Protocol defining the interface for synchronous transactionable storage."""

    def begin_transaction(self) -> SyncTransactionProtocol[StorageValueT]:
        """Begin a new transaction."""
        ...

    def transaction(self) -> SyncTransactionContextManagerProtocol[StorageValueT]:
        """Get a typed transaction context manager."""
        ...
