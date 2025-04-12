from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncGenerator

import aiofile
import filelock
from pydantic import Field

from loomi import AsyncService, Attach, Spec
from loomistd.codec import CodecProtocol
from loomistd.codec.json import JSONCodec

from .._base import BaseStorage, BaseStorageSpec
from .._exceptions import (
    StorageError,
    StorageKeyError,
    StorageOperationError,
    TransactionError,
    TransactionInvalidError,
)
from .._protocols import TransactionProtocol
from .logger import logger
from .types import (
    FileStorageEncodedKey,
    FileStorageEncodedValue,
    FileStorageKey,
    FileStorageValue,
    TransactionOperation,
)

__all__ = [
    "FileStorage",
    "FileStorageSpec",
    "FileStorageTransaction",
]


class FileStorageSpec(BaseStorageSpec):
    path: Path = Field(default=Path("state/db.json"))
    codec: Spec = Field(default=Spec(factory=JSONCodec))


class FileStorage(
    BaseStorage[
        FileStorageKey,
        FileStorageValue,
        FileStorageEncodedKey,
        FileStorageEncodedValue,
    ],
    AsyncService,
):
    """
    Simple file-based storage implementation with transaction support.
    Uses basic locking strategy for correctness over efficiency.
    """

    _codec: CodecProtocol[
        FileStorageKey, FileStorageValue, FileStorageEncodedKey, FileStorageEncodedValue
    ] = Attach(JSONCodec)

    def __init__(
        self,
        spec: FileStorageSpec,
    ):
        """Initialize file storage."""
        super().__init__(spec)
        self.path = spec.path

        # Single lock for all in-process synchronization
        self._memory_lock = asyncio.Lock()

        # Single lock file for all inter-process synchronization
        self._lock_file = self.path.parent / f"{self.path.name}.lock"
        self._file_lock = filelock.FileLock(self._lock_file)

        self._data: dict[str, str] = {}
        self._connected = False
        self._active_transactions: set[FileStorageTransaction] = set()

    async def _connect_impl(self) -> None:
        """Load data from file if it exists."""
        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        async with self._memory_lock:
            with self._file_lock:
                # Create file if needed
                if not self.path.exists():
                    if self.mode == "write":
                        async with aiofile.async_open(self.path, "w") as f:
                            await f.write("{}")
                    else:
                        raise StorageError(
                            f"Storage file {self.path} does not exist and mode is read-only"
                        )

                # Load initial data
                await self._load_data()

        logger.debug(f"Connected to file storage at {self.path} in {self.mode} mode")

    async def _disconnect_impl(self) -> None:
        """Ensure all data is saved and clean up."""
        async with self._memory_lock:
            with self._file_lock:
                # Roll back any active transactions
                for transaction in self._active_transactions.copy():
                    await transaction.rollback()

                # Final save if in write mode
                if self.mode == "write":
                    await self._save()

        self._connected = False
        logger.debug("Disconnected from file storage")

    async def _load_data(self) -> None:
        """Load data from file. Must be called with both locks held."""
        try:
            content = self.path.read_text()
            self._data = json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            raise StorageError(f"Corrupted storage file: {e}")
        except Exception as e:
            raise StorageError(f"Failed to load data: {e}")

    async def _save(self) -> None:
        """Save data to file. Must be called with both locks held."""
        if self.mode != "write":
            raise StorageError("Cannot save in read-only mode")

        temp_path = self.path.with_suffix(".tmp")
        try:
            content = json.dumps(self._data, indent=2)
            async with aiofile.async_open(temp_path, "w") as f:
                await f.write(content)
            os.replace(temp_path, self.path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to save data: {e}")

    async def _get_impl(self, key: FileStorageKey) -> FileStorageValue:
        """Get value by key."""
        encoded_key = self.codec.encode_key(key)

        # Always get fresh data
        async with self._memory_lock:
            with self._file_lock:
                await self._load_data()
                try:
                    encoded_value = self._data[encoded_key]
                except KeyError:
                    raise StorageKeyError(f"Key {key} not found")

                try:
                    return self.codec.decode_value(encoded_value)
                except Exception as e:
                    raise StorageOperationError(f"Failed to decode value: {e}")

    async def _set_impl(self, key: FileStorageKey, value: FileStorageValue) -> None:
        """Set value for key."""
        encoded_key = self.codec.encode_key(key)
        encoded_value = self.codec.encode_value(value)

        async with self._memory_lock:
            with self._file_lock:
                await self._load_data()  # Get latest data
                self._data[encoded_key] = encoded_value
                await self._save()

    async def _delete_impl(self, key: FileStorageKey) -> None:
        """Delete value by key."""
        encoded_key = self.codec.encode_key(key)

        async with self._memory_lock:
            with self._file_lock:
                await self._load_data()  # Get latest data
                try:
                    del self._data[encoded_key]
                except KeyError:
                    raise StorageKeyError(f"Key {key} not found")
                except Exception as e:
                    raise StorageOperationError(f"Failed to delete key: {e}")
                await self._save()

    async def _exists_impl(self, key: FileStorageKey) -> bool:
        """Check if key exists."""
        encoded_key = self.codec.encode_key(key)

        async with self._memory_lock:
            with self._file_lock:
                await self._load_data()  # Get latest data
                return encoded_key in self._data

    async def _list_keys_impl(
        self, prefix: FileStorageKey, depth: int
    ) -> AsyncGenerator[FileStorageKey, None]:
        """List all keys under prefix."""
        encoded_prefix = self.codec.encode_key(prefix)

        # Get snapshot of keys while holding locks
        async with self._memory_lock:
            with self._file_lock:
                await self._load_data()  # Get latest data
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

    async def _begin_transaction_impl(
        self,
    ) -> FileStorageTransaction:
        """Begin a new transaction."""
        transaction = FileStorageTransaction(self)
        async with self._memory_lock:
            self._active_transactions.add(transaction)
        return transaction

    async def _apply_transaction(self, transaction: FileStorageTransaction) -> None:
        """Apply transaction operations atomically."""
        if self.mode != "write":
            raise StorageError("Cannot apply transaction in read-only mode")

        async with self._memory_lock:
            with self._file_lock:
                try:
                    await self._load_data()  # Get latest data

                    # Apply all operations
                    for op in transaction._operations:
                        encoded_key = self.codec.encode_key(op.key)
                        if op.op_type == "set":
                            encoded_value = self.codec.encode_value(op.value)
                            self._data[encoded_key] = encoded_value
                        elif op.op_type == "delete":
                            self._data.pop(encoded_key, None)

                    # Save changes
                    await self._save()

                    # Remove from active transactions
                    self._active_transactions.discard(transaction)

                except Exception as e:
                    # Attempt rollback
                    try:
                        await transaction.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Failed to rollback transaction: {rollback_error}")
                    raise TransactionError(f"Failed to apply transaction: {e}")


class FileStorageTransaction(TransactionProtocol[FileStorageKey, FileStorageValue]):
    """Implementation of transaction for file-based storage."""

    def __init__(self, storage: FileStorage):
        """Initialize transaction."""
        self._storage = storage
        self._operations: list[TransactionOperation] = []
        self._read_set: set[str] = set()
        self._write_set: set[str] = set()
        self._committed = False
        self._rolled_back = False

    def _check_valid(self) -> None:
        """Check if transaction is still valid."""
        if self._committed:
            raise TransactionInvalidError("Transaction already committed")
        if self._rolled_back:
            raise TransactionInvalidError("Transaction already rolled back")

    async def get(self, key: FileStorageKey) -> FileStorageValue:
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
        value = await self._storage.get(key)
        self._read_set.add(encoded_key)
        return value

    async def set(self, key: FileStorageKey, value: FileStorageValue) -> None:
        """Set value within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("set", key, value))

    async def delete(self, key: FileStorageKey) -> None:
        """Delete key within transaction context."""
        self._check_valid()
        encoded_key = self._storage.codec.encode_key(key)
        self._write_set.add(encoded_key)
        self._operations.append(TransactionOperation("delete", key))

    async def exists(self, key: FileStorageKey) -> bool:
        """Check if key exists within transaction context."""
        self._check_valid()
        try:
            await self.get(key)
            return True
        except StorageKeyError:
            return False

    async def list_keys(
        self, prefix: FileStorageKey, depth: int = 1
    ) -> AsyncGenerator[FileStorageKey, None]:
        """List all keys under prefix within transaction."""
        self._check_valid()

        # Get snapshot of keys, considering transaction changes
        encoded_prefix = self._storage.codec.encode_key(prefix)

        # Get current keys from storage
        base_keys = set()
        async for key in self._storage.list_keys(prefix, depth):
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

    async def commit(self) -> None:
        """Commit transaction changes."""
        self._check_valid()
        await self._storage._apply_transaction(self)
        self._committed = True

    async def rollback(self) -> None:
        """Roll back transaction changes."""
        self._check_valid()
        self._rolled_back = True
        self._operations.clear()
        self._read_set.clear()
        self._write_set.clear()
