"""
This module includes an observable kv storage solution with:
- Persistent storage
- Change notifications
- Transactional operations
- Type safety
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, AsyncGenerator

from loomistd.kv_storage import (
    StorageProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)
from loomistd.observer import ObserverProtocol, SubscriptionProtocol

from ._types import StateCallbackFn, StateKey, StateValue

__all__ = [
    "ObservableKVStorageCore",
    "ObservableKVTransaction",
    "ObservableKVTransactionContextManager",
]


class ObservableKVStorageCore:
    _storage: StorageProtocol[StateKey, StateValue, Any, Any]
    _observer: ObserverProtocol[StateKey, Any]

    def __init__(
        self,
        storage: StorageProtocol[StateKey, StateValue, Any, Any],
        observer: ObserverProtocol[StateKey, Any],
    ) -> None:
        """
        Initialize ObservableKVStorage with storage and observer.

        Args:
            storage: Storage backend
            observer: Observer backend
        """
        self._storage = storage
        self._observer = observer

    @property
    def storage(self) -> StorageProtocol[StateKey, StateValue, Any, Any]:
        """
        Get storage backend.

        Returns:
            Storage instance
        """
        return self._storage

    @property
    def observer(self) -> ObserverProtocol[StateKey, Any]:
        """
        Get observer backend.

        Returns:
            Observer instance
        """
        return self._observer

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
        return await self.storage.get(key)

    async def set(self, key: StateKey, value: StateValue) -> None:
        """
        Set value at key and notify observers.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If storage fails
            ObserverError: If notification fails
        """
        await self.storage.set(key, value)
        await self.observer.notify(key)

    async def delete(self, key: StateKey) -> None:
        """
        Delete value at key and notify observers.

        Args:
            key: Key to delete

        Raises:
            StorageOperationError: If deletion fails
            ObserverError: If notification fails
            StorageKeyError: If key not found
        """
        await self.storage.delete(key)
        await self.observer.notify(key)

    async def exists(self, key: StateKey) -> bool:
        """
        Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageOperationError: If check fails
        """
        return await self.storage.exists(key)

    async def list_keys(self, prefix: StateKey, depth: int = 1) -> AsyncGenerator[StateKey, None]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to filter results
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            AsyncGenerator of matching keys

        Raises:
            StorageOperationError: If listing fails
        """
        async for key in self.storage.list_keys(prefix, depth):
            yield key

    async def subscribe(
        self,
        key: StateKey,
        callback: StateCallbackFn,
        depth: int = 0,
    ) -> SubscriptionProtocol[StateKey]:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Async callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.


        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        return await self.observer.subscribe(key, callback, depth)

    async def unsubscribe(self, subscription: SubscriptionProtocol[StateKey]) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        await self.observer.unsubscribe(subscription)

    async def begin_transaction(self) -> ObservableKVTransaction:
        """
        Begin a new transaction that handles both storage and notifications.

        Returns:
            New transaction instance combining storage and notifications

        Raises:
            TransactionError: If transaction cannot be started
        """
        storage_txn = await self.storage.begin_transaction()
        return ObservableKVTransaction(storage_txn=storage_txn, observer=self.observer)

    async def transaction(self) -> ObservableKVTransactionContextManager:
        """
        Get transaction context manager for combined storage and notification handling.

        Returns:
            Transaction context manager for use in async with statements

        Example:
            ```python
            async with kv.transaction() as txn:
                await txn.set(key1, value1)
                await txn.set(key2, value2)
                # Auto-commits and notifies on success
                # Auto-rollbacks with no notifications on failure
            ```
        """
        return ObservableKVTransactionContextManager(self)


@dataclass
class ObservableKVTransaction(TransactionProtocol[StateKey, StateValue]):
    """
    Transaction implementation that combines storage operations and notifications.
    Ensures atomicity between storage changes and observer notifications.
    """

    storage_txn: TransactionProtocol[StateKey, StateValue]
    observer: ObserverProtocol[StateKey, Any]
    # Track modified keys for notification after commit
    modified_keys: set[StateKey] = field(default_factory=set)

    async def get(self, key: StateKey) -> StateValue:
        """Get value within transaction context"""
        return await self.storage_txn.get(key)

    async def set(self, key: StateKey, value: StateValue) -> None:
        """Set value and track key for notification"""
        await self.storage_txn.set(key, value)
        self.modified_keys.add(key)

    async def delete(self, key: StateKey) -> None:
        """Delete value and track key for notification"""
        await self.storage_txn.delete(key)
        self.modified_keys.add(key)

    async def exists(self, key: StateKey) -> bool:
        """Check key existence within transaction"""
        return await self.storage_txn.exists(key)

    async def list_keys(self, prefix: StateKey, depth: int = 1) -> AsyncGenerator[StateKey, None]:
        """List keys with prefix within transaction"""
        async for key in self.storage_txn.list_keys(prefix, depth):
            yield key

    async def commit(self) -> None:
        """Commit transaction and notify observers of changes"""
        await self.storage_txn.commit()
        # After successful storage commit, notify observers of all modified keys
        for key in self.modified_keys:
            await self.observer.notify(key)

    async def rollback(self) -> None:
        """Rollback transaction without notifications"""
        await self.storage_txn.rollback()
        self.modified_keys.clear()


@dataclass
class ObservableKVTransactionContextManager(
    TransactionContextManagerProtocol[StateKey, StateValue]
):
    """
    Context manager for State transactions that handles both storage and notifications.
    """

    _observable_kv: ObservableKVStorageCore  # Reference to parent State instance
    _transaction: ObservableKVTransaction | None = None  # Store the active transaction

    async def __aenter__(self) -> ObservableKVTransaction:
        """Begin new transaction with combined storage and notification handling"""
        self._transaction = await self._observable_kv.begin_transaction()
        return self._transaction

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """
        Handle transaction completion:
        - On success (no exception): commit changes and send notifications
        - On failure (exception): rollback changes, no notifications
        """
        if self._transaction is None:
            raise RuntimeError("Transaction not initialized")

        try:
            if exc_type is not None:
                # Exception occurred, rollback
                await self._transaction.rollback()
                return False
            # No exception, commit
            await self._transaction.commit()
            return True
        finally:
            # Clear the transaction reference
            self._transaction = None
