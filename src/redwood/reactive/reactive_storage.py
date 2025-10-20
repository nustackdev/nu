"""This module includes an reactive kv storage solution.

Features:
- Persistent storage
- Change notifications
- Transactional operations
- Type safety
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import attrs

from redwood.backend import (
    ObserverProtocol,
    SnapshotContextManagerProtocol,
    SnapshotProtocol,
    StorageProtocol,
    SubscriptionProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)


if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType

    from redwood.abc import CallbackFn, TupleKey, Value

__all__ = [
    "ReactiveStorage",
    "ReactiveStorageSnapshot",
    "ReactiveStorageSnapshotContextManager",
    "ReactiveStorageTransaction",
    "ReactiveStorageTransactionContextManager",
]


class ReactiveStorage[EncodedKeyT, EncodedValueT]:
    """Key-value storage that combines persistent storage with change notifications."""

    _storage: StorageProtocol[EncodedKeyT, EncodedValueT]
    _observer: ObserverProtocol[EncodedKeyT]

    def __init__(
        self,
        storage: StorageProtocol[EncodedKeyT, EncodedValueT],
        observer: ObserverProtocol[EncodedKeyT],
    ) -> None:
        """Initialize ReactiveStorage with storage and observer.

        Args:
            storage: Storage ibackend
            observer: Observer backend
        """
        self._storage = storage
        self._observer = observer

    @property
    def storage(self) -> StorageProtocol[EncodedKeyT, EncodedValueT]:
        """Get storage backend.

        Returns:
            Storage instance
        """
        return self._storage

    @property
    def observer(self) -> ObserverProtocol[EncodedKeyT]:
        """Get observer backend.

        Returns:
            Observer instance
        """
        return self._observer

    def get(self, key: TupleKey) -> Value:
        """Get value at key.

        Args:
            key: Key to retrieve

        Returns:
            Value stored at key

        Raises:
            StorageOperationError: If retrieval fails
            StorageKeyError: If key not found
        """
        return self.storage.get(key)

    def set(self, key: TupleKey, value: Value) -> None:
        """Set value at key and notify observers.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If storage fails
            ObserverError: If notification fails
        """
        self.storage.set(key, value)
        self.observer.notify(key)

    def delete(self, key: TupleKey) -> None:
        """Delete value at key and notify observers.

        Args:
            key: Key to delete

        Raises:
            StorageOperationError: If deletion fails
            ObserverError: If notification fails
            StorageKeyError: If key not found
        """
        self.storage.delete(key)
        self.observer.notify(key)

    def exists(self, key: TupleKey) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageOperationError: If check fails
        """
        return self.storage.exists(key)

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        """List all keys under prefix.

        Args:
            prefix: Key prefix to filter results
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching keys

        Raises:
            StorageOperationError: If listing fails
        """
        yield from self.storage.list_keys(prefix, depth)

    def subscribe(
        self,
        key: TupleKey,
        callback: CallbackFn,
        depth: int = 0,
    ) -> SubscriptionProtocol:
        """Subscribe to changes under key prefix.

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

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self.observer.unsubscribe(subscription)

    def begin_transaction(self) -> ReactiveStorageTransaction:
        """Begin a new transaction that handles both storage and notifications.

        Returns:
            New transaction instance combining storage and notifications

        Raises:
            TransactionError: If transaction cannot be started
        """
        storage_txn = self.storage.begin_transaction()
        return ReactiveStorageTransaction(storage_txn=storage_txn, observer=self.observer)

    def transaction(self) -> ReactiveStorageTransactionContextManager:
        """Get transaction context manager for combined storage and notification handling.

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
        return ReactiveStorageTransactionContextManager(self)

    def begin_snapshot(self) -> ReactiveStorageSnapshot:
        """Begin a new read-only snapshot.

        Returns:
            New snapshot instance for read-only operations

        Raises:
            StorageError: If snapshot cannot be started
        """
        storage_snap = self.storage.begin_snapshot()
        return ReactiveStorageSnapshot(storage_snap=storage_snap)

    def snapshot(self) -> ReactiveStorageSnapshotContextManager:
        """Get snapshot context manager for read-only operations.

        Returns:
            Snapshot context manager for use in with statements

        Example:
            ```python
            with kv.snapshot() as snap:
                value = snap.get(key)
                # Read-only operations only
                # Auto-cleanup on exit
            ```
        """
        return ReactiveStorageSnapshotContextManager(self)

    def __hash__(self) -> int:
        return hash((self.storage, self.observer))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.storage == other.storage and self.observer == other.observer


@attrs.define(frozen=True)
class ReactiveStorageTransaction:
    """Transaction implementation that combines storage operations and notifications.

    Ensures atomicity between storage changes and observer notifications.
    """

    storage_txn: TransactionProtocol
    observer: ObserverProtocol
    # Track modified keys for notification after commit
    modified_keys: set[TupleKey] = attrs.field(factory=set)

    def get(self, key: TupleKey) -> Value:
        """Get value within transaction context."""
        return self.storage_txn.get(key)

    def set(self, key: TupleKey, value: Value) -> None:
        """Set value and track key for notification."""
        self.storage_txn.set(key, value)
        self.modified_keys.add(key)

    def delete(self, key: TupleKey) -> None:
        """Delete value and track key for notification."""
        self.storage_txn.delete(key)
        self.modified_keys.add(key)

    def exists(self, key: TupleKey) -> bool:
        """Check key existence within transaction."""
        return self.storage_txn.exists(key)

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        """List keys with prefix within transaction."""
        yield from self.storage_txn.list_keys(prefix, depth)

    def commit(self) -> None:
        """Commit transaction and notify observers of changes."""
        self.storage_txn.commit()
        # After successful storage commit, notify observers of all modified keys
        for key in self.modified_keys:
            self.observer.notify(key)

    def rollback(self) -> None:
        """Rollback transaction without notifications."""
        self.storage_txn.rollback()
        self.modified_keys.clear()

    def __hash__(self) -> int:
        return hash(self.storage_txn)

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self.storage_txn == other.storage_txn


@dataclass
class ReactiveStorageTransactionContextManager(TransactionContextManagerProtocol):
    """Context manager for State transactions that handles both storage and notifications."""

    _reactive_kv: ReactiveStorage  # Reference to parent State instance
    _transaction: ReactiveStorageTransaction | None = None  # Store the active transaction

    def __enter__(self) -> ReactiveStorageTransaction:
        """Begin new transaction with combined storage and notification handling."""
        self._transaction = self._reactive_kv.begin_transaction()
        return self._transaction

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Handle transaction completion.

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


@attrs.define(frozen=True)
class ReactiveStorageSnapshot:
    """Read-only snapshot implementation that provides consistent view of storage.

    No observer functionality needed since snapshots are read-only.
    """

    storage_snap: SnapshotProtocol

    def get(self, key: TupleKey) -> Value:
        """Get value within snapshot context."""
        return self.storage_snap.get(key)

    def exists(self, key: TupleKey) -> bool:
        """Check key existence within snapshot."""
        return self.storage_snap.exists(key)

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        """List keys with prefix within snapshot."""
        yield from self.storage_snap.list_keys(prefix, depth)

    def close(self) -> None:
        """Close snapshot and clean up resources."""
        self.storage_snap.close()

    def __hash__(self) -> int:
        return hash(self.storage_snap)

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self.storage_snap == other.storage_snap


@dataclass
class ReactiveStorageSnapshotContextManager(SnapshotContextManagerProtocol):
    """Context manager for read-only snapshots."""

    _reactive_kv: ReactiveStorage  # Reference to parent backend instance
    _snapshot: ReactiveStorageSnapshot | None = None  # Store the active snapshot

    def __enter__(self) -> ReactiveStorageSnapshot:
        """Begin new snapshot for read-only operations."""
        self._snapshot = self._reactive_kv.begin_snapshot()
        return self._snapshot

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Clean up snapshot resources."""
        if self._snapshot is None:
            raise RuntimeError("Snapshot not initialized")

        try:
            # Always clean up snapshot resources
            self._snapshot.close()
            return exc_type is None
        finally:
            # Clear the snapshot reference
            self._snapshot = None


if TYPE_CHECKING:
    __: type[TransactionProtocol] = ReactiveStorageTransaction
    ___: type[SnapshotProtocol] = ReactiveStorageSnapshot
