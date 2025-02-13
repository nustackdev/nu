from typing import Any, AsyncGenerator, Protocol

from ecosystem.std.observer import ObserverProtocol, SubscriptionProtocol
from ecosystem.std.storage import (
    StorageProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)

from ._types import StateCallbackFn, StateKey, StateValue


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

    @property
    def storage(self) -> StorageProtocol[StateKey, StateValue, Any, Any]:
        """
        Get storage backend.

        Returns:
            Storage instance
        """
        ...

    @property
    def observer(self) -> ObserverProtocol[StateKey, Any]:
        """
        Get observer backend.

        Returns:
            Observer instance
        """
        ...

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

    async def list_keys(self, prefix: StateKey) -> AsyncGenerator[StateKey, None]:
        """
        List all keys under prefix.

        Args:
            prefix: Optional key prefix to filter results

        Returns:
            AsyncGenerator of matching keys

        Raises:
            StorageOperationError: If listing fails
        """
        ...

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

    async def unsubscribe(self, subscription: SubscriptionProtocol[StateKey]) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    async def begin_transaction(self) -> TransactionProtocol[StateKey, StateValue]:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    async def transaction(self) -> TransactionContextManagerProtocol[StateKey, StateValue]:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...
