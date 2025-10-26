from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from mesh import SyncResource

from redwood.exceptions import StorageConnectionError, StorageOperationError

from ._snapshot import SnapshotContextManager
from ._transaction import TransactionContextManager


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import TupleKey, Value
    from redwood.backend import (
        CodecProtocol,
        SnapshotProtocol,
        StorageMode,
        StorageProtocol,
        TransactionProtocol,
    )


__all__ = [
    "BaseStorage",
]


class BaseStorage[EncodedKeyT, EncodedValueT](ABC, SyncResource):
    """Base class for storage implementations.

    Type Parameters:
        EncodedKeyT: Type of encoded keys (e.g., bytes, str)
        EncodedValueT: Type of encoded values (e.g., bytes, str)
    """

    codec: CodecProtocol[EncodedKeyT, EncodedValueT]

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
    def _get_impl(self, key: TupleKey) -> Value:
        """Implementation-specific get logic."""
        ...

    @final
    def get(self, key: TupleKey) -> Value:
        """Get value by key."""
        self._ensure_connected()
        return self._get_impl(key)

    @abstractmethod
    def _set_impl(self, key: TupleKey, value: Value) -> None:
        """Implementation-specific set logic."""
        ...

    @final
    def set(self, key: TupleKey, value: Value) -> None:
        """Set value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        # Validate value type (?)
        # if not self._validate_value(value):
        #     raise StorageValidationError(f"Invalid value type: {type(value)}")
        self._set_impl(key, value)

    @abstractmethod
    def _delete_impl(self, key: TupleKey) -> None:
        """Implementation-specific delete logic."""
        ...

    @final
    def delete(self, key: TupleKey) -> None:
        """Delete value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        self._delete_impl(key)

    @abstractmethod
    def _exists_impl(self, key: TupleKey) -> bool:
        """Implementation-specific exists logic."""
        ...

    @final
    def exists(self, key: TupleKey) -> bool:
        """Check if key exists."""
        self._ensure_connected()
        return self._exists_impl(key)

    @abstractmethod
    def _list_keys_impl(self, prefix: TupleKey, depth: int) -> Generator[TupleKey, None]:
        """Implementation-specific list_keys logic."""
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true generator

    @final
    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None]:
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

    def _list_items_impl(
        self,
        prefix: TupleKey,
        depth: int,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Default implementation for listing key/value pairs under prefix.

        Subclasses can override this method to provide more efficient
        iteration strategies without re-implementing the public API.
        """
        for key in self._list_keys_impl(prefix, depth):
            yield key, self._get_impl(key)

    def _list_values_impl(
        self,
        prefix: TupleKey,
        depth: int,
    ) -> Generator[Value, None, None]:
        """Default implementation for listing values under prefix."""
        for _, value in self._list_items_impl(prefix, depth):
            yield value

    @final
    def list_values(self, prefix: TupleKey, depth: int = 1) -> Generator[Value, None, None]:
        """List all values under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all values under prefix.

        Returns:
            Generator of matching values

        Raises:
            StorageOperationError: If list operation fails
        """
        self._ensure_connected()
        yield from self._list_values_impl(prefix, depth)

    @final
    def list_items(
        self,
        prefix: TupleKey,
        depth: int = 1,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """List key/value pairs under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all entries under prefix.

        Returns:
            Generator of matching key/value pairs

        Raises:
            StorageOperationError: If list operation fails
        """
        self._ensure_connected()
        yield from self._list_items_impl(prefix, depth)

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


if TYPE_CHECKING:
    _: type[StorageProtocol] = BaseStorage
