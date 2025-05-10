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
from typing import TYPE_CHECKING, Any, Generator

from loomi.interfaces.state.kv import (
    SyncObservableStorageProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from loomi.interfaces.state.observer import SyncSubscriptionProtocol
from loomistd.kv import StorageServiceProtocol
from loomistd.observer import ObserverServiceProtocol

from ._types import StateCallbackFn, StateKey, StateValue

__all__ = [
    "ObservableKVStorageCore",
    "ObservableKVTransaction",
    "ObservableKVTransactionContextManager",
]


class ObservableKVStorageCore:
    _storage: StorageServiceProtocol[StateKey, StateValue, Any, Any]
    _observer: ObserverServiceProtocol[StateKey, Any]

    def __init__(
        self,
        storage: StorageServiceProtocol[StateKey, StateValue, Any, Any],
        observer: ObserverServiceProtocol[StateKey, Any],
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
    def storage(self) -> StorageServiceProtocol[StateKey, StateValue, Any, Any]:
        """
        Get storage backend.

        Returns:
            Storage instance
        """
        return self._storage

    @property
    def observer(self) -> ObserverServiceProtocol[StateKey, Any]:
        """
        Get observer backend.

        Returns:
            Observer instance
        """
        return self._observer

    def get(self, key: StateKey) -> StateValue:
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
        return self.storage.get(key)

    def set(self, key: StateKey, value: StateValue) -> None:
        """
        Set value at key and notify observers.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If storage fails
            ObserverError: If notification fails
        """
        self.storage.set(key, value)
        self.observer.notify(key)

    def delete(self, key: StateKey) -> None:
        """
        Delete value at key and notify observers.

        Args:
            key: Key to delete

        Raises:
            StorageOperationError: If deletion fails
            ObserverError: If notification fails
            StorageKeyError: If key not found
        """
        self.storage.delete(key)
        self.observer.notify(key)

    def exists(self, key: StateKey) -> bool:
        """
        Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageOperationError: If check fails
        """
        return self.storage.exists(key)

    def list_keys(self, prefix: StateKey, depth: int = 1) -> Generator[StateKey, None, None]:
        """
        List all keys under prefix.

        Args:
            prefix: Key prefix to filter results
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching keys

        Raises:
            StorageOperationError: If listing fails
        """
        for key in self.storage.list_keys(prefix, depth):
            yield key

    def subscribe(
        self,
        key: StateKey,
        callback: StateCallbackFn,
        depth: int = 0,
    ) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Sync callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.


        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        return self.observer.subscribe(key, callback, depth)

    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self.observer.unsubscribe(subscription)

    def begin_transaction(self) -> ObservableKVTransaction:
        """
        Begin a new transaction that handles both storage and notifications.

        Returns:
            New transaction instance combining storage and notifications

        Raises:
            TransactionError: If transaction cannot be started
        """
        storage_txn = self.storage.begin_transaction()
        return ObservableKVTransaction(storage_txn=storage_txn, observer=self.observer)

    def transaction(self) -> ObservableKVTransactionContextManager:
        """
        Get transaction context manager for combined storage and notification handling.

        Returns:
            Transaction context manager for use in with statements

        Example:
            ```python
            with kv.transaction() as txn:
                txn.set(key1, value1)
                txn.set(key2, value2)
                # Auto-commits and notifies on success
                # Auto-rollbacks with no notifications on failure
            ```
        """
        return ObservableKVTransactionContextManager(self)


@dataclass
class ObservableKVTransaction(SyncTransactionProtocol[StateValue]):
    """
    Transaction implementation that combines storage operations and notifications.
    Ensures atomicity between storage changes and observer notifications.
    """

    storage_txn: SyncTransactionProtocol[StateValue]
    observer: ObserverServiceProtocol[StateKey, Any]
    # Track modified keys for notification after commit
    modified_keys: set[StateKey] = field(default_factory=set)

    def get(self, key: StateKey) -> StateValue:
        """Get value within transaction context"""
        return self.storage_txn.get(key)

    def set(self, key: StateKey, value: StateValue) -> None:
        """Set value and track key for notification"""
        self.storage_txn.set(key, value)
        self.modified_keys.add(key)

    def delete(self, key: StateKey) -> None:
        """Delete value and track key for notification"""
        self.storage_txn.delete(key)
        self.modified_keys.add(key)

    def exists(self, key: StateKey) -> bool:
        """Check key existence within transaction"""
        return self.storage_txn.exists(key)

    def list_keys(self, prefix: StateKey, depth: int = 1) -> Generator[StateKey, None, None]:
        """List keys with prefix within transaction"""
        for key in self.storage_txn.list_keys(prefix, depth):
            yield key

    def commit(self) -> None:
        """Commit transaction and notify observers of changes"""
        self.storage_txn.commit()
        # After successful storage commit, notify observers of all modified keys
        for key in self.modified_keys:
            self.observer.notify(key)

    def rollback(self) -> None:
        """Rollback transaction without notifications"""
        self.storage_txn.rollback()
        self.modified_keys.clear()


@dataclass
class ObservableKVTransactionContextManager(SyncTransactionContextManagerProtocol[StateValue]):
    """
    Context manager for State transactions that handles both storage and notifications.
    """

    _observable_kv: ObservableKVStorageCore  # Reference to parent State instance
    _transaction: ObservableKVTransaction | None = None  # Store the active transaction

    def __enter__(self) -> ObservableKVTransaction:
        """Begin new transaction with combined storage and notification handling"""
        self._transaction = self._observable_kv.begin_transaction()
        return self._transaction

    def __exit__(
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
                self._transaction.rollback()
                return False
            # No exception, commit
            self._transaction.commit()
            return True
        finally:
            # Clear the transaction reference
            self._transaction = None


if TYPE_CHECKING:
    _: type[SyncObservableStorageProtocol] = ObservableKVStorageCore
