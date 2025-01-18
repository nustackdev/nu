"""State management protocol definitions."""

from __future__ import annotations

from abc import abstractmethod
from types import TracebackType
from typing import AsyncIterator, Protocol, runtime_checkable

from ..types import StateAsyncCallbackFn, StateKey, StateValue


@runtime_checkable
class ServiceStateFeatureProtocol(Protocol):
    """Protocol defining service state management."""

    @abstractmethod
    async def state_get(self, key: StateKey) -> StateValue:
        """
        Get state value at path.

        Args:
            key: State path components

        Returns:
            State value if exists, None otherwise

        Raises:
            StateError: If state access fails
        """
        ...

    @abstractmethod
    async def state_set(self, key: StateKey, value: StateValue) -> None:
        """
        Set state value at path.

        Args:
            key: State path components
            value: Value to store

        Raises:
            StateError: If state update fails
        """
        ...

    @abstractmethod
    async def state_delete(self, key: StateKey) -> None:
        """
        Delete state at path.

        Args:
            key: State path components

        Raises:
            StateError: If state deletion fails
        """
        ...

    @abstractmethod
    async def state_exists(self, key: StateKey) -> bool:
        """
        Check if state exists at path.

        Args:
            key: State path components

        Returns:
            True if state exists, False otherwise

        Raises:
            StateError: If state check fails
        """
        ...

    @abstractmethod
    async def state_list(self, *prefix: str) -> AsyncIterator[StateKey]:
        """
        List all state keys under prefix.

        Args:
            *prefix: State path prefix components

        Returns:
            AsyncIterator of matching state keys

        Raises:
            StateError: If state listing fails
        """
        ...

    @abstractmethod
    async def state_subscribe(
        self, key: StateKey, callback: StateAsyncCallbackFn
    ) -> SubscriptionProtocol:
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

    @abstractmethod
    async def state_unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    @abstractmethod
    async def state_begin_transaction(self) -> TransactionProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    @abstractmethod
    async def state_transaction(self) -> TransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...


@runtime_checkable
class StateProtocol(Protocol):
    """Protocol for state storage adapters."""

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    async def delete(self, key: StateKey) -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    @abstractmethod
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

    @abstractmethod
    async def list_keys(self, prefix: StateKey) -> AsyncIterator[StateKey]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to list

        Returns:
            AsyncIterator of matching state keys

        Raises:
            StateError: If listing fails
        """
        ...

    @abstractmethod
    async def subscribe(
        self, key: StateKey, callback: StateAsyncCallbackFn
    ) -> SubscriptionProtocol:
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

    @abstractmethod
    async def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    @abstractmethod
    async def begin_transaction(self) -> TransactionProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    @abstractmethod
    async def transaction(self) -> TransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...


@runtime_checkable
class SubscriptionProtocol(Protocol):
    """
    Represents a subscription to a topic pattern.

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

    topic_pattern: StateKey
    callback: StateAsyncCallbackFn


@runtime_checkable
class TransactionProtocol(Protocol):
    """Protocol defining the interface for transactions."""

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    async def list_keys(self, prefix: StateKey) -> AsyncIterator[StateKey]:
        """
        List all keys under prefix within transaction context.

        Args:
            prefix: Key prefix to list

        Returns:
            AsyncIterator of matching keys

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If list operation fails
        """
        ...

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit all changes in the transaction.

        Raises:
            TransactionError: If commit fails or transaction is invalid
            StorageOperationError: If storage operations fail during commit
        """
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """
        Roll back all changes in the transaction.

        Raises:
            TransactionError: If rollback fails or transaction is invalid
        """
        ...


@runtime_checkable
class TransactionContextManagerProtocol(Protocol):
    """Async context manager for storage transactions."""

    def __init__(self, handler: TransactionalHandlerProtocol):
        """
        Initialize transaction context manager.

        Args:
            storage: Storage instance to manage transactions for
        """
        ...

    async def __aenter__(self) -> TransactionProtocol:
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


class TransactionalHandlerProtocol(Protocol):
    """Protocol defining the interface for transactionable storage."""

    @abstractmethod
    async def begin_transaction(self) -> TransactionProtocol:
        """Begin a new transaction."""
        ...

    @abstractmethod
    async def transaction(self) -> TransactionContextManagerProtocol:
        """Get a typed transaction context manager."""
        ...
