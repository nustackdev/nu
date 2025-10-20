"""In-memory storage implementation with transaction support."""

from __future__ import annotations

import threading
from collections.abc import Generator
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING
from uuid import uuid4

import attrs
from mesh import Attach, ResourceSpec, Spec

from redwood.abc import Value
from redwood.exceptions import (
    SnapshotError,
    StorageKeyError,
    StorageOperationError,
    TransactionConflictError,
    TransactionError,
    TransactionInvalidError,
)

from ._base import BaseStorage


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import TupleKey
    from redwood.backend import (
        CodecProtocol,
        SnapshotProtocol,
        StorageProtocol,
        TransactionProtocol,
    )


logger = getLogger(__name__)


@dataclass
class TransactionOperation:
    """Represents a single operation in a transaction."""

    op_type: str  # "set" or "delete"
    key: TupleKey
    value: Value | None = None


class InMemoryStorage(BaseStorage[str, Value]):
    """Simple file-based storage implementation with transaction support.

    Uses basic locking strategy for correctness over efficiency.
    """

    codec: CodecProtocol[
        str,
        Value,
    ] = Attach()

    spec: InMemoryStorageSpec

    def setup(self) -> None:
        """Initialize in-memory storage."""
        self._data: dict[str, Value] = {}
        self._data_lock = threading.Lock()
        self._active_transactions: set[InMemoryStorageTransaction] = set()
        super().setup()

    def cleanup(self) -> None:
        """Clean up in-memory storage."""
        super().cleanup()
        self._data.clear()
        self._active_transactions.clear()
        if self._data_lock.locked():
            self._data_lock.release()

    def _connect_impl(self) -> None:
        """Initialize storage."""
        with self._data_lock:
            self._data.clear()
            self._active_transactions.clear()
        logger.debug("Connected to in-memory storage")

    def _disconnect_impl(self) -> None:
        """Clean up storage."""
        with self._data_lock:
            # Roll back any active transactions
            for transaction in self._active_transactions.copy():
                transaction.rollback()

            self._data.clear()
        logger.debug("Disconnected from in-memory storage")

    def _get_impl(self, key: TupleKey) -> Value:
        """Get value by key."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            try:
                if encoded_key not in self._data:
                    raise StorageKeyError(f"Key {key} not found")
                return self._data[encoded_key]
            except Exception as e:
                if not isinstance(e, StorageKeyError):
                    raise StorageOperationError(f"Failed to get key {key}: {e}") from e
                raise

    def _set_impl(self, key: TupleKey, value: Value) -> None:
        """Set value for key."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            try:
                self._data[encoded_key] = value
            except Exception as e:
                raise StorageOperationError(f"Failed to set key {key}: {e}") from e

    def _delete_impl(self, key: TupleKey) -> None:
        """Delete key."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            try:
                self._data.pop(encoded_key, None)
            except KeyError as e:
                raise StorageKeyError(f"Key {key} not found") from e
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

    def _exists_impl(self, key: TupleKey) -> bool:
        """Check if key exists."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            return encoded_key in self._data

    def _list_keys_impl(self, prefix: TupleKey, depth: int) -> Generator[TupleKey, None, None]:
        """List all keys under prefix."""
        encoded_prefix = self.codec.encode_key(prefix)

        # Get snapshot of keys
        with self._data_lock:
            matching_keys = []
            for encoded_key in self._data:
                if encoded_key.startswith(encoded_prefix):
                    # Split the key into parts based on '/' for depth calculation
                    decoded_key = self.codec.decode_key(encoded_key)
                    if depth == -1 or len(decoded_key) - len(prefix) == depth:
                        matching_keys.append(decoded_key)

        # Yield outside lock
        matching_keys.sort()  # Sort for consistent ordering
        yield from matching_keys

    def _begin_transaction_impl(
        self,
    ) -> InMemoryStorageTransaction:
        """Begin a new transaction."""
        transaction = InMemoryStorageTransaction(self)
        with self._data_lock:
            self._active_transactions.add(transaction)
        return transaction

    def _begin_snapshot_impl(
        self,
    ) -> InMemoryStorageSnapshot:
        """Begin a new read-only snapshot."""
        # Create snapshot with current data state
        with self._data_lock:
            # Create a deep copy of current data for the snapshot
            snapshot_data = self._data.copy()

        return InMemoryStorageSnapshot(self, snapshot_data)

    def _check_conflicts(self, transaction: InMemoryStorageTransaction) -> bool:
        """Check for conflicts with other transactions."""
        with self._data_lock:
            for other_txn in self._active_transactions:
                if other_txn is not transaction:
                    # Check for write-write conflicts
                    if transaction._write_set & other_txn._write_set:
                        return False
                    # Check for read-write conflicts
                    if transaction._read_set & other_txn._write_set:
                        return False
            return True

    def _apply_transaction(self, transaction: InMemoryStorageTransaction) -> None:
        """Apply transaction operations atomically."""
        with self._data_lock:
            try:
                # Apply operations
                for op in transaction._operations:
                    encoded_key = self.codec.encode_key(op.key)
                    if op.op_type == "set":
                        self._data[encoded_key] = op.value
                    elif op.op_type == "delete":
                        self._data.pop(encoded_key, None)

                # Remove from active transactions
                self._active_transactions.discard(transaction)

            except Exception as e:
                # Attempt rollback
                try:
                    transaction.rollback()
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
                raise TransactionError(f"Failed to apply transaction: {e}") from e


class InMemoryStorageTransaction:
    """Simple in-memory transaction implementation."""

    def __init__(self, storage: InMemoryStorage) -> None:
        """Initialize transaction."""
        self._storage = storage
        self._operations: list[TransactionOperation] = []
        self._read_set: set[str] = set()
        self._write_set: set[str] = set()
        self._committed = False
        self._rolled_back = False
        self._uuid = uuid4()

    def _check_valid(self) -> None:
        """Check if transaction is still valid."""
        if self._committed:
            raise TransactionInvalidError("Transaction already committed")
        if self._rolled_back:
            raise TransactionInvalidError("Transaction already rolled back")

    def get(self, key: TupleKey) -> Value:
        """Get value within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)

        # Check transaction operations first
        for op in reversed(self._operations):
            if self._storage.codec.encode_key(op.key) == encoded_key:
                if op.op_type == "delete":
                    raise StorageKeyError(f"Key {key} was deleted in this transaction")
                elif op.op_type == "set":
                    return op.value

        # Get from storage
        value = self._storage.get(key)
        self._read_set.add(encoded_key)
        return value

    def set(self, key: TupleKey, value: Value) -> None:
        """Set value within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("set", key, value))

    def delete(self, key: TupleKey) -> None:
        """Delete key within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)

        # Raise error if key does not exist in neither storage nor transaction
        key_exists = False

        # 1. Check transaction operations first.
        # Loop over operations in reverse order to find the last operation
        for op in reversed(self._operations):
            if self._storage.codec.encode_key(op.key) == encoded_key:
                if op.op_type == "delete":
                    # If last operation is a delete, we should raise an error
                    raise StorageKeyError(f"Key {key} was already deleted in this transaction")
                elif op.op_type == "set":
                    # If last operation is a set, we can can remove it
                    key_exists = True
                    break

        # 2. Check storage if key does not exist in transaction
        if not key_exists and self._storage.exists(key):
            key_exists = True

        if not key_exists:
            raise StorageKeyError(f"Key {key} does not exist")

        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("delete", key))

    def exists(self, key: TupleKey) -> bool:
        """Check if key exists within transaction context."""
        self._check_valid()
        try:
            self.get(key)
            return True
        except StorageKeyError:
            return False

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        """List all keys under prefix within transaction."""
        self._check_valid()

        # Get snapshot of keys, considering transaction changes
        encoded_prefix = self._storage.codec.encode_key(prefix)

        # Get current keys from storage
        base_keys = set()
        for key in self._storage.list_keys(prefix, depth):
            encoded_key = self._storage.codec.encode_key(key)
            if encoded_key.startswith(encoded_prefix):
                base_keys.add(encoded_key)

        # Apply transaction operations
        for op in self._operations:
            if len(op.key) < len(prefix):
                continue

            if prefix != op.key[: len(prefix)]:
                continue

            if depth == -1 or len(op.key) - len(prefix) == depth:
                encoded_key = self._storage.codec.encode_key(op.key)
                if op.op_type == "set":
                    base_keys.add(encoded_key)
                elif op.op_type == "delete":
                    base_keys.discard(encoded_key)

        # Yield final set of keys
        for encoded_key in sorted(base_keys):  # Sort for consistent ordering
            yield self._storage.codec.decode_key(encoded_key)

    def commit(self) -> None:
        """Commit transaction changes."""
        self._check_valid()

        if not self._storage._check_conflicts(self):
            raise TransactionConflictError("Transaction conflicts with other changes")

        try:
            self._storage._apply_transaction(self)
            self._committed = True
        except Exception as e:
            raise TransactionError(f"Failed to commit transaction: {e}") from e

    def rollback(self) -> None:
        """Roll back transaction changes."""
        self._check_valid()
        self._rolled_back = True
        self._operations.clear()
        self._read_set.clear()
        self._write_set.clear()

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self._uuid == other._uuid


class InMemoryStorageSnapshot:
    """In-memory storage read-only snapshot implementation."""

    def __init__(
        self,
        storage: InMemoryStorage,
        snapshot_data: dict[str, Value],
    ) -> None:
        """Initialize snapshot with data copy."""
        self._storage = storage
        self._snapshot_data = snapshot_data
        self._closed = False
        self._uuid = uuid4()

    def _check_valid(self) -> None:
        """Check if snapshot is still valid."""
        if self._closed:
            raise SnapshotError("Snapshot already closed")

    def get(self, key: TupleKey) -> Value:
        """Get value within snapshot context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)

        try:
            if encoded_key not in self._snapshot_data:
                raise StorageKeyError(f"Key {key} not found")
            return self._snapshot_data[encoded_key]
        except Exception as e:
            if not isinstance(e, StorageKeyError):
                raise StorageOperationError(f"Failed to get key {key}: {e}") from e
            raise

    def exists(self, key: TupleKey) -> bool:
        """Check if key exists within snapshot context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        return encoded_key in self._snapshot_data

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        """List all keys under prefix within snapshot context."""
        self._check_valid()
        encoded_prefix = self._storage.codec.encode_key(prefix)

        matching_keys = []
        for encoded_key in self._snapshot_data:
            if encoded_key.startswith(encoded_prefix):
                decoded_key = self._storage.codec.decode_key(encoded_key)
                if depth == -1 or len(decoded_key) - len(prefix) == depth:
                    matching_keys.append(decoded_key)

        # Yield sorted keys for consistent ordering
        yield from sorted(matching_keys)

    def close(self) -> None:
        """Close snapshot and clean up resources."""
        if not self._closed:
            self._snapshot_data.clear()
            self._closed = True

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self._uuid == other._uuid


@attrs.define(frozen=True, slots=True, kw_only=True)
class InMemoryStorageSpec(ResourceSpec):
    """Specification for InMemoryStorage resource."""

    name: str = "in_memory_storage"
    factory: type = InMemoryStorage
    mode: str = "write"
    codec: Spec


if TYPE_CHECKING:
    _: type[StorageProtocol] = InMemoryStorage
    __: type[TransactionProtocol] = InMemoryStorageTransaction
    ___: type[SnapshotProtocol] = InMemoryStorageSnapshot
