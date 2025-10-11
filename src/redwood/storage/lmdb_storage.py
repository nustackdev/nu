"""LMDB storage backend with transaction and snapshot support."""

from __future__ import annotations

import sys
import threading
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, TypeGuard
from uuid import uuid4

import attrs
import lmdb
from frozendict import frozendict
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


class LMDBStorage(BaseStorage[bytes, bytes]):
    """LMDB storage implementation with transaction support.

    Uses memory-mapped files for high performance and ACID guarantees.
    """

    codec: StorageCodecProtocol[bytes, bytes] = Attach()

    spec: LMDBStorageSpec

    def setup(self) -> None:
        """Initialize LMDB storage with environment setup."""
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

    def cleanup(self) -> None:
        """Clean up LMDB resources."""
        super().cleanup()

        if self._data_lock.locked():
            self._data_lock.release()
        self._active_transactions.clear()

    def _validate_value(self, value: Value) -> TypeGuard[Value]:
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

            logger.debug("Disconnected from LMDB")

    def _get_impl(self, key: Key) -> Value:
        """Get value by key."""
        try:
            encoded_key = self.codec.encode_key(key)

            with self._env.begin() as txn:
                cursor = txn.cursor()
                if cursor.set_key(encoded_key):
                    encoded_value = cursor.value()
                else:
                    raise StorageKeyError(f"Key {key} not found")

                if not isinstance(encoded_value, bytes):
                    raise StorageError(f"LMDB returned non-bytes value: {type(encoded_value)}")

                return self.codec.decode_value(encoded_value)

        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}") from e

    def _set_impl(self, key: Key, value: Value) -> None:
        """Set value for key."""
        # Encode both before transaction to avoid partial failure
        encoded_key = self.codec.encode_key(key)
        encoded_value = self.codec.encode_value(value)

        try:
            with self._env.begin(write=True) as txn:
                txn.put(encoded_key, encoded_value)

        except Exception as e:
            raise StorageOperationError(f"Failed to set key {key}: {e}") from e

    def _delete_impl(self, key: Key) -> None:
        """Delete value by key."""
        encoded_key = self.codec.encode_key(key)

        try:
            with self._env.begin(write=True) as txn:
                # Delete the key
                if not txn.delete(encoded_key):
                    raise StorageKeyError(f"Key {key} not found")
        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

    def _exists_impl(self, key: Key) -> bool:
        """Check if key exists."""
        encoded_key = self.codec.encode_key(key)

        try:
            with self._env.begin() as txn:
                cursor = txn.cursor()
                return cursor.set_key(encoded_key)

        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def _list_keys_impl(self, prefix: Key, depth: int) -> Generator[Key, None, None]:
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
                            # Skip this key but continue iteration
                            if not cursor.next():
                                break
                            continue

                        yield decoded_key

                        if not cursor.next():
                            break
                finally:
                    cursor.close()

        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

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
            raise StorageError(f"Failed to begin transaction: {e}") from e

    def _begin_snapshot_impl(
        self,
    ) -> LMDBStorageSnapshot:
        """Begin a new read-only snapshot."""
        try:
            # Start read-only LMDB transaction
            lmdb_txn = self._env.begin(write=False)

            # Create snapshot wrapper
            snapshot = LMDBStorageSnapshot(self, lmdb_txn)

            return snapshot

        except Exception as e:
            raise StorageError(f"Failed to begin snapshot: {e}") from e


class LMDBStorageTransaction:
    """LMDB transaction implementation with proper resource management."""

    def __init__(self, storage: LMDBStorage, txn: lmdb.Transaction) -> None:
        """Initialize transaction with LMDB txn."""
        self._storage = storage
        self._lmdb_txn = txn
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
        try:
            encoded_key = self._storage.codec.encode_key(key)

            cursor = self._lmdb_txn.cursor()
            if cursor.set_key(encoded_key):
                encoded_value = cursor.value()
            else:
                raise StorageKeyError(f"Key {key} not found")

            if not isinstance(encoded_value, bytes):
                raise StorageError(f"LMDB returned non-bytes value: {type(encoded_value)}")

            return self._storage.codec.decode_value(encoded_value)

        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}") from e

    def set(self, key: Key, value: Value) -> None:
        """Set value within transaction context."""
        self._check_valid()

        # Encode both before operation to avoid partial failure
        encoded_key = self._storage.codec.encode_key(key)
        encoded_value = self._storage.codec.encode_value(value)

        try:
            self._lmdb_txn.put(encoded_key, encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to set key {key}: {e}") from e

    def delete(self, key: Key) -> None:
        """Delete key within transaction context."""
        self._check_valid()

        encoded_key = self._storage.codec.encode_key(key)

        try:
            if not self._lmdb_txn.delete(encoded_key):
                raise StorageKeyError(f"Key {key} not found")
        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

    def exists(self, key: Key) -> bool:
        """Check if key exists within transaction context."""
        self._check_valid()

        encoded_key = self._storage.codec.encode_key(key)

        try:
            cursor = self._lmdb_txn.cursor()
            return cursor.set_key(encoded_key)

        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def list_keys(self, prefix: Key, depth: int = 1) -> Generator[Key, None, None]:
        """List all keys under prefix within transaction context."""
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
                        # Skip this key but continue iteration
                        if not cursor.next():
                            break
                        continue

                    yield decoded_key

                    if not cursor.next():
                        break
            finally:
                cursor.close()
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

    def commit(self) -> None:
        """Commit transaction changes."""
        self._check_valid()
        try:
            self._lmdb_txn.commit()
            self._committed = True
            with self._storage._data_lock:
                self._storage._active_transactions.discard(self)
        except Exception as e:
            raise TransactionError(f"Failed to commit transaction: {e}") from e

    def rollback(self) -> None:
        """Roll back transaction changes."""
        self._check_valid()
        try:
            self._lmdb_txn.abort()
            self._rolled_back = True
            with self._storage._data_lock:
                self._storage._active_transactions.discard(self)
        except Exception as e:
            raise TransactionError(f"Failed to rollback transaction: {e}") from e

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self._uuid == other._uuid


class LMDBStorageSnapshot:
    """LMDB read-only snapshot implementation."""

    def __init__(self, storage: LMDBStorage, txn: lmdb.Transaction) -> None:
        """Initialize snapshot with read-only LMDB txn."""
        self._storage = storage
        self._lmdb_txn = txn
        self._closed = False
        self._uuid = uuid4()

    def _check_valid(self) -> None:
        """Check if snapshot is still valid."""
        if self._closed:
            raise SnapshotError("Snapshot already closed")

    def get(self, key: Key) -> Value:
        """Get value within snapshot context."""
        self._check_valid()
        try:
            encoded_key = self._storage.codec.encode_key(key)

            cursor = self._lmdb_txn.cursor()
            if cursor.set_key(encoded_key):
                encoded_value = cursor.value()
            else:
                raise StorageKeyError(f"Key {key} not found")

            if not isinstance(encoded_value, bytes):
                raise StorageError(f"LMDB returned non-bytes value: {type(encoded_value)}")

            return self._storage.codec.decode_value(encoded_value)

        except StorageKeyError:
            raise
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}") from e

    def exists(self, key: Key) -> bool:
        """Check if key exists within snapshot context."""
        self._check_valid()

        encoded_key = self._storage.codec.encode_key(key)

        try:
            cursor = self._lmdb_txn.cursor()
            return cursor.set_key(encoded_key)

        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def list_keys(self, prefix: Key, depth: int = 1) -> Generator[Key, None, None]:
        """List all keys under prefix within snapshot context."""
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
                        # Skip this key but continue iteration
                        if not cursor.next():
                            break
                        continue

                    yield decoded_key

                    if not cursor.next():
                        break
            finally:
                cursor.close()
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

    def close(self) -> None:
        """Close snapshot and clean up resources."""
        if not self._closed:
            try:
                self._lmdb_txn.abort()  # Read-only transaction, just abort
            finally:
                self._closed = True

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self._uuid == other._uuid


@attrs.define(frozen=True, slots=True, kw_only=True)
class LMDBStorageSpec(ResourceSpec):
    """Specification for LMDBStorage resource."""

    name: str = "lmdb_storage"
    factory: type = LMDBStorage
    mode: str = "write"
    path: Path | str = Path(".db")
    codec: Spec
    map_size: int = 10 * 1024 * 1024 * 1024  # 10GB default
    max_dbs: int = 0
    lmdb_kwargs: frozendict = attrs.field(factory=frozendict)


if TYPE_CHECKING:
    _: type[StorageProtocol] = LMDBStorage
    __: type[TransactionProtocol] = LMDBStorageTransaction
    ___: type[SnapshotProtocol] = LMDBStorageSnapshot
