from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Generic, TypeGuard, final

from loomi.tree import SnapshotProtocol, TransactionProtocol
from loomistd.codec import CodecProtocol

from ._exceptions import StorageConnectionError, StorageOperationError, StorageValidationError
from ._snapshot import SnapshotContextManager
from ._transaction import TransactionContextManager
from ._types import StorageEncodedKeyT, StorageEncodedValueT, StorageKeyT, StorageMode, ValueT


__all__ = [
    "BaseStorage",
    "is_valid_key",
]


class BaseStorage(ABC, Generic[StorageKeyT, ValueT, StorageEncodedKeyT, StorageEncodedValueT]):
    """Base class for storage implementations.

    Type Parameters:
        ValueT: Type of values supported by this storage
    """

    codec: CodecProtocol[StorageKeyT, ValueT, StorageEncodedKeyT, StorageEncodedValueT]

    @property
    def mode(self) -> StorageMode:
        """Get storage mode."""
        return self.spec.mode  # type: ignore

    def setup(self) -> None:
        self._connected = False
        self.connect()

    def cleanup(self) -> None:
        self.disconnect()

    def _ensure_connected(self) -> None:
        """Verify connection state."""
        if not self._connected:
            raise StorageConnectionError("Storage is not connected")

    def _validate_key(self, key: StorageKeyT) -> None:
        """Validate key format."""
        if not is_valid_key(key):
            raise StorageValidationError(f"Invalid key format: {key}")

    # Connection Management
    @abstractmethod
    def _connect_impl(self) -> None:
        """Implementation-specific connect logic."""
        ...

    @final
    def connect(self) -> None:
        """Connect to storage backend."""
        if self._connected:
            return
        try:
            self._connect_impl()
            self._connected = True
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect: {e}") from e

    @abstractmethod
    def _disconnect_impl(self) -> None:
        """Implementation-specific disconnect logic."""
        ...

    @final
    def disconnect(self) -> None:
        """Disconnect from storage backend."""
        if not self._connected:
            return
        try:
            self._disconnect_impl()
        finally:
            self._connected = False

    # Core Operations
    @abstractmethod
    def _get_impl(self, key: StorageKeyT) -> ValueT:
        """Implementation-specific get logic."""
        ...

    @final
    def get(self, key: StorageKeyT) -> ValueT:
        """Get value by key."""
        self._ensure_connected()
        return self._get_impl(key)

    @abstractmethod
    def _set_impl(self, key: StorageKeyT, value: ValueT) -> None:
        """Implementation-specific set logic."""
        ...

    @final
    def set(self, key: StorageKeyT, value: ValueT) -> None:
        """Set value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        self._validate_key(key)
        # Validate value type (?)
        # if not self._validate_value(value):
        #     raise StorageValidationError(f"Invalid value type: {type(value)}")
        self._set_impl(key, value)

    @abstractmethod
    def _delete_impl(self, key: StorageKeyT) -> None:
        """Implementation-specific delete logic."""
        ...

    @final
    def delete(self, key: StorageKeyT) -> None:
        """Delete value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        self._validate_key(key)
        self._delete_impl(key)

    @abstractmethod
    def _exists_impl(self, key: StorageKeyT) -> bool:
        """Implementation-specific exists logic."""
        ...

    @final
    def exists(self, key: StorageKeyT) -> bool:
        """Check if key exists."""
        self._ensure_connected()
        return self._exists_impl(key)

    @abstractmethod
    def _list_keys_impl(self, prefix: StorageKeyT, depth: int) -> Generator[StorageKeyT, None]:
        """Implementation-specific list_keys logic."""
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true generator

    @final
    def list_keys(self, prefix: StorageKeyT, depth: int = 1) -> Generator[StorageKeyT, None]:
        """List all keys under prefix within transaction context.

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
        self._ensure_connected()
        for key in self._list_keys_impl(prefix, depth):
            yield key

    @abstractmethod
    def _begin_transaction_impl(self) -> TransactionProtocol[ValueT]:
        """Implementation-specific transaction creation."""
        ...

    @final
    def begin_transaction(self) -> TransactionProtocol[ValueT]:
        """Begin a new transaction."""
        self._ensure_connected()
        try:
            return self._begin_transaction_impl()
        except Exception as e:
            raise StorageOperationError(f"Failed to begin transaction: {e}") from e

    @final
    def transaction(self) -> TransactionContextManager[ValueT]:
        """Create a transaction context manager.

        Returns:
            Context manager for handling transactions

        Example:
            with storage.transaction() as txn:
                txn.set(key, value)
                # Auto-commits if no exception
                # Auto-rollbacks if exception occurs
        """
        return TransactionContextManager[ValueT](self)

    @abstractmethod
    def _begin_snapshot_impl(self) -> SnapshotProtocol[ValueT]:
        """Implementation-specific snapshot creation."""
        ...

    @final
    def begin_snapshot(self) -> SnapshotProtocol[ValueT]:
        """Begin a new snapshot."""
        self._ensure_connected()
        try:
            return self._begin_snapshot_impl()
        except Exception as e:
            raise StorageOperationError(f"Failed to begin snapshot: {e}") from e

    @final
    def snapshot(self) -> SnapshotContextManager[ValueT]:
        """Create a snapshot context manager.

        Returns:
            Context manager for handling snapshots

        Example:
            with storage.snapshot() as snap:
                value = snap.get(key)
                # Read-only operations
                # Auto-cleanup on exit
        """
        return SnapshotContextManager[ValueT](self)


def is_valid_key(value: StorageKeyT) -> TypeGuard[StorageKeyT]:
    """Type guard to verify if a value is a valid key.

    Args:
        value: Value to check

    Returns:
        True if value is a valid key (tuple of strings)
    """
    return isinstance(value, tuple) and all(
        isinstance(part, str) and len(part.strip()) for part in value
    )
