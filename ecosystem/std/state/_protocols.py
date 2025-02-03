from abc import abstractmethod
from typing import Any, AsyncIterator, Protocol, runtime_checkable

from ecosystem.std.observer import ObserverProtocol, SubscriptionProtocol
from ecosystem.std.storage import (
    StorageProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)

from ._types import StateCallbackFn, StateKey, StateValue


@runtime_checkable
class StateProtocol(Protocol):
    """
    Provides a unified interface for different data organization strategies
    while maintaining common state access patterns.

    Features:
    - Type-safe state access
    - Transactional operations
    - Change notifications
    - Key space management
    - Subscription handling

    Type Parameters:
        StateKey: Key type (tuple of strings)
        StateValue: Value type
    """

    storage: StorageProtocol[StateKey, StateValue, Any, Any]
    observer: ObserverProtocol[StateKey, Any]

    @abstractmethod
    async def get(self, key: StateKey) -> StateValue:
        """
        Get value at key.

        Args:
            key: Key to retrieve

        Returns:
            Value stored at key

        Raises:
            StorageOperationError: If retrieval fails
            StorageKeyError: If key not found
        """
        ...

    @abstractmethod
    async def set(self, key: StateKey, value: StateValue) -> None:
        """
        Set value at key.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If storage fails
        """
        ...

    @abstractmethod
    async def delete(self, key: StateKey) -> None:
        """
        Delete value at key.

        Args:
            key: Key to delete

        Raises:
            StorageOperationError: If deletion fails
            StorageKeyError: If key not found
        """
        ...

    @abstractmethod
    async def exists(self, key: StateKey) -> bool:
        """
        Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageKeyError: If check fails
        """
        ...

    @abstractmethod
    async def list_keys(self, prefix: StateKey) -> AsyncIterator[StateKey]:
        """
        List all keys under prefix.

        Args:
            prefix: Optional key prefix to filter results

        Returns:
            AsyncIterator of matching keys

        Raises:
            StorageOperationError: If listing fails
        """
        ...

    @abstractmethod
    async def subscribe(
        self, key: StateKey, callback: StateCallbackFn
    ) -> SubscriptionProtocol[StateKey]:
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
    async def unsubscribe(self, subscription: SubscriptionProtocol[StateKey]) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    @abstractmethod
    async def begin_transaction(self) -> TransactionProtocol[StateKey, StateValue]:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    @abstractmethod
    async def transaction(self) -> TransactionContextManagerProtocol[StateKey, StateValue]:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...
