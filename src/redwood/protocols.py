from __future__ import annotations

from collections.abc import Generator
from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from .types import (
    CallbackFn,
    EncodedKeyT,
    EncodedValueT,
    Key,
    Value,
)


__all__ = []


class StorageCodecProtocol(Protocol[EncodedKeyT, EncodedValueT]):
    """Protocol for complete storage encoding/decoding.

    Combines key and value codec operations into a unified interface
    for storage engines that need to encode both keys and values.

    Type Parameters:
        KeyT: The type of keys (contravariant)
        EncodedKeyT: The type of encoded keys (covariant)
        ValueT: The type of values (contravariant)
        EncodedValueT: The type of encoded values (covariant)
    """

    def encode_key(self, key: Key) -> EncodedKeyT:
        """Encode a key for storage.

        Args:
            key: The key to encode

        Returns:
            Encoded key

        Raises:
            EncodeError: If encoding fails
        """
        ...

    def decode_key(self, encoded: EncodedKeyT) -> Key:
        """Decode a key from storage.

        Args:
            encoded: Encoded key to decode

        Returns:
            Decoded key

        Raises:
            DecodeError: If decoding fails
        """
        ...

    def encode_value(self, value: Value) -> EncodedValueT:
        """Encode a value for storage.

        Args:
            value: The value to encode

        Returns:
            Encoded value

        Raises:
            EncodeError: If encoding fails
        """
        ...

    def decode_value(self, encoded: EncodedValueT) -> Value:
        """Decode a value from storage.

        Args:
            encoded: Encoded value to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If decoding fails
        """
        ...


class KeyCodecProtocol(Protocol[EncodedKeyT]):
    """Protocol for encoding/decoding storage keys.

    Type Parameters:
        KeyT: The type of keys that can be encoded (contravariant)
        EncodedKeyT: The type of encoded keys (covariant)

    Keys typically require lexicographic ordering preservation for
    range queries and efficient prefix scans in storage engines.
    """

    def encode(self, key: Key) -> EncodedKeyT:
        """Encode a key for storage.

        Args:
            key: The key to encode

        Returns:
            Encoded key suitable for storage

        Raises:
            EncodeError: If encoding fails
            ValueError: If key type is invalid
        """
        ...

    def decode(self, encoded: EncodedKeyT) -> Key:
        """Decode a key from storage.

        Args:
            encoded: Encoded key to decode

        Returns:
            Decoded key

        Raises:
            DecodeError: If decoding fails
            ValueError: If encoded format is invalid
        """
        ...


class ValueCodecProtocol(Protocol[EncodedValueT]):
    """Protocol for encoding/decoding storage values.

    Type Parameters:
        ValueT: The type of values that can be encoded (contravariant)
        EncodedValueT: The type of encoded values (covariant)
    """

    def encode(self, value: Value) -> EncodedValueT:
        """Encode a value for storage.

        Args:
            value: The value to encode

        Returns:
            Encoded value suitable for storage

        Raises:
            EncodeError: If encoding fails
            ValueError: If value type is invalid
            TypeError: If value contains unsupported types
        """
        ...

    def decode(self, encoded: EncodedValueT) -> Value:
        """Decode a value from storage.

        Args:
            encoded: Encoded value to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If decoding fails
            ValueError: If encoded format is invalid
            TypeError: If encoded value contains invalid types
        """
        ...


class StorageProtocol(Protocol):
    """Protocol for state storage adapters."""

    def get(self, key: Key) -> Value:
        """Get value by key.

        Args:
            key: State key to retrieve

        Returns:
            State value if found, None otherwise

        Raises:
            StateError: If value cannot be retrieved
        """
        ...

    def set(self, key: Key, value: Value) -> None:
        """Set value by key.

        Args:
            key: State key to set
            value: Value to store

        Raises:
            StateError: If value cannot be stored
        """
        ...

    def delete(self, key: Key) -> None:
        """Delete value by key.

        Args:
            key: State key to delete

        Raises:
            StateError: If value cannot be deleted
        """
        ...

    def exists(self, key: Key) -> bool:
        """Check if key exists.

        Args:
            key: State key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StateError: If check fails
        """
        ...

    def list_keys(
        self,
        prefix: Key,
        depth: int = ...,
    ) -> Generator[Key, None, None]:
        """List all keys under prefix.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching state keys

        Raises:
            StateError: If listing fails
        """
        ...

    def begin_transaction(self) -> TransactionProtocol:
        """Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> TransactionContextManagerProtocol:
        """Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...

    def begin_snapshot(self) -> SnapshotProtocol:
        """Begin snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be started
        """
        ...

    def snapshot(self) -> SnapshotContextManagerProtocol:
        """Get snapshot context manager.

        Returns:
            Snapshot context manager
        """
        ...

    def __hash__(self) -> int:
        """Get hash of the storage.

        Returns:
            Hash value of the storage
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the storage.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


@runtime_checkable
class TransactionProtocol(Protocol):
    """Protocol defining the interface for transactions."""

    def get(self, key: Key) -> Value:
        """Get value within transaction context.

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            TransactionError: If transaction is invalid or operation fails
            KeyError: If key not found
            StorageOperationError: If get operation fails
        """
        ...

    def set(self, key: Key, value: Value) -> None:
        """Set value within transaction context.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If set operation fails
        """
        ...

    def delete(self, key: Key) -> None:
        """Delete value within transaction context.

        Args:
            key: Key to delete

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If delete operation fails
        """
        ...

    def exists(self, key: Key) -> bool:
        """Check if key exists within transaction context.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            TransactionError: If transaction is invalid or operation fails
            StorageOperationError: If exists check fails
        """
        ...

    def list_keys(
        self,
        prefix: Key,
        depth: int = ...,
    ) -> Generator[Key, None, None]:
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
        ...

    def commit(self) -> None:
        """Commit all changes in the transaction.

        Raises:
            TransactionError: If commit fails or transaction is invalid
            StorageOperationError: If storage operations fail during commit
        """
        ...

    def rollback(self) -> None:
        """Roll back all changes in the transaction.

        Raises:
            TransactionError: If rollback fails or transaction is invalid
        """
        ...

    def __hash__(self) -> int:
        """Get hash of the transaction.

        Returns:
            Hash value of the transaction
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the transaction.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class TransactionContextManagerProtocol(Protocol):
    """Context manager for storage transactions."""

    def __enter__(self) -> TransactionProtocol:
        """Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit or rollback transaction based on context exit.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception type if an error occurred.
            exc_val (Optional[BaseException]): Exception value if an error occurred.
            exc_tb (Optional[TracebackType]): Exception traceback if an error occurred.

        Returns:
            None
        """
        ...


class TransactionalHandlerProtocol(Protocol):
    """Protocol defining the interface for transactionable storage."""

    def begin_transaction(self) -> TransactionProtocol:
        """Begin a new transaction."""
        ...

    def transaction(self) -> TransactionContextManagerProtocol:
        """Get a typed transaction context manager."""
        ...


@runtime_checkable
class SnapshotProtocol(Protocol):
    """Protocol defining the interface for read-only snapshots."""

    def get(self, key: Key) -> Value:
        """Get value within snapshot context.

        Args:
            key: Key to retrieve

        Returns:
            Value if found, None if not found

        Raises:
            KeyError: If key not found
            StorageOperationError: If get operation fails
        """
        ...

    def exists(self, key: Key) -> bool:
        """Check if key exists within snapshot context.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageOperationError: If exists check fails
        """
        ...

    def list_keys(
        self,
        prefix: Key,
        depth: int = ...,
    ) -> Generator[Key, None, None]:
        """List all keys under prefix within snapshot context.

        Args:
            prefix: Key prefix to list
            depth: Depth of listing (default is 1)
                If depth is -1, lists all keys under prefix.

        Returns:
            Generator of matching keys

        Raises:
            StorageOperationError: If list operation fails
        """
        ...

    def close(self) -> None:
        """Close snapshot and clean up resources.

        Raises:
            StorageOperationError: If cleanup fails
        """
        ...

    def __hash__(self) -> int:
        """Get hash of the snapshot.

        Returns:
            Hash value of the snapshot
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the snapshot.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class SnapshotContextManagerProtocol(Protocol):
    """Context manager for storage snapshots."""

    def __enter__(self) -> SnapshotProtocol:
        """Create a new snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be created
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up snapshot resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        ...


class SnapshotHandlerProtocol(Protocol):
    """Protocol defining the interface for snapshot-capable storage."""

    def begin_snapshot(self) -> SnapshotProtocol:
        """Begin a new read-only snapshot."""
        ...

    def snapshot(self) -> SnapshotContextManagerProtocol:
        """Get a typed snapshot context manager."""
        ...


class ObserverProtocol(Protocol):
    """Protocol for observable adapters."""

    def subscribe(
        self,
        key: Key,
        callback: CallbackFn,
        depth: int = ...,
    ) -> SubscriptionProtocol:
        """Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        ...

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    def notify(self, topic: Key) -> None:
        """Notify observers of a change at the specified topic.

        Args:
            topic: Topic identifying changed state

        Raises:
            ObserverError: If notification fails
        """

    def __hash__(self) -> int:
        """Get hash of the observer.

        Returns:
            Hash value of the observer
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the observer.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class SubscriptionProtocol(Protocol):
    """Represents a subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Callable that will be invoked on matching notifications.
            Must accept a single parameter of type StorageValue.

    Type Parameters:
        StorageValue: Topic type (tuple of strings)
    """

    @property
    def topic_pattern(self) -> Key:
        """Get topic pattern for subscription."""
        ...

    @property
    def callback(self) -> CallbackFn:
        """Get callback for subscription."""
        ...

    @property
    def depth(self) -> int:
        """Get depth for subscription."""
        ...
