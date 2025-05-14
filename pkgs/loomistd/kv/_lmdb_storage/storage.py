from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Generator, TypeGuard

import lmdb

from loomi.attr import UseService
from loomi.interfaces.state.kv import SyncStorageProtocol, SyncTransactionProtocol
from loomi.service import SyncService
from loomi.spec import Spec, SpecField
from loomistd.codec import CodecProtocol
from loomistd.codec.binary import BinaryCodecSpec

from .._base import BaseStorage
from .._exceptions import (
    StorageError,
    StorageKeyError,
    StorageOperationError,
    TransactionError,
    TransactionInvalidError,
)
from .logger import logger
from .types import LMDBStorageEncodedKey, LMDBStorageEncodedValue, LMDBStorageKey, LMDBStorageValue

__all__ = [
    "LMDBStorage",
    "LMDBStorageSpec",
    "LMDBStorageTransaction",
]


class LMDBStorage(
    BaseStorage[
        LMDBStorageKey,
        LMDBStorageValue,
        LMDBStorageEncodedKey,
        LMDBStorageEncodedValue,
    ],
    SyncService,
):
    """
    LMDB storage implementation with transaction support.

    Uses memory-mapped files for high performance and ACID guarantees.
    """

    codec_srv: CodecProtocol[
        LMDBStorageKey, LMDBStorageValue, LMDBStorageEncodedKey, LMDBStorageEncodedValue
    ] = UseService()

    spec: LMDBStorageSpec

    def setup(self):
        self.path = (
            self.spec.path.resolve()
            if isinstance(self.spec.path, Path)
            else Path(self.spec.path).resolve()
        )

        if self.spec.map_size <= 0:
            raise ValueError("Map size must be positive")
        if self.spec.map_size > sys.maxsize:
            raise ValueError("Map size too large for platform")

        self._env: lmdb.Environment
        self._data_lock = threading.Lock()
        self._active_transactions: set[LMDBStorageTransaction] = set()

        super().setup()

    def cleanup(self):
        super().cleanup()

        if self._data_lock.locked():
            self._data_lock.release()
        self._active_transactions.clear()

    def _validate_value(self, value: LMDBStorageValue) -> TypeGuard[LMDBStorageValue]:
        return True

    def _connect_impl(self) -> None:
        """Initialize LMDB environment."""

        # Ensure directory exists
        self.path.mkdir(parents=True, exist_ok=True)

        with self._data_lock:
            # Open LMDB environment
            self._env = lmdb.open(
                str(self.path),
                map_size=self.spec.map_size,
                max_dbs=self.spec.max_dbs,
                readonly=self.mode == "read",
                **self.spec.lmdb_kwargs,
            )
            logger.debug(f"Connected to LMDB at {self.path} in {self.mode} mode")

    def _disconnect_impl(self) -> None:
        """Close LMDB environment."""
        with self._data_lock:
            # Roll back any active transactions
            for transaction in self._active_transactions.copy():
                try:
                    transaction.rollback()
                except Exception as e:
                    logger.error(f"Failed to rollback transaction during disconnect: {e}")

            if self._env is not None:
                try:
                    self._env.close()
                finally:
                    del self._env

            self._connected = False
            logger.debug("Disconnected from LMDB")

    def _get_impl(self, key: LMDBStorageKey) -> LMDBStorageValue:
        """Get value by key."""
        try:
            encoded_key = self.codec.encode_key(key)

            with self._env.begin() as txn:
                encoded_value = txn.get(encoded_key, None)

                if encoded_value is None:
                    raise StorageKeyError(f"Key {key} not found")

                if not isinstance(encoded_value, bytes):
                    raise StorageError(f"LMDB returned non-bytes value: {type(encoded_value)}")

                return self.codec.decode_value(encoded_value)

        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}")

    def _set_impl(self, key: LMDBStorageKey, value: LMDBStorageValue) -> None:
        """Set value for key."""
        # Encode both before transaction to avoid partial failure
        encoded_key = self.codec.encode_key(key)
        encoded_value = self.codec.encode_value(value)

        try:
            with self._env.begin(write=True) as txn:
                txn.put(encoded_key, encoded_value)

        except Exception as e:
            raise StorageOperationError(f"Failed to set key {key}: {e}")

    def _delete_impl(self, key: LMDBStorageKey) -> None:
        """Delete value by key."""
        encoded_key = self.codec.encode_key(key)

        try:
            with self._env.begin(write=True) as txn:
                # Check if key exists before deleting
                if txn.get(encoded_key) is None:
                    raise StorageKeyError(f"Key {key} not found")
                # Delete the key
                txn.delete(encoded_key)

        except Exception as e:
            raise StorageOperationError(f"Failed to delete key {key}: {e}")

    def _exists_impl(self, key: LMDBStorageKey) -> bool:
        """Check if key exists."""
        encoded_key = self.codec.encode_key(key)

        try:
            with self._env.begin() as txn:
                return txn.get(encoded_key) is not None

        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}")

    def _list_keys_impl(
        self, prefix: LMDBStorageKey, depth: int
    ) -> Generator[LMDBStorageKey, None]:
        """List all keys under prefix."""
        encoded_prefix = self.codec.encode_key(prefix)

        try:
            with self._env.begin() as txn:
                cursor = txn.cursor()

                try:
                    # Position cursor at first matching key
                    found = cursor.set_range(encoded_prefix)
                    if not found:
                        return

                    while True:
                        encoded_key = cursor.key()

                        # Check if we've moved past prefix
                        if not encoded_key.startswith(encoded_prefix):
                            break

                        decoded_key = self.codec.decode_key(encoded_key)
                        if depth != -1 and len(decoded_key) - len(prefix) != depth:
                            break

                        yield decoded_key

                        if not cursor.next():
                            break
                finally:
                    cursor.close()

        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}")

    def _begin_transaction_impl(
        self,
    ) -> LMDBStorageTransaction:
        """Begin a new transaction."""
        try:
            # Start LMDB transaction
            lmdb_txn = self._env.begin(write=True)

            # Create and track our transaction wrapper
            transaction = LMDBStorageTransaction(self, lmdb_txn)
            with self._data_lock:
                self._active_transactions.add(transaction)

            return transaction

        except Exception as e:
            raise StorageError(f"Failed to begin transaction: {e}")


class LMDBStorageTransaction(SyncTransactionProtocol[LMDBStorageValue]):
    """LMDB transaction implementation with proper resource management."""

    def __init__(self, storage: LMDBStorage, txn: lmdb.Transaction):
        """Initialize transaction with LMDB txn."""
        self._storage = storage
        self._lmdb_txn = txn
        self._committed = False
        self._rolled_back = False

    def _check_valid(self) -> None:
        """Check if transaction is still valid."""
        if self._committed:
            raise TransactionInvalidError("Transaction already committed")
        if self._rolled_back:
            raise TransactionInvalidError("Transaction already rolled back")

    def get(self, key: LMDBStorageKey) -> LMDBStorageValue:
        """Get value within transaction context."""
        self._check_valid()
        try:
            encoded_key = self._storage.codec.encode_key(key)
            encoded_value = self._lmdb_txn.get(encoded_key, None)

            if encoded_value is None:
                raise StorageKeyError(f"Key {key} not found")

            if not isinstance(encoded_value, bytes):
                raise StorageError(f"LMDB returned non-bytes value: {type(encoded_value)}")

            return self._storage.codec.decode_value(encoded_value)

        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}")

    def set(self, key: LMDBStorageKey, value: LMDBStorageValue) -> None:
        """Set value within transaction context."""
        self._check_valid()

        # Encode both before operation to avoid partial failure
        encoded_key = self._storage.codec.encode_key(key)
        encoded_value = self._storage.codec.encode_value(value)

        try:
            self._lmdb_txn.put(encoded_key, encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to set key {key}: {e}")

    def delete(self, key: LMDBStorageKey) -> None:
        """Delete key within transaction context."""
        self._check_valid()

        encoded_key = self._storage.codec.encode_key(key)

        try:
            self._lmdb_txn.delete(encoded_key)
        except Exception as e:
            raise StorageOperationError(f"Failed to delete key {key}: {e}")

    def exists(self, key: LMDBStorageKey) -> bool:
        """Check if key exists within transaction context."""
        self._check_valid()

        encoded_key = self._storage.codec.encode_key(key)

        try:
            return self._lmdb_txn.get(encoded_key) is not None
        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}")

    def list_keys(self, prefix: LMDBStorageKey, depth: int = 1) -> Generator[LMDBStorageKey, None]:
        self._check_valid()
        encoded_prefix = self._storage.codec.encode_key(prefix)

        try:
            cursor = self._lmdb_txn.cursor()
            try:
                found = cursor.set_range(encoded_prefix)
                if not found:
                    return
                while True:
                    encoded_key = cursor.key()
                    if not encoded_key.startswith(encoded_prefix):
                        break

                    decoded_key = self._storage.codec.decode_key(encoded_key)
                    if depth != -1 and len(decoded_key) - len(prefix) != depth:
                        break

                    yield decoded_key

                    if not cursor.next():
                        break
            finally:
                cursor.close()
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}")

    def commit(self) -> None:
        """Commit transaction changes."""
        self._check_valid()
        try:
            self._lmdb_txn.commit()
            self._committed = True
            with self._storage._data_lock:
                self._storage._active_transactions.discard(self)
        except Exception as e:
            raise TransactionError(f"Failed to commit transaction: {e}")

    def rollback(self) -> None:
        """Roll back transaction changes."""
        self._check_valid()
        try:
            self._lmdb_txn.abort()
            self._rolled_back = True
            with self._storage._data_lock:
                self._storage._active_transactions.discard(self)
        except Exception as e:
            raise TransactionError(f"Failed to rollback transaction: {e}")


class LMDBStorageSpec(Spec):
    name: str = SpecField(default="lmdb_storage")
    factory: type = SpecField(default=LMDBStorage)
    mode: str = SpecField(default="write")
    path: Path | str = SpecField(default=Path(".db"))
    codec_srv: Spec = SpecField(default_factory=BinaryCodecSpec)
    map_size: int = SpecField(default=10 * 1024 * 1024 * 1024)  # 10GB default
    max_dbs: int = SpecField(default=0)
    lmdb_kwargs: dict = SpecField(default_factory=dict)


if TYPE_CHECKING:
    _: type[SyncStorageProtocol] = LMDBStorage
