from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generic, TypeGuard, final

from pydantic import Field

from loomi.interfaces.state.kv import AsyncTransactionProtocol
from loomi.spec import Spec
from loomistd.codec import CodecProtocol

from ._exceptions import StorageConnectionError, StorageOperationError, StorageValidationError
from ._transaction import TransactionContextManager
from ._types import (
    StorageEncodedKeyT,
    StorageEncodedValueT,
    StorageKeyT,
    StorageMode,
    StorageValueT,
)

__all__ = [
    "BaseStorage",
    "BaseStorageSpec",
    "is_valid_key",
]


class BaseStorageSpec(Spec):
    """Base storage spec."""

    codec: Spec
    mode: StorageMode = Field(default="write")


class BaseStorage(
    ABC, Generic[StorageKeyT, StorageValueT, StorageEncodedKeyT, StorageEncodedValueT]
):
    """
    Base class for storage implementations.

    Type Parameters:
        ValueT: Type of values supported by this storage
    """

    _codec: CodecProtocol[StorageKeyT, StorageValueT, StorageEncodedKeyT, StorageEncodedValueT]

    @property
    def codec(
        self,
    ) -> CodecProtocol[StorageKeyT, StorageValueT, StorageEncodedKeyT, StorageEncodedValueT]:
        """
        Get codec for encoding/decoding keys and values.

        Returns:
            Codec instance
        """
        return self._codec

    @property
    def mode(self) -> StorageMode:
        """Get storage mode."""
        return self.spec.mode  # type: ignore

    async def setup(self) -> None:
        self._connected = False
        await self.connect()

    async def cleanup(self) -> None:
        await self.disconnect()

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
    async def _connect_impl(self) -> None:
        """Implementation-specific connect logic."""
        ...

    @final
    async def connect(self) -> None:
        """Connect to storage backend."""
        if self._connected:
            return
        try:
            await self._connect_impl()
            self._connected = True
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect: {e}") from e

    @abstractmethod
    async def _disconnect_impl(self) -> None:
        """Implementation-specific disconnect logic."""
        ...

    @final
    async def disconnect(self) -> None:
        """Disconnect from storage backend."""
        if not self._connected:
            return
        try:
            await self._disconnect_impl()
        finally:
            self._connected = False

    # Core Operations
    @abstractmethod
    async def _get_impl(self, key: StorageKeyT) -> StorageValueT:
        """Implementation-specific get logic."""
        ...

    @final
    async def get(self, key: StorageKeyT) -> StorageValueT:
        """Get value by key."""
        self._ensure_connected()
        return await self._get_impl(key)

    @abstractmethod
    async def _set_impl(self, key: StorageKeyT, value: StorageValueT) -> None:
        """Implementation-specific set logic."""
        ...

    @final
    async def set(self, key: StorageKeyT, value: StorageValueT) -> None:
        """Set value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        self._validate_key(key)
        # Validate value type (?)
        # if not self._validate_value(value):
        #     raise StorageValidationError(f"Invalid value type: {type(value)}")
        await self._set_impl(key, value)

    @abstractmethod
    async def _delete_impl(self, key: StorageKeyT) -> None:
        """Implementation-specific delete logic."""
        ...

    @final
    async def delete(self, key: StorageKeyT) -> None:
        """Delete value by key."""
        if self.mode != "write":
            raise StorageOperationError("Cannot set value in read-only mode")

        self._ensure_connected()
        self._validate_key(key)
        await self._delete_impl(key)

    @abstractmethod
    async def _exists_impl(self, key: StorageKeyT) -> bool:
        """Implementation-specific exists logic."""
        ...

    @final
    async def exists(self, key: StorageKeyT) -> bool:
        """Check if key exists."""
        self._ensure_connected()
        return await self._exists_impl(key)

    @abstractmethod
    async def _list_keys_impl(
        self, prefix: StorageKeyT, depth: int
    ) -> AsyncGenerator[StorageKeyT, None]:
        """Implementation-specific list_keys logic."""
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true async generator

    @final
    async def list_keys(
        self, prefix: StorageKeyT, depth: int = 1
    ) -> AsyncGenerator[StorageKeyT, None]:
        """
        List all keys under prefix within transaction context.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            AsyncGenerator of matching keys

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If list operation fails
        """
        self._ensure_connected()
        async for key in self._list_keys_impl(prefix, depth):
            yield key

    @abstractmethod
    async def _begin_transaction_impl(self) -> AsyncTransactionProtocol[StorageValueT]:
        """Implementation-specific transaction creation."""
        ...

    @final
    async def begin_transaction(self) -> AsyncTransactionProtocol[StorageValueT]:
        """Begin a new transaction."""
        self._ensure_connected()
        try:
            return await self._begin_transaction_impl()
        except Exception as e:
            raise StorageOperationError(f"Failed to begin transaction: {e}") from e

    @final
    async def transaction(self) -> TransactionContextManager[StorageValueT]:
        """
        Create a transaction context manager.

        Returns:
            Context manager for handling transactions

        Example:
            async with storage.transaction() as txn:
                await txn.set(key, value)
                # Auto-commits if no exception
                # Auto-rollbacks if exception occurs
        """
        return TransactionContextManager[StorageValueT](self)


def is_valid_key(value: StorageKeyT) -> TypeGuard[StorageKeyT]:
    """
    Type guard to verify if a value is a valid key.

    Args:
        value: Value to check

    Returns:
        True if value is a valid key (tuple of strings)
    """
    return isinstance(value, tuple) and all(
        isinstance(part, str) and len(part.strip()) for part in value
    )
