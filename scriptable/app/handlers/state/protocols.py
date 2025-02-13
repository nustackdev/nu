from __future__ import annotations

from types import TracebackType
from typing import AsyncGenerator, Generator, Protocol

from .types import AsyncStateCallbackFn, StateKey, StateValue, SyncStateCallbackFn

__all__ = [
    "AsyncStateProtocol",
    "AsyncSubscriptionProtocol",
    "AsyncTransactionProtocol",
    "AsyncTransactionContextManagerProtocol",
    "AsyncTransactionalHandlerProtocol",
    "SyncStateProtocol",
    "SyncSubscriptionProtocol",
    "SyncTransactionProtocol",
    "SyncTransactionContextManagerProtocol",
    "SyncTransactionalHandlerProtocol",
]

# --- Protocols for asynchronous state handling --- #


class AsyncStateProtocol(Protocol):
    """Protocol for asynchronous state storage adapters."""

    async def get(self, key: StateKey) -> StateValue:
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

    async def set(self, key: StateKey, value: StateValue) -> None:
        """
        Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    async def delete(self, key: StateKey) -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    async def exists(self, key: StateKey) -> bool:
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

    async def list_keys(self, prefix: StateKey) -> AsyncGenerator[StateKey, None]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to list

        Returns:
            AsyncGenerator of matching state keys

        Raises:
            StateError: If listing fails
        """
        ...

    async def subscribe(
        self, key: StateKey, callback: AsyncStateCallbackFn
    ) -> AsyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Async callback function for notifications

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        ...

    async def unsubscribe(self, subscription: AsyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

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


class AsyncSubscriptionProtocol(Protocol):
    """
    Represents an asynchronous subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Async callable that will be invoked on matching notifications.
            Must accept a single parameter of type StateKey.

    Type Parameters:
        StateKey: Topic type (tuple of strings)
    """

    @property
    def topic_pattern(self) -> StateKey:
        """
        Get topic pattern for subscription.
        """
        ...

    @property
    def callback(self) -> AsyncStateCallbackFn:
        """
        Get callback for subscription.
        """
        ...


class AsyncTransactionProtocol(Protocol):
    """Protocol defining the interface for asynchronous transactions."""

    async def get(self, key: StateKey) -> StateValue:
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

    async def set(self, key: StateKey, value: StateValue) -> None:
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

    async def delete(self, key: StateKey) -> None:
        """
        Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    async def exists(self, key: StateKey) -> bool:
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

    async def list_keys(self, prefix: StateKey) -> AsyncGenerator[StateKey, None]:
        """
        List all keys under prefix within transaction context.

        Args:
            prefix: Key prefix to list

        Returns:
            AsyncGenerator of matching keys

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If list operation fails
        """
        ...

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


class AsyncTransactionContextManagerProtocol(Protocol):
    """Async context manager for storage transactions."""

    async def __aenter__(self) -> AsyncTransactionProtocol:
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


class AsyncTransactionalHandlerProtocol(Protocol):
    """Protocol defining the interface for asynchronous transactionable storage."""

    async def begin_transaction(self) -> AsyncTransactionProtocol:
        """Begin a new transaction."""
        ...

    async def transaction(self) -> AsyncTransactionContextManagerProtocol:
        """Get a typed transaction context manager."""
        ...


# --- Protocols for synchronous state handling --- #


class SyncStateProtocol(Protocol):
    """Protocol for synchronous state storage adapters."""

    def get(self, key: StateKey) -> StateValue:
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

    def set(self, key: StateKey, value: StateValue) -> None:
        """
        Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    def delete(self, key: StateKey) -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    def exists(self, key: StateKey) -> bool:
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

    def list_keys(self, prefix: StateKey) -> Generator[StateKey, None, None]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to list

        Returns:
            Generator of matching state keys

        Raises:
            StateError: If listing fails
        """
        ...

    def subscribe(self, key: StateKey, callback: SyncStateCallbackFn) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Callback function for notifications

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        ...

    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
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


class SyncSubscriptionProtocol(Protocol):
    """
    Represents a synchronous subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Callable that will be invoked on matching notifications.
            Must accept a single parameter of type StateKey.

    Type Parameters:
        StateKey: Topic type (tuple of strings)
    """

    topic_pattern: StateKey
    callback: SyncStateCallbackFn


class SyncTransactionProtocol(Protocol):
    """Protocol defining the interface for synchronous transactions."""

    def get(self, key: StateKey) -> StateValue:
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

    def set(self, key: StateKey, value: StateValue) -> None:
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

    def delete(self, key: StateKey) -> None:
        """
        Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    def exists(self, key: StateKey) -> bool:
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

    def list_keys(self, prefix: StateKey) -> Generator[StateKey, None, None]:
        """
        List all keys under prefix within transaction context.

        Args:
            prefix: Key prefix to list

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


class SyncTransactionContextManagerProtocol(Protocol):
    """Synchronous context manager for storage transactions."""

    def __init__(self, handler: SyncTransactionalHandlerProtocol):
        """
        Initialize transaction context manager.

        Args:
            storage: Storage instance to manage transactions for
        """
        ...

    def __enter__(self) -> SyncTransactionProtocol:
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


class SyncTransactionalHandlerProtocol(Protocol):
    """Protocol defining the interface for synchronous transactionable storage."""

    def begin_transaction(self) -> SyncTransactionProtocol:
        """Begin a new transaction."""
        ...

    def transaction(self) -> SyncTransactionContextManagerProtocol:
        """Get a typed transaction context manager."""
        ...
