from typing import TYPE_CHECKING, AsyncIterator, Iterator, Protocol

if TYPE_CHECKING:
    from scriptable.app.handlers.state import (
        AsyncStateCallbackFn,
        AsyncSubscriptionProtocol,
        StateKey,
        StateValue,
        SyncStateCallbackFn,
        SyncSubscriptionProtocol,
    )


__all__ = [
    "SyncAccessorContextProtocol",
    "AsyncAccessorContextProtocol",
]


class SyncAccessorContextProtocol(Protocol):
    """Protocol defining interface for value access context (state or transaction)."""

    def get(self, key: "StateKey") -> "StateValue":
        """
        Get value by key.

        Args:
            key: State key to retrieve value for

        Returns:
            Value if found, None if not found

        Raises:
            StorageError: If get operation fails
        """
        ...

    def set(self, key: "StateKey", value: "StateValue") -> None:
        """
        Set value by key.

        Args:
            key: State key to set value for
            value: Value to store

        Raises:
            StorageError: If set operation fails
        """
        ...

    def delete(self, key: "StateKey") -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete value for

        Raises:
            StorageError: If delete operation fails
        """
        ...

    def exists(self, key: "StateKey") -> bool:
        """
        Check if key exists.

        Args:
            key: State key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageError: If check fails
        """
        ...

    def list_keys(self, prefix: "StateKey") -> Iterator["StateKey"]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to list under

        Returns:
            AsyncIterator yielding matching keys

        Raises:
            StorageError: If listing fails
        """
        ...

    def subscribe(
        self, key: "StateKey", callback: "SyncStateCallbackFn"
    ) -> "SyncSubscriptionProtocol":
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

    def unsubscribe(self, subscription: "SyncSubscriptionProtocol") -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...


class AsyncAccessorContextProtocol(Protocol):
    """Protocol defining interface for value access context (state or transaction)."""

    async def get(self, key: "StateKey") -> "StateValue":
        """
        Get value by key.

        Args:
            key: State key to retrieve value for

        Returns:
            Value if found, None if not found

        Raises:
            StorageError: If get operation fails
        """
        ...

    async def set(self, key: "StateKey", value: "StateValue") -> None:
        """
        Set value by key.

        Args:
            key: State key to set value for
            value: Value to store

        Raises:
            StorageError: If set operation fails
        """
        ...

    async def delete(self, key: "StateKey") -> None:
        """
        Delete value by key.

        Args:
            key: State key to delete value for

        Raises:
            StorageError: If delete operation fails
        """
        ...

    async def exists(self, key: "StateKey") -> bool:
        """
        Check if key exists.

        Args:
            key: State key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageError: If check fails
        """
        ...

    async def list_keys(self, prefix: "StateKey") -> AsyncIterator["StateKey"]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to list under

        Returns:
            AsyncIterator yielding matching keys

        Raises:
            StorageError: If listing fails
        """
        ...

    async def subscribe(
        self, key: "StateKey", callback: "AsyncStateCallbackFn"
    ) -> "AsyncSubscriptionProtocol":
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

    async def unsubscribe(self, subscription: "AsyncSubscriptionProtocol") -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...
