from __future__ import annotations

from types import TracebackType
from typing import AsyncGenerator, Protocol, runtime_checkable

from loomistd.codec import CodecProtocol

from ._types import StorageEncodedKeyT, StorageEncodedValueT, StorageKeyT, StorageValueT

__all__ = [
    "KVOperationsProtocol",
    "StorageProtocol",
    "TransactionProtocol",
    "TransactionContextManagerProtocol",
    "TransactionalHandlerProtocol",
]


class KVOperationsProtocol(Protocol[StorageKeyT, StorageValueT]):
    async def get(self, key: StorageKeyT) -> StorageValueT:
        """
        Retrieve value by key.

        This method must:
        - Validate key format
        - Handle missing keys
        - Decode stored data

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            StorageConnectionError: If not connected
            StorageKeyError: If key format invalid
            StorageOperationError: If operation fails
        """
        ...

    async def set(self, key: StorageKeyT, value: StorageValueT) -> None:
        """
        Set value for key.

        This method must:
        - Validate key and value
        - Encode data for storage
        - Handle concurrent access

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If operation fails
            ValueError: If value type invalid
        """
        ...

    async def delete(self, key: StorageKeyT) -> None:
        """
        Delete value by key.

        This method must:
        - Validate key format
        - Handle missing keys
        - Handle concurrent access

        Args:
            key: Key to delete

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If operation fails
        """
        ...

    async def exists(self, key: StorageKeyT) -> bool:
        """
        Check if key exists.

        This method must:
        - Validate key format
        - Handle concurrent access

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If check fails
        """
        ...

    async def list_keys(
        self, prefix: StorageKeyT, depth: int = ...
    ) -> AsyncGenerator[StorageKeyT, None]:
        """
        List all keys under prefix.

        This method must:
        - Validate prefix format
        - Handle recursion
        - Support efficient iteration

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            AsyncGenerator of matching keys

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If operation fails
        """
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true async generator

    async def begin_transaction(self) -> TransactionProtocol[StorageKeyT, StorageValueT]:
        """
        Begin a new transaction.

        This method must:
        - Create isolated transaction scope
        - Initialize tracking structures
        - Handle nested transactions

        Returns:
            New transaction instance

        Raises:
            StorageConnectionError: If not connected
            StorageError: If transaction start fails
        """
        ...

    async def transaction(self) -> TransactionContextManagerProtocol[StorageKeyT, StorageValueT]:
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
        ...


class StorageProtocol(
    KVOperationsProtocol[StorageKeyT, StorageValueT],
    Protocol[StorageKeyT, StorageValueT, StorageEncodedKeyT, StorageEncodedValueT],
):
    """
    Protocol defining state storage operations.

    Storage implementations handle the persistence of state data with:
    - Transactional guarantees
    - Proper error handling
    - Resource management
    - Type safety

    Type Parameters:
        KeyT: Key type (must be tuple of strings)
        ValueT: Value type (must be valid state value)
        EncodedKeyT: Encoded key type for storage
        EncodedValueT: Encoded value type for storage

    Implementation Requirements:
        - Must maintain ACID guarantees
        - Must handle concurrent access
        - Must validate all inputs
        - Must properly encode/decode data
    """

    @property
    def codec(
        self,
    ) -> CodecProtocol[StorageKeyT, StorageValueT, StorageEncodedKeyT, StorageEncodedValueT]:
        """
        Get codec for encoding/decoding keys and values.

        Returns:
            Codec instance
        """
        ...

    async def connect(self) -> None:
        """
        Establish connection to storage backend.

        This method must:
        - Initialize resources
        - Verify backend health
        - Set up any required structures

        Raises:
            StorageConnectionError: If connection fails
        """
        ...

    async def disconnect(self) -> None:
        """
        Close connection to storage backend.

        This method must:
        - Clean up resources
        - Flush pending changes
        - Handle existing transactions

        Raises:
            StorageConnectionError: If disconnection fails
        """
        ...


@runtime_checkable
class TransactionProtocol(Protocol[StorageKeyT, StorageValueT]):
    """Protocol defining the interface for transactions."""

    async def get(self, key: StorageKeyT) -> StorageValueT:
        """
        Retrieve value by key.

        This method must:
        - Validate key format
        - Handle missing keys
        - Decode stored data

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            StorageConnectionError: If not connected
            StorageKeyError: If key format invalid
            StorageOperationError: If operation fails
        """
        ...

    async def set(self, key: StorageKeyT, value: StorageValueT) -> None:
        """
        Set value for key.

        This method must:
        - Validate key and value
        - Encode data for storage
        - Handle concurrent access

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If operation fails
            ValueError: If value type invalid
        """
        ...

    async def delete(self, key: StorageKeyT) -> None:
        """
        Delete value by key.

        This method must:
        - Validate key format
        - Handle missing keys
        - Handle concurrent access

        Args:
            key: Key to delete

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If operation fails
        """
        ...

    async def exists(self, key: StorageKeyT) -> bool:
        """
        Check if key exists.

        This method must:
        - Validate key format
        - Handle concurrent access

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If check fails
        """
        ...

    async def list_keys(
        self, prefix: StorageKeyT, depth: int = ...
    ) -> AsyncGenerator[StorageKeyT, None]:
        """
        List all keys under prefix.

        This method must:
        - Validate prefix format
        - Handle recursion
        - Support efficient iteration

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            AsyncGenerator of matching keys

        Raises:
            StorageConnectionError: If not connected
            StorageOperationError: If operation fails
        """
        if False:  # This will never execute but helps type checkers
            yield prefix  # Dummy yield to make it a true async generator

    async def commit(self) -> None:
        """
        Commit all changes in the transaction.

        Raises:
            TransactionError: If commit fails or transaction is invalid
            StorageOperationError: If storage operations fail during commit
        """
        ...

    async def rollback(self) -> None:
        """
        Roll back all changes in the transaction.

        Raises:
            TransactionError: If rollback fails or transaction is invalid
        """
        ...


class TransactionContextManagerProtocol(Protocol[StorageKeyT, StorageValueT]):
    """Async context manager for storage transactions."""

    def __init__(self, handler: TransactionalHandlerProtocol[StorageKeyT, StorageValueT]):
        """
        Initialize transaction context manager.

        Args:
            storage: Storage instance to manage transactions for
        """
        ...

    async def __aenter__(self) -> TransactionProtocol[StorageKeyT, StorageValueT]:
        """
        Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Commit or rollback transaction based on context exit.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type if an error occurred.
            exc_val (Optional[BaseException]): Exception value if an error occurred.
            exc_tb (Optional[TracebackType]): Exception traceback if an error occurred.

        Returns:
            None
        """
        ...


class TransactionalHandlerProtocol(Protocol[StorageKeyT, StorageValueT]):
    """Protocol defining the interface for transactionable storage."""

    async def begin_transaction(self) -> TransactionProtocol[StorageKeyT, StorageValueT]:
        """Begin a new transaction."""
        ...

    async def transaction(self) -> TransactionContextManagerProtocol[StorageKeyT, StorageValueT]:
        """Get a typed transaction context manager."""
        ...
