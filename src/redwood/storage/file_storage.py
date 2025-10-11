"""File-based storage implementation with transaction support."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import attrs
import filelock
from mesh import Attach, ResourceSpec, Spec
from mesh.common.logging import get_logger

from redwood.exceptions import (
    SnapshotError,
    StorageError,
    StorageKeyError,
    StorageOperationError,
    TransactionError,
    TransactionInvalidError,
)

from ._base import BaseStorage


if TYPE_CHECKING:
    from collections.abc import Generator
    from logging import Logger

    from redwood.protocols import (
        SnapshotProtocol,
        StorageCodecProtocol,
        StorageProtocol,
        TransactionProtocol,
    )
    from redwood.types import Key, Value


logger: Logger = get_logger(__name__)


__all__ = [
    "FileStorage",
    "FileStorageSnapshot",
    "FileStorageSpec",
    "FileStorageTransaction",
]


@dataclass
class TransactionOperation:
    """Represents a single operation in a transaction."""

    op_type: str  # "set" or "delete"
    key: Key
    value: Value | None = None


class FileStorage(BaseStorage[str, str]):
    """Simple file-based storage implementation with transaction support.

    Uses basic locking strategy for correctness over efficiency.
    """

    codec: StorageCodecProtocol[str, str] = Attach()

    spec: FileStorageSpec

    def setup(self) -> None:
        """Set up file storage resources."""
        self.path = (
            self.spec.path.resolve()
            if isinstance(self.spec.path, Path)
            else Path(self.spec.path).resolve()
        )

        # Single lock for all in-process synchronization
        self._memory_lock = threading.Lock()

        # Database file path
        self._data_file_path = self.path / "db.json"

        # Single lock file for all inter-process synchronization
        self._lock_file = self.path / f"{self.path.name}.lock"
        self._file_lock = filelock.FileLock(self._lock_file)

        self._data: dict[str, str] = {}
        self._active_transactions: set[FileStorageTransaction] = set()

        super().setup()

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()

        # Clean up lock file
        if self._lock_file.exists():
            self._lock_file.unlink()
        if self._memory_lock.locked():
            self._memory_lock.release()
        if self._file_lock.is_locked:
            self._file_lock.release()
        self._data.clear()
        self._active_transactions.clear()

    def _connect_impl(self) -> None:
        """Load data from file if it exists."""
        # Ensure directory exists
        self.path.mkdir(parents=True, exist_ok=True)
        self._data_file_path.touch(exist_ok=True)

        with self._memory_lock, self._file_lock:
            # Create file if needed
            if not self.path.exists():
                if self.mode == "write":
                    with Path.open(self._data_file_path, "w") as f:
                        f.write("{}")
                else:
                    raise StorageError(
                        f"Storage file {self.path} does not exist and mode is read-only"
                    )

            # Load initial data
            self._load_data()

        logger.debug(f"Connected to file storage at {self.path} in {self.mode} mode")

    def _disconnect_impl(self) -> None:
        """Ensure all data is saved and clean up."""
        with self._memory_lock, self._file_lock:
            # Roll back any active transactions
            for transaction in self._active_transactions.copy():
                transaction.rollback()

            # Final save if in write mode
            if self.mode == "write":
                self._save()

        logger.debug("Disconnected from file storage")

    def _load_data(self) -> None:
        """Load data from file. Must be called with both locks held."""
        try:
            content = self._data_file_path.read_text()
            self._data = json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            raise StorageError(f"Corrupted storage file: {e}") from e
        except Exception as e:
            raise StorageError(f"Failed to load data: {e}") from e

    def _save(self) -> None:
        """Save data to file. Must be called with both locks held."""
        if self.mode != "write":
            raise StorageError("Cannot save in read-only mode")

        temp_path = self._data_file_path.with_suffix(".tmp")
        try:
            content = json.dumps(self._data, indent=2)
            with Path.open(temp_path, "w") as f:
                f.write(content)
            Path.replace(temp_path, self._data_file_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to save data: {e}") from e

    def _get_impl(self, key: Key) -> Value:
        """Get value by key."""
        encoded_key = self.codec.encode_key(key)

        # Always get fresh data
        with self._memory_lock, self._file_lock:
            self._load_data()
            try:
                encoded_value = self._data[encoded_key]
            except KeyError as e:
                raise StorageKeyError(f"Key {key} not found") from e

            try:
                return self.codec.decode_value(encoded_value)
            except Exception as e:
                raise StorageOperationError(f"Failed to decode value: {e}") from e

    def _set_impl(self, key: Key, value: Value) -> None:
        """Set value for key."""
        encoded_key = self.codec.encode_key(key)
        encoded_value = self.codec.encode_value(value)

        with self._memory_lock, self._file_lock:
            self._load_data()  # Get latest data
            self._data[encoded_key] = encoded_value
            self._save()

    def _delete_impl(self, key: Key) -> None:
        """Delete value by key."""
        encoded_key = self.codec.encode_key(key)

        with self._memory_lock, self._file_lock:
            self._load_data()  # Get latest data
            try:
                del self._data[encoded_key]
            except KeyError as e:
                raise StorageKeyError(f"Key {key} not found") from e
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key: {e}") from e
            self._save()

    def _exists_impl(self, key: Key) -> bool:
        """Check if key exists."""
        encoded_key = self.codec.encode_key(key)

        with self._memory_lock, self._file_lock:
            self._load_data()  # Get latest data
            return encoded_key in self._data

    def _list_keys_impl(self, prefix: Key, depth: int) -> Generator[Key, None, None]:
        """List all keys under prefix."""
        encoded_prefix = self.codec.encode_key(prefix)

        # Get snapshot of keys while holding locks
        with self._memory_lock, self._file_lock:
            self._load_data()  # Get latest data
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
    ) -> FileStorageTransaction:
        """Begin a new transaction."""
        transaction = FileStorageTransaction(self)
        with self._memory_lock:
            self._active_transactions.add(transaction)
        return transaction

    def _begin_snapshot_impl(
        self,
    ) -> FileStorageSnapshot:
        """Begin a new read-only snapshot."""
        # Create snapshot with current data state
        with self._memory_lock, self._file_lock:
            self._load_data()  # Get latest data
            # Create a deep copy of current data for the snapshot
            snapshot_data = self._data.copy()

        return FileStorageSnapshot(self, snapshot_data)

    def _apply_transaction(self, transaction: FileStorageTransaction) -> None:
        """Apply transaction operations atomically."""
        if self.mode != "write":
            raise StorageError("Cannot apply transaction in read-only mode")

        with self._memory_lock, self._file_lock:
            try:
                self._load_data()  # Get latest data

                # Apply all operations
                for op in transaction._operations:
                    encoded_key = self.codec.encode_key(op.key)
                    if op.op_type == "set":
                        encoded_value = self.codec.encode_value(op.value)
                        self._data[encoded_key] = encoded_value
                    elif op.op_type == "delete":
                        self._data.pop(encoded_key, None)

                # Save changes
                self._save()

                # Remove from active transactions
                self._active_transactions.discard(transaction)

            except Exception as e:
                # Attempt rollback
                try:
                    transaction.rollback()
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
                raise TransactionError(f"Failed to apply transaction: {e}") from e


class FileStorageTransaction:
    """Implementation of transaction for file-based storage."""

    def __init__(self, storage: FileStorage) -> None:
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

    def get(self, key: Key) -> Value:
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

    def set(self, key: Key, value: Value) -> None:
        """Set value within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("set", key, value))

    def delete(self, key: Key) -> None:
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

    def exists(self, key: Key) -> bool:
        """Check if key exists within transaction context."""
        self._check_valid()
        try:
            self.get(key)
            return True
        except StorageKeyError:
            return False

    def list_keys(self, prefix: Key, depth: int = 1) -> Generator[Key, None, None]:
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
        self._storage._apply_transaction(self)
        self._committed = True

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


class FileStorageSnapshot:
    """File storage read-only snapshot implementation."""

    def __init__(self, storage: FileStorage, snapshot_data: dict[str, str]) -> None:
        """Initialize snapshot with data copy."""
        self._storage = storage
        self._snapshot_data = snapshot_data
        self._closed = False
        self._uuid = uuid4()

    def _check_valid(self) -> None:
        """Check if snapshot is still valid."""
        if self._closed:
            raise SnapshotError("Snapshot already closed")

    def get(self, key: Key) -> Value:
        """Get value within snapshot context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)

        try:
            encoded_value = self._snapshot_data[encoded_key]
        except KeyError as e:
            raise StorageKeyError(f"Key {key} not found") from e

        try:
            return self._storage.codec.decode_value(encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to decode value: {e}") from e

    def exists(self, key: Key) -> bool:
        """Check if key exists within snapshot context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        return encoded_key in self._snapshot_data

    def list_keys(self, prefix: Key, depth: int = 1) -> Generator[Key, None, None]:
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
class FileStorageSpec(ResourceSpec):
    """Specification for FileStorage resource."""

    name: str = "file_storage"
    factory: type = FileStorage
    mode: str = "write"
    path: Path | str = Path(".db")
    codec: Spec


if TYPE_CHECKING:
    _: type[StorageProtocol] = FileStorage
    __: type[TransactionProtocol] = FileStorageTransaction
    ___: type[SnapshotProtocol] = FileStorageSnapshot
