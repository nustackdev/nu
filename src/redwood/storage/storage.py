"""This module includes an reactive kv storage solution.

Features:
- Persistent storage
- Change notifications
- Transactional operations
- Type safety
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from .utils import SnapshotContextManager, TransactionContextManager


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import CallbackFn, TupleKey, Value
    from redwood.be import (
        CodecProtocol,
        ObserverProtocol,
        SnapshotContextManagerProtocol,
        SnapshotProtocol,
        StorageDescriptor,
        StorageProtocol,
        StorageScanOptions,
        SubscriptionProtocol,
        TransactionContextManagerProtocol,
        TransactionProtocol,
    )


__all__ = [
    "ReactiveStorage",
    "ReactiveStorageSnapshot",
    "ReactiveStorageTransaction",
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
    def codec(self) -> CodecProtocol[EncodedKeyT, EncodedValueT]:
        """Get storage codec.

        Returns:
            Storage codec
        """
        return self.storage.codec

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

    def describe(self) -> StorageDescriptor:
        """Get storage descriptor.

        Returns:
            Storage descriptor
        """
        return self.storage.describe()

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

    def list_values(self, prefix: TupleKey, depth: int = 1) -> Generator[Value, None, None]:
        """List all values under prefix."""
        yield from self.storage.list_values(prefix, depth)

    def list_items(
        self,
        prefix: TupleKey,
        depth: int = 1,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """List key/value pairs under prefix."""
        yield from self.storage.list_items(prefix, depth)

    def scan_keys(self, options: StorageScanOptions, /) -> Generator[TupleKey, None, None]:
        """Scan keys using configured options."""
        yield from self.storage.scan_keys(options)

    def scan_items(
        self,
        options: StorageScanOptions,
        /,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Scan key/value pairs using configured options."""
        yield from self.storage.scan_items(options)

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

    def transaction(self) -> TransactionContextManagerProtocol:
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
        return TransactionContextManager(self)

    def begin_snapshot(self) -> ReactiveStorageSnapshot:
        """Begin a new read-only snapshot.

        Returns:
            New snapshot instance for read-only operations

        Raises:
            StorageError: If snapshot cannot be started
        """
        storage_snap = self.storage.begin_snapshot()
        return ReactiveStorageSnapshot(storage_snap=storage_snap)

    def snapshot(self) -> SnapshotContextManagerProtocol:
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
        return SnapshotContextManager(self)

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

    def list_values(self, prefix: TupleKey, depth: int = 1) -> Generator[Value, None, None]:
        """List values with prefix within transaction."""
        yield from self.storage_txn.list_values(prefix, depth)

    def list_items(
        self,
        prefix: TupleKey,
        depth: int = 1,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """List key/value pairs with prefix within transaction."""
        yield from self.storage_txn.list_items(prefix, depth)

    def scan_keys(self, options: StorageScanOptions, /) -> Generator[TupleKey, None, None]:
        """Scan keys within transaction."""
        yield from self.storage_txn.scan_keys(options)

    def scan_items(
        self,
        options: StorageScanOptions,
        /,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Scan key/value pairs within transaction."""
        yield from self.storage_txn.scan_items(options)

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

    def list_values(self, prefix: TupleKey, depth: int = 1) -> Generator[Value, None, None]:
        """List values with prefix within snapshot."""
        yield from self.storage_snap.list_values(prefix, depth)

    def list_items(
        self,
        prefix: TupleKey,
        depth: int = 1,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """List key/value pairs with prefix within snapshot."""
        yield from self.storage_snap.list_items(prefix, depth)

    def scan_keys(self, options: StorageScanOptions, /) -> Generator[TupleKey, None, None]:
        """Scan keys within snapshot."""
        yield from self.storage_snap.scan_keys(options)

    def scan_items(
        self,
        options: StorageScanOptions,
        /,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Scan key/value pairs within snapshot."""
        yield from self.storage_snap.scan_items(options)

    def close(self) -> None:
        """Close snapshot and clean up resources."""
        self.storage_snap.close()

    def __hash__(self) -> int:
        return hash(self.storage_snap)

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self.storage_snap == other.storage_snap


if TYPE_CHECKING:
    _: type[StorageProtocol] = ReactiveStorage
    __: type[TransactionProtocol] = ReactiveStorageTransaction
    ___: type[SnapshotProtocol] = ReactiveStorageSnapshot
