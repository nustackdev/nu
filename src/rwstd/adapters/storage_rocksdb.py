"""RocksDB storage backend implementation.

This module provides a RocksDB-backed storage implementation conforming to
the Redwood storage protocol. It uses composition of base classes to build
transactions and snapshots with proper resource management and error handling.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from redwood.be import (
    CodecProtocol,
    ObserverProtocol,
    ScanProtocol,
    SnapshotProtocol,
    StorageClosedError,
    StorageDeleteError,
    StorageError,
    StorageKeyError,
    StorageOperationError,
    StorageScanOptions,
    StorageTransactionAbortedError,
    StorageTransactionError,
    SubscriptionProtocol,
    TransactionProtocol,
    WriteBatchProtocol,
)
from rwstd.lazy_import import lazy_import


if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterator

    import rwrocks as _rwrocks  # type: ignore[import]
    from redwood.abc import CallbackFn, TupleKey, Value


rwrocks = cast(
    "_rwrocks",
    lazy_import("rwrocks", "rwrocks is required for RocksDBStorage."),
)


__all__ = [
    "RocksDBScan",
    "RocksDBSnapshot",
    "RocksDBStorage",
    "RocksDBTransaction",
]


# =============================================================================
# Base Context Class
# =============================================================================


class _RocksDBContextBase:
    """Base class for RocksDB transaction/snapshot contexts.

    Provides common functionality for state management, validation, and
    resource cleanup. All contexts wrap a RocksDB transaction handle.
    """

    def __init__(
        self,
        storage: RocksDBStorage,
        rwrocks_txn: rwrocks.Transaction,
    ) -> None:
        """Initialize context with storage reference and RocksDB transaction.

        Args:
            storage: Parent storage instance
            rwrocks_txn: RocksDB transaction handle
        """
        self._storage = storage
        self._rwrocks_txn: Any | None = rwrocks_txn
        self._closed = False
        self._uuid = uuid4()

    def _require_active(self) -> Any:
        """Validate context is active and return transaction handle.

        Returns:
            Active RocksDB transaction handle

        Raises:
            StorageClosedError: If context is closed or invalid
        """
        if self._closed:
            raise StorageClosedError("Context is closed")
        if self._rwrocks_txn is None:
            raise StorageClosedError("Context handle is invalid")
        return self._rwrocks_txn

    def _mark_closed(self) -> None:
        """Mark context as closed and clear handle."""
        self._closed = True
        self._rwrocks_txn = None

    @property
    def is_closed(self) -> bool:
        """Check if context is closed.

        Returns:
            True if closed, False otherwise.
        """
        return self._closed

    @property
    def is_active(self) -> bool:
        """Check if context is active.

        Returns:
            True if active and not closed, False otherwise.
        """
        return not self._closed

    def __hash__(self) -> int:
        """Hash based on unique identifier."""
        return hash(self._uuid)

    def __eq__(self, other: object) -> bool:
        """Compare contexts by UUID."""
        return isinstance(other, _RocksDBContextBase) and self._uuid == other._uuid


# =============================================================================
# Read Operations Mixin
# =============================================================================


class _ReadOperationsMixin:
    """Mixin providing read operations for RocksDB contexts.

    Implements point access (get, has), batch access (multiget),
    and range access (scan) operations.
    """

    # Type hints for mixed-in attributes
    _storage: RocksDBStorage
    _require_active: Any  # Method from _RocksDBContextBase

    def get(self, key: TupleKey, default: Value | None = None) -> Value:
        """Get value by key.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value at key, or default if not found

        Raises:
            StorageKeyError: If key not found and no default provided
            StorageOperationError: If operation fails
            StorageClosedError: If context is closed
        """
        txn = self._require_active()
        codec = self._storage.codec

        # Encode key for RocksDB
        try:
            encoded_key = codec.encode_key(key)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key {key}: {e}") from e

        # Retrieve from RocksDB
        try:
            with self._storage._db_lock:
                encoded_value = txn.get(encoded_key)
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}") from e

        # Handle not found
        if encoded_value is None:
            if default is not None:
                return default
            raise StorageKeyError(f"Key {key} not found")

        # Decode value
        try:
            return codec.decode_value(encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to decode value for key {key}: {e}") from e

    def has(self, key: TupleKey) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            StorageOperationError: If check fails
            StorageClosedError: If context is closed
        """
        txn = self._require_active()
        codec = self._storage.codec

        try:
            encoded_key = codec.encode_key(key)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key {key}: {e}") from e

        try:
            with self._storage._db_lock:
                return txn.get(encoded_key) is not None
        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def multiget(self, keys: list[TupleKey]) -> dict[TupleKey, Value]:
        """Get multiple keys.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dict mapping keys to values. Missing keys are omitted.

        Raises:
            StorageOperationError: If operation fails
            StorageClosedError: If context is closed
        """
        result: dict[TupleKey, Value] = {}

        for key in keys:
            try:
                value = self.get(key)
                result[key] = value
            except StorageKeyError:
                # Skip missing keys
                continue

        return result

    def scan(self, options: StorageScanOptions) -> ScanProtocol:
        """Create scan iterator with configured options.

        Args:
            options: Scan configuration (bounds, direction, limits)

        Returns:
            Scan iterator conforming to ScanProtocol

        Raises:
            StorageOperationError: If scan creation fails
            StorageClosedError: If context is closed
        """
        txn = self._require_active()

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
        except Exception as e:
            raise StorageOperationError(f"Failed to create scan iterator: {e}") from e

        return RocksDBScan(self._storage, iterator, options)

    ###### TEMP METHOD FOR COMPATIBILITY ######
    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        txn = self._require_active()
        codec = self._storage.codec
        encoded_prefix = codec.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                keys = _collect_prefixed_keys(
                    iterator,
                    encoded_prefix,
                    codec.decode_key,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

        yield from keys


###### TEMP METHOD FOR COMPATIBILITY ######
def _collect_prefixed_keys(
    iterator: Any,
    encoded_prefix: bytes,
    decode_key: Callable[[bytes], TupleKey],
    prefix: TupleKey,
    depth: int,
) -> list[TupleKey]:
    """Collect keys that match the encoded prefix using a RocksDB iterator."""
    keys: list[TupleKey] = []
    try:
        if encoded_prefix:
            iterator.seek(encoded_prefix)
        else:
            iterator.seek_to_first()

        while True:
            try:
                encoded_key, _ = iterator.get()
            except ValueError:
                break

            if not encoded_key.startswith(encoded_prefix):
                break

            decoded_key = decode_key(encoded_key)
            if depth == -1 or len(decoded_key) - len(prefix) == depth:
                keys.append(decoded_key)

            try:
                iterator.skip()
            except ValueError:
                break
    finally:
        # Ensure the underlying C++ iterator is released promptly.
        del iterator

    return keys


# =============================================================================
# Write Operations Mixin
# =============================================================================


class _WriteOperationsMixin:
    """Mixin providing write operations for RocksDB contexts.

    Implements point writes (put, delete) and range writes (range_delete).
    Tracks modified keys for notification on commit.
    """

    # Type hints for mixed-in attributes
    _storage: RocksDBStorage
    _require_active: Any  # Method from _RocksDBContextBase
    _modified_keys: set[TupleKey]  # Initialized in __init__

    def put(self, key: TupleKey, value: Value) -> None:
        """Put key-value pair.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If write fails
            StorageClosedError: If context is closed
        """
        txn = self._require_active()
        codec = self._storage.codec

        # Encode key and value
        try:
            encoded_key = codec.encode_key(key)
            encoded_value = codec.encode_value(value)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key/value for {key}: {e}") from e

        # Write to RocksDB
        try:
            with self._storage._db_lock:
                txn.put(encoded_key, encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to put key {key}: {e}") from e

        # Track modification for notifications
        self._modified_keys.add(key)

    def delete(self, key: TupleKey) -> bool:
        """Delete key.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            StorageDeleteError: If deletion fails
            StorageClosedError: If context is closed
        """
        txn = self._require_active()
        codec = self._storage.codec

        try:
            encoded_key = codec.encode_key(key)
        except Exception as e:
            raise StorageDeleteError(f"Failed to encode key {key}: {e}") from e

        # Check if key exists
        try:
            with self._storage._db_lock:
                exists = txn.get(encoded_key) is not None

                if not exists:
                    return False

                # Delete the key
                txn.delete_single(encoded_key)
        except Exception as e:
            raise StorageDeleteError(f"Failed to delete key {key}: {e}") from e

        # Track modification for notifications
        self._modified_keys.add(key)
        return True


# =============================================================================
# Transaction Control Mixin
# =============================================================================


class _TransactionControlMixin:
    """Mixin providing transaction control operations.

    Implements commit and abort operations with proper notification
    and cleanup handling.
    """

    # Type hints for mixed-in attributes
    _storage: RocksDBStorage
    _require_active: Any  # Method from _RocksDBContextBase
    _mark_closed: Any  # Method from _RocksDBContextBase
    _modified_keys: set[TupleKey]
    _committed: bool
    _aborted: bool

    def commit(self) -> None:
        """Commit all changes in the transaction.

        Sends notifications for all modified keys after successful commit.

        Raises:
            StorageTransactionError: If commit fails or transaction is invalid
            StorageClosedError: If context is closed
        """
        if self._committed:
            raise StorageTransactionError("Transaction already committed")
        if self._aborted:
            raise StorageTransactionError("Transaction already aborted")

        txn = self._require_active()

        # Commit to RocksDB
        try:
            with self._storage._db_lock:
                txn.commit()
        except Exception as e:
            raise StorageTransactionError(f"Failed to commit transaction: {e}") from e

        # Mark as committed before notifications
        self._committed = True
        self._mark_closed()

        # Notify observers of all modifications
        for key in self._modified_keys:
            self._storage._notify(key)

        # Remove from active transactions
        self._storage._remove_transaction(self)

    def abort(self) -> None:
        """Abort transaction and discard all changes.

        Raises:
            StorageTransactionAbortedError: If abort fails
            StorageClosedError: If context is closed
        """
        if self._committed:
            raise StorageTransactionError("Transaction already committed")
        if self._aborted:
            raise StorageTransactionError("Transaction already aborted")

        txn = self._require_active()

        try:
            with self._storage._db_lock:
                txn.rollback()
        except Exception as e:
            raise StorageTransactionAbortedError(f"Failed to abort transaction: {e}") from e
        finally:
            self._aborted = True
            self._mark_closed()
            self._storage._remove_transaction(self)


# =============================================================================
# Composed Classes
# =============================================================================


class RocksDBSnapshot(_RocksDBContextBase, _ReadOperationsMixin):
    """Read-only snapshot implementation.

    Provides consistent read-only view of the database at a point in time.
    Composed from base context and read operations.
    """

    @property
    def writable(self) -> bool:
        """Always False for snapshots."""
        return False

    def close(self) -> None:
        """Close snapshot and release resources.

        Raises:
            StorageError: If close fails
        """
        if self._closed:
            return

        if self._rwrocks_txn is not None:
            try:
                with self._storage._db_lock:
                    # Rollback to release the snapshot
                    self._rwrocks_txn.rollback()
            except Exception as e:
                raise StorageError(f"Failed to close snapshot: {e}") from e
            finally:
                self._mark_closed()
                self._storage._remove_snapshot(self)
        else:
            self._mark_closed()
            self._storage._remove_snapshot(self)

    def __enter__(self) -> RocksDBSnapshot:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager - auto close."""
        self.close()


class RocksDBTransaction(
    _RocksDBContextBase,
    _ReadOperationsMixin,
    _WriteOperationsMixin,
    _TransactionControlMixin,
):
    """Read-write transaction implementation.

    Provides full read-write access with ACID guarantees.
    Composed from base context, read operations, write operations,
    and transaction control.
    """

    def __init__(
        self,
        storage: RocksDBStorage,
        rwrocks_txn: rwrocks.Transaction,
    ) -> None:
        """Initialize transaction.

        Args:
            storage: Parent storage instance
            rwrocks_txn: RocksDB transaction handle
        """
        super().__init__(storage, rwrocks_txn)
        self._modified_keys: set[TupleKey] = set()
        self._committed = False
        self._aborted = False

    @property
    def writable(self) -> bool:
        """Always True for transactions."""
        return True

    def __enter__(self) -> RocksDBTransaction:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager - auto commit or abort.

        If an exception occurred, abort the transaction.
        Otherwise, commit the transaction.
        """
        if exc_type is not None:
            # Exception occurred - abort
            try:
                self.abort()
            except Exception:
                # Suppress abort errors if already handling exception
                pass
        else:
            # No exception - commit
            self.commit()


# =============================================================================
# Scan Iterator
# =============================================================================


class RocksDBScan:
    """Scan iterator implementation conforming to ScanProtocol.

    Provides Pythonic iteration interface over a range of keys.
    Handles bounds checking, direction, and limits.
    """

    def __init__(
        self,
        storage: RocksDBStorage,
        rwrocks_iterator: Any,
        options: StorageScanOptions,
    ) -> None:
        """Initialize scan iterator.

        Args:
            storage: Parent storage instance
            rwrocks_iterator: RocksDB iterator
            options: Scan configuration
        """
        self._storage = storage
        self._iterator = rwrocks_iterator
        self._options = options
        self._items: list[tuple[TupleKey, Value]] | None = None

    def _ensure_collected(self) -> list[tuple[TupleKey, Value]]:
        """Collect all items matching scan options.

        Lazily collects items on first access. Subsequent calls return
        cached results.

        Returns:
            List of (key, value) tuples
        """
        if self._items is not None:
            return self._items

        codec = self._storage.codec
        options = self._options
        items: list[tuple[TupleKey, Value]] = []

        try:
            # Validate length option
            if options.length == 0 or options.length < -1:
                raise StorageOperationError(f"Invalid scan length: {options.length}")

            # Encode bounds
            start_key = codec.encode_key(options.start) if options.start else b""
            end_key = codec.encode_key(options.end) if options.end else None

            # Seek to start position
            try:
                if start_key:
                    self._iterator.seek(start_key)
                else:
                    self._iterator.seek_to_first()
            except ValueError:
                # Iterator exhausted immediately
                self._items = []
                return self._items

            # Iterate through range
            while True:
                try:
                    encoded_key, encoded_value = self._iterator.get()
                except ValueError:
                    # Iterator exhausted
                    break

                # Decode key for bound checking
                try:
                    key = codec.decode_key(encoded_key)
                except Exception as e:
                    raise StorageOperationError(f"Failed to decode key: {e}") from e

                # Check end bound
                if end_key is not None:
                    if options.end_inclusive:
                        if encoded_key > end_key:
                            break
                    else:
                        if encoded_key >= end_key:
                            break

                # Check start bound (inclusive/exclusive)
                if options.start is not None:
                    if options.start_inclusive:
                        if key < options.start:
                            try:
                                self._iterator.skip()
                            except ValueError:
                                break
                            continue
                    else:
                        if key <= options.start:
                            try:
                                self._iterator.skip()
                            except ValueError:
                                break
                            continue

                # Length filter (if requested)
                if options.length == -1 or len(key) == options.length:
                    # Decode value only if key passes length filter
                    try:
                        value = codec.decode_value(encoded_value)
                    except Exception as e:
                        raise StorageOperationError(f"Failed to decode value: {e}") from e

                    items.append((key, value))

                # Check limit
                if options.limit is not None and len(items) >= options.limit:
                    break

                # Advance iterator
                try:
                    self._iterator.skip()
                except ValueError:
                    break

        except Exception as e:
            raise StorageOperationError(f"Failed during scan: {e}") from e
        finally:
            # Release iterator to free C++ resources
            del self._iterator

        # Apply reverse if requested
        if options.reverse:
            items.reverse()

        self._items = items
        return self._items

    def items(self) -> Iterator[tuple[TupleKey, Value]]:
        """Iterate over (key, value) tuples.

        Yields:
            Tuples of (key, value) for each item in scan range

        Raises:
            StorageOperationError: If iteration fails
        """
        yield from self._ensure_collected()

    def keys(self) -> Iterator[TupleKey]:
        """Iterate over keys only.

        Yields:
            Keys in scan range

        Raises:
            StorageOperationError: If iteration fails
        """
        for key, _ in self._ensure_collected():
            yield key

    def values(self) -> Iterator[Value]:
        """Iterate over values only.

        Yields:
            Values in scan range

        Raises:
            StorageOperationError: If iteration fails
        """
        for _, value in self._ensure_collected():
            yield value

    def __iter__(self) -> Iterator[TupleKey]:
        """Default iteration yields keys."""
        return self.keys()

    def __enter__(self) -> RocksDBScan:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        pass


# =============================================================================
# Main Storage Class
# =============================================================================


class RocksDBStorage:
    """RocksDB storage implementation conforming to StorageProtocol.

    Provides persistent key-value storage with transactions, snapshots,
    and optional change notifications via an observer.
    """

    def __init__(
        self,
        path: Path | str,
        codec: CodecProtocol[bytes, bytes],
        observer: ObserverProtocol[bytes] | None = None,
        *,
        wal_path: Path | str | None = None,
        options: dict[str, Any] | None = None,
        txn_db_options: dict[str, Any] | None = None,
        txn_options: dict[str, Any] | None = None,
        create_if_missing: bool = True,
        sync_writes: bool = False,
        disable_wal: bool = False,
    ) -> None:
        """Initialize RocksDB storage.

        Args:
            path: Database directory path
            codec: Codec for key/value encoding
            observer: Optional observer for change notifications
            wal_path: Optional separate WAL directory
            options: RocksDB options dict
            txn_db_options: TransactionDB options dict
            txn_options: Transaction options dict
            create_if_missing: Create database if it doesn't exist
            sync_writes: Sync writes to disk
            disable_wal: Disable write-ahead log
        """
        # Core dependencies
        self._codec = codec
        self._observer = observer

        # Paths
        self._path = Path(path) if isinstance(path, str) else path
        self._wal_path = Path(wal_path) if isinstance(wal_path, str) else wal_path

        # Configuration
        self._options_dict = options or {}
        self._txn_db_options_dict = txn_db_options or {}
        self._txn_options_dict = txn_options or {}
        self._create_if_missing = create_if_missing
        self._sync_writes = sync_writes
        self._disable_wal = disable_wal

        # State
        self._db: rwrocks.TransactionDB | None = None
        self._db_lock = threading.RLock()
        self._active_transactions: set[RocksDBTransaction] = set()
        self._active_snapshots: set[RocksDBSnapshot] = set()
        self._opened = False

        self._uuid = uuid4()

    def __hash__(self) -> int:
        return hash(self._uuid)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, RocksDBStorage) and self._uuid == value._uuid

    @property
    def codec(self) -> CodecProtocol[bytes, bytes]:
        """Get codec for key/value encoding."""
        return self._codec

    def open(self) -> None:
        """Open RocksDB database and initialize resources.

        Raises:
            StorageError: If database cannot be opened
        """
        if self._opened:
            return

        with self._db_lock:
            # Create directories
            try:
                self._path.mkdir(parents=True, exist_ok=True)
                if self._wal_path is not None:
                    self._wal_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise StorageError(f"Failed to create database directories: {e}") from e

            # Configure RocksDB options
            options_dict = dict(self._options_dict)
            if "create_if_missing" not in options_dict:
                options_dict["create_if_missing"] = self._create_if_missing

            try:
                options = rwrocks.Options(**options_dict)
            except Exception as e:
                raise StorageError(f"Invalid RocksDB options: {e}") from e

            if self._wal_path is not None:
                options.wal_dir = str(self._wal_path)

            # Configure TransactionDB options
            txn_db_options = None
            if self._txn_db_options_dict:
                try:
                    txn_db_options = rwrocks.TransactionDBOptions(**self._txn_db_options_dict)
                except Exception as e:
                    raise StorageError(f"Invalid TransactionDB options: {e}") from e

            # Open database
            try:
                self._db = rwrocks.TransactionDB(
                    str(self._path),
                    options,
                    txn_db_options,
                )
            except Exception as e:
                raise StorageError(f"Failed to open RocksDB database: {e}") from e

            self._opened = True

    def close(self) -> None:
        """Close database and release all resources.

        All active transactions are aborted and snapshots are closed.

        Raises:
            StorageError: If close fails
        """
        if not self._opened:
            return

        with self._db_lock:
            # Abort all active transactions
            for transaction in list(self._active_transactions):
                try:
                    transaction.abort()
                except Exception:
                    # Best effort cleanup
                    pass

            # Close all active snapshots
            for snapshot in list(self._active_snapshots):
                try:
                    snapshot.close()
                except Exception:
                    # Best effort cleanup
                    pass

            # Clear tracking sets
            self._active_transactions.clear()
            self._active_snapshots.clear()

            # Close database
            if self._db is not None:
                try:
                    self._db.close()
                except Exception as e:
                    raise StorageError(f"Failed to close database: {e}") from e
                finally:
                    self._db = None

            self._opened = False

    def subscribe(
        self,
        pattern: TupleKey,
        callback: CallbackFn,
        depth: int = 0,
    ) -> SubscriptionProtocol:
        """Subscribe to key pattern changes.

        Args:
            pattern: Key prefix pattern to match
            callback: Function called on matching mutations
            depth: Depth of pattern matching (0=exact, 1=prefix, -1=all subkeys)

        Returns:
            Subscription handle for unsubscribing

        Raises:
            StorageOperationError: If subscription fails
        """
        if self._observer is None:
            raise StorageOperationError("Observer not configured for this storage")

        try:
            return self._observer.subscribe(pattern, callback, depth)
        except Exception as e:
            raise StorageOperationError(f"Failed to subscribe: {e}") from e

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes.

        Args:
            subscription: Subscription from subscribe()

        Raises:
            StorageOperationError: If unsubscribe fails
        """
        if self._observer is None:
            raise StorageOperationError("Observer not configured for this storage")

        try:
            self._observer.unsubscribe(subscription)
        except Exception as e:
            raise StorageOperationError(f"Failed to unsubscribe: {e}") from e

    def begin(self, *, write: bool = False) -> TransactionProtocol | SnapshotProtocol:
        """Begin transaction or snapshot.

        Args:
            write: If True, begin read-write transaction; else read-only snapshot

        Returns:
            Transaction if write=True, Snapshot if write=False

        Raises:
            StorageError: If begin fails
            StorageClosedError: If storage is not open
        """
        if write:
            return self.begin_transaction()
        else:
            return self.begin_snapshot()

    def begin_snapshot(self) -> RocksDBSnapshot:
        """Begin read-only snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot creation fails
            StorageClosedError: If storage is not open
        """
        self._require_open()

        with self._db_lock:
            # Create transaction options with snapshot
            txn_options_dict = dict(self._txn_options_dict)
            txn_options_dict["set_snapshot"] = True

            try:
                txn_options = rwrocks.TransactionOptions(**txn_options_dict)
            except Exception as e:
                raise StorageError(f"Invalid snapshot options: {e}") from e

            # Begin transaction with snapshot
            try:
                rwrocks_txn = self._db.begin_transaction(txn_options)
                rwrocks_txn.set_snapshot()
            except Exception as e:
                raise StorageError(f"Failed to begin snapshot: {e}") from e

            snapshot = RocksDBSnapshot(self, rwrocks_txn)
            self._active_snapshots.add(snapshot)
            return snapshot

    def begin_transaction(self) -> RocksDBTransaction:
        """Begin read-write transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction creation fails
            StorageClosedError: If storage is not open
        """
        self._require_open()

        with self._db_lock:
            # Create transaction options
            txn_options = None
            if self._txn_options_dict:
                try:
                    txn_options = rwrocks.TransactionOptions(**self._txn_options_dict)
                except Exception as e:
                    raise StorageError(f"Invalid transaction options: {e}") from e

            # Begin transaction
            try:
                if txn_options is not None:
                    rwrocks_txn = self._db.begin_transaction(txn_options)
                else:
                    rwrocks_txn = self._db.begin_transaction()
            except Exception as e:
                raise StorageError(f"Failed to begin transaction: {e}") from e

            transaction = RocksDBTransaction(self, rwrocks_txn)
            self._active_transactions.add(transaction)
            return transaction

    def begin_write_batch(self) -> WriteBatchProtocol:
        """Begin write-only batch.

        Not implemented for RocksDB storage.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Write batches not supported by RocksDB storage")

    @contextmanager
    def transaction(self) -> Iterator[RocksDBTransaction]:
        """Context manager for a read-write transaction.

        Begins a transaction, yields it to the caller, and commits on successful
        exit. If an exception is raised inside the context, the transaction is
        aborted. Best-effort cleanup is used for abort/commit errors.
        """
        txn = self.begin_transaction()
        try:
            yield txn
            # If caller didn't already commit/abort, commit now.
            if not txn._committed and not txn._aborted:
                txn.commit()
        except Exception:
            # On error, ensure transaction is aborted if not already finalized.
            try:
                if not txn._committed and not txn._aborted:
                    txn.abort()
            except Exception:
                # Best-effort cleanup; preserve original exception.
                pass
            raise

    @contextmanager
    def snapshot(self) -> Iterator[RocksDBSnapshot]:
        """Context manager for a read-only snapshot.

        Begins a snapshot and ensures it is closed on exit.
        """
        snap = self.begin_snapshot()
        try:
            yield snap
        finally:
            try:
                snap.close()
            except Exception:
                # Best-effort cleanup
                pass

    @contextmanager
    def write_batch(self) -> Iterator[WriteBatchProtocol]:
        """Context manager providing a write-batch-like interface.

        RocksDB write-batch is not implemented separately; use a transaction as a
        write batch. Commits on successful exit, aborts on exception.
        """
        # Use a transaction as a write-batch
        batch = self.begin_transaction()
        try:
            yield batch
            if not batch._committed and not batch._aborted:
                batch.commit()
        except Exception:
            try:
                if not batch._committed and not batch._aborted:
                    batch.abort()
            except Exception:
                pass
            raise

    def _notify(self, key: TupleKey) -> None:
        """Notify observer of key change.

        Args:
            key: Key that changed
        """
        if self._observer is not None:
            try:
                self._observer.notify(key)
            except Exception:
                # Best effort notification - don't fail transaction
                pass

    def _remove_transaction(self, transaction: RocksDBTransaction) -> None:
        """Remove transaction from active set.

        Args:
            transaction: Transaction to remove
        """
        self._active_transactions.discard(transaction)

    def _remove_snapshot(self, snapshot: RocksDBSnapshot) -> None:
        """Remove snapshot from active set.

        Args:
            snapshot: Snapshot to remove
        """
        self._active_snapshots.discard(snapshot)

    def _require_open(self) -> None:
        """Validate storage is open.

        Raises:
            StorageClosedError: If storage is not open
        """
        if not self._opened or self._db is None:
            raise StorageClosedError("Storage is not open")

    def __enter__(self) -> RocksDBStorage:
        """Enter context manager - open storage."""
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager - close storage."""
        self.close()


if TYPE_CHECKING:
    _: type[TransactionProtocol] = RocksDBTransaction
    __: type[SnapshotProtocol] = RocksDBSnapshot
