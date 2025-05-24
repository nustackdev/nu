from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Generator
from uuid import uuid4

from loomi.attr import UseService
from loomi.interfaces.state.kv import SyncStorageProtocol, SyncTransactionProtocol
from loomi.service import SyncService
from loomi.spec import Spec, SpecField
from loomistd.codec import CodecProtocol
from loomistd.codec.passthrough import PassthroughCodecSpec

from .._base import BaseStorage
from .._exceptions import (
    StorageKeyError,
    StorageOperationError,
    TransactionConflictError,
    TransactionError,
    TransactionInvalidError,
)
from .logger import logger
from .types import (
    InMemoryStorageEncodedKey,
    InMemoryStorageEncodedValue,
    InMemoryStorageKey,
    InMemoryStorageValue,
    TransactionOperation,
)

__all__ = [
    "InMemoryStorage",
    "InMemoryStorageSpec",
    "InMemoryStorageTransaction",
]


class InMemoryStorage(
    BaseStorage[
        InMemoryStorageKey,
        InMemoryStorageValue,
        InMemoryStorageEncodedKey,
        InMemoryStorageEncodedValue,
    ],
    SyncService,
):
    """
    Simple file-based storage implementation with transaction support.
    Uses basic locking strategy for correctness over efficiency.
    """

    codec: CodecProtocol[
        InMemoryStorageKey,
        InMemoryStorageValue,
        InMemoryStorageEncodedKey,
        InMemoryStorageEncodedValue,
    ] = UseService()

    spec: InMemoryStorageSpec

    def setup(self):
        self._data: dict[InMemoryStorageEncodedKey, InMemoryStorageEncodedValue] = {}
        self._data_lock = threading.Lock()
        self._active_transactions: set[InMemoryStorageTransaction] = set()
        super().setup()

    def cleanup(self):
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

    def _get_impl(self, key: InMemoryStorageKey) -> InMemoryStorageValue:
        """Get value by key."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            try:
                if encoded_key not in self._data:
                    raise StorageKeyError(f"Key {key} not found")
                return self._data[encoded_key]
            except Exception as e:
                if not isinstance(e, StorageKeyError):
                    raise StorageOperationError(f"Failed to get key {key}: {e}")
                raise

    def _set_impl(self, key: InMemoryStorageKey, value: InMemoryStorageValue) -> None:
        """Set value for key."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            try:
                self._data[encoded_key] = value
            except Exception as e:
                raise StorageOperationError(f"Failed to set key {key}: {e}")

    def _delete_impl(self, key: InMemoryStorageKey) -> None:
        """Delete key."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            try:
                self._data.pop(encoded_key, None)
            except KeyError:
                raise StorageKeyError(f"Key {key} not found")
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key {key}: {e}")

    def _exists_impl(self, key: InMemoryStorageKey) -> bool:
        """Check if key exists."""
        encoded_key = self.codec.encode_key(key)

        with self._data_lock:
            return encoded_key in self._data

    def _list_keys_impl(
        self, prefix: InMemoryStorageKey, depth: int
    ) -> Generator[InMemoryStorageKey, None, None]:
        """List all keys under prefix."""
        encoded_prefix = self.codec.encode_key(prefix)

        # Get snapshot of keys
        with self._data_lock:
            matching_keys = []
            for encoded_key in self._data.keys():
                if encoded_key.startswith(encoded_prefix):
                    # Split the key into parts based on '/' for depth calculation
                    decoded_key = self.codec.decode_key(encoded_key)
                    if depth == -1 or len(decoded_key) - len(prefix) == depth:
                        matching_keys.append(decoded_key)

        # Yield outside lock
        for key in matching_keys:
            yield key

    def _begin_transaction_impl(
        self,
    ) -> InMemoryStorageTransaction:
        """Begin a new transaction."""
        transaction = InMemoryStorageTransaction(self)
        with self._data_lock:
            self._active_transactions.add(transaction)
        return transaction

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
                raise TransactionError(f"Failed to apply transaction: {e}")


class InMemoryStorageTransaction:
    """Simple in-memory transaction implementation."""

    def __init__(self, storage: InMemoryStorage):
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

    def get(self, key: InMemoryStorageKey) -> InMemoryStorageValue:
        """Get value within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)

        # Check transaction operations first
        for op in reversed(self._operations):
            if self._storage.codec.encode_key(op.key) == encoded_key:
                if op.op_type == "delete":
                    raise StorageKeyError(f"Key {key} was deleted in this transaction")
                return op.value

        # Get from storage
        value = self._storage.get(key)
        self._read_set.add(encoded_key)
        return value

    def set(self, key: InMemoryStorageKey, value: InMemoryStorageValue) -> None:
        """Set value within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("set", key, value))

    def delete(self, key: InMemoryStorageKey) -> None:
        """Delete key within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("delete", key))

    def exists(self, key: InMemoryStorageKey) -> bool:
        """Check if key exists within transaction context."""
        self._check_valid()
        try:
            self.get(key)
            return True
        except StorageKeyError:
            return False

    def list_keys(
        self, prefix: InMemoryStorageKey, depth: int = 1
    ) -> Generator[InMemoryStorageKey, None, None]:
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
            encoded_key = self._storage.codec.encode_key(op.key)
            if encoded_key.startswith(encoded_prefix):
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
            raise TransactionError(f"Failed to commit transaction: {e}")

    def rollback(self) -> None:
        """Roll back transaction changes."""
        self._check_valid()
        self._rolled_back = True
        self._operations.clear()
        self._read_set.clear()
        self._write_set.clear()

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: Any) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self._uuid == other._uuid


class InMemoryStorageSpec(Spec):
    name: str = SpecField(default="in_memory_storage")
    factory: type = SpecField(default=InMemoryStorage)
    mode: str = SpecField(default="write")
    codec: Spec = SpecField(default_factory=PassthroughCodecSpec)


if TYPE_CHECKING:
    _: type[SyncStorageProtocol] = InMemoryStorage
    __: type[SyncTransactionProtocol] = InMemoryStorageTransaction
