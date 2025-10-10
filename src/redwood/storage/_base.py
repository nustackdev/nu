from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from redwood.exceptions import StorageConnectionError, StorageOperationError

from ._snapshot import SnapshotContextManager
from ._transaction import TransactionContextManager


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.protocols import SnapshotProtocol, StorageCodecProtocol, TransactionProtocol
    from redwood.types import Key, StorageMode, Value


__all__ = [
    "BaseStorage",
    "is_valid_key",
]


class BaseStorage[EncodedKeyT, EncodedValueT](ABC):
    """Base class for storage implementations.

    Type Parameters:
        EncodedKeyT: Type of encoded keys (e.g., bytes, str)
        EncodedValueT: Type of encoded values (e.g., bytes, str)
    """

    codec: StorageCodecProtocol[EncodedKeyT, EncodedValueT]

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
    def _get_impl(self, key: Key) -> Value:
        """Implementation-specific get logic."""
        ...

    @final
    def get(self, key: Key) -> Value:
        """Get value by key."""
        self._ensure_connected()
        return self._get_impl(key)

    @abstractmethod
    def _set_impl(self, key: Key, value: Value) -> None:
        """Implementation-specific set logic."""
        ...

    @final
    def set(self, key: Key, value: Value) -> None:
        """Set value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        # Validate value type (?)
        # if not self._validate_value(value):
        #     raise StorageValidationError(f"Invalid value type: {type(value)}")
        self._set_impl(key, value)

    @abstractmethod
    def _delete_impl(self, key: Key) -> None:
        """Implementation-specific delete logic."""
        ...

    @final
    def delete(self, key: Key) -> None:
        """Delete value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        self._delete_impl(key)

    @abstractmethod
    def _exists_impl(self, key: Key) -> bool:
        """Implementation-specific exists logic."""
        ...

    @final
    def exists(self, key: Key) -> bool:
        """Check if key exists."""
        self._ensure_connected()
        return self._exists_impl(key)

    @abstractmethod
    def _list_keys_impl(self, prefix: Key, depth: int) -> Generator[Key, None]:
        """Implementation-specific list_keys logic."""
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true generator

    @final
    def list_keys(self, prefix: Key, depth: int = 1) -> Generator[Key, None]:
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
        yield from self._list_keys_impl(prefix, depth)

    @abstractmethod
    def _begin_transaction_impl(self) -> TransactionProtocol:
        """Implementation-specific transaction creation."""
        ...

    @final
    def begin_transaction(self) -> TransactionProtocol:
        """Begin a new transaction."""
        self._ensure_connected()
        try:
            return self._begin_transaction_impl()
        except Exception as e:
            raise StorageOperationError(f"Failed to begin transaction: {e}") from e

    @final
    def transaction(self) -> TransactionContextManager:
        """Create a transaction context manager.

        Returns:
            Context manager for handling transactions

        Example:
            with storage.transaction() as txn:
                txn.set(key, value)
                # Auto-commits if no exception
                # Auto-rollbacks if exception occurs
        """
        return TransactionContextManager(self)

    @abstractmethod
    def _begin_snapshot_impl(self) -> SnapshotProtocol:
        """Implementation-specific snapshot creation."""
        ...

    @final
    def begin_snapshot(self) -> SnapshotProtocol:
        """Begin a new snapshot."""
        self._ensure_connected()
        try:
            return self._begin_snapshot_impl()
        except Exception as e:
            raise StorageOperationError(f"Failed to begin snapshot: {e}") from e

    @final
    def snapshot(self) -> SnapshotContextManager:
        """Create a snapshot context manager.

        Returns:
            Context manager for handling snapshots

        Example:
            with storage.snapshot() as snap:
                value = snap.get(key)
                # Read-only operations
                # Auto-cleanup on exit
        """
        return SnapshotContextManager(self)
