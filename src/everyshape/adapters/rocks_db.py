"""RocksDB storage backend implementation - OPTIMIZED SCAN.

Key optimization: RocksDBScan now uses lazy iteration and only decodes what's requested:
- keys() only decodes keys (no value decoding)
- values() only decodes values
- items() decodes both

This eliminates wasteful operations when only keys or values are needed.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from enum import Enum, auto
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast, overload
from uuid import uuid4

from everyshape.storage import (
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
    Subscription,
    TransactionProtocol,
    WriteBatchProtocol,
)
from everyshape.utils.lazy_import import lazy_import


if TYPE_CHECKING:
    from collections.abc import Generator, Iterator
    from types import TracebackType

    import esrocks as _esrocks  # type: ignore[import]
    from everyshape.loc.key import Key
    from everyshape.storage import SubscriptionOptions
    from everyshape.types import Value


esrocks = cast(
    "_esrocks",
    lazy_import("esrocks", "esrocks is required for RocksDBStorage."),
)


__all__ = [
    "RocksDBScan",
    "RocksDBSnapshot",
    "RocksDBStorage",
    "RocksDBTransaction",
]


logger = getLogger(__name__)


# =============================================================================
# Types
# =============================================================================


class IteratorType(Enum):
    KEYS = auto()
    VALUES = auto()
    ITEMS = auto()


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
        esrocks_txn: esrocks.Transaction,
    ) -> None:
        """Initialize context with storage reference and RocksDB transaction.

        Args:
            storage: Parent storage instance
            esrocks_txn: RocksDB transaction handle
        """
        self._storage = storage
        self._esrocks_txn: Any | None = esrocks_txn
        self._closed = False
        self._uuid = uuid4()

    def _require_active(self) -> object:
        """Validate context is active and return transaction handle.

        Returns:
            Active RocksDB transaction handle

        Raises:
            StorageClosedError: If context is closed or invalid
        """
        if self._closed:
            raise StorageClosedError("Context is closed")
        if self._esrocks_txn is None:
            raise StorageClosedError("Context handle is invalid")
        return self._esrocks_txn

    def _mark_closed(self) -> None:
        """Mark context as closed and clear handle."""
        self._closed = True
        self._esrocks_txn = None

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
# Operation Mixins
# =============================================================================


class _ReadOperationsMixin:
    """Mixin providing read operations for RocksDB contexts.

    Implements point access (get, has), batch access (multiget),
    and range access (scan) operations.
    """

    # Type hints for mixed-in attributes
    _storage: RocksDBStorage
    _require_active: Any  # Method from _RocksDBContextBase

    def get(self, key: Key) -> Value:
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
            encoded_value = txn.get(encoded_key)
        except Exception as e:
            raise StorageOperationError(f"Failed to get key {key}: {e}") from e

        # Handle not found
        if encoded_value is None:
            raise StorageKeyError(f"Key {key} not found")

        # Decode value
        try:
            return codec.decode_value(encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to decode value for key {key}: {e}") from e

    def has(self, key: Key) -> bool:
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
            return txn.get(encoded_key) is not None
        except Exception as e:
            raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def multiget(self, keys: list[Key]) -> dict[Key, Value]:
        """Get multiple keys.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dict mapping keys to values. Missing keys are omitted.

        Raises:
            StorageOperationError: If operation fails
            StorageClosedError: If context is closed
        """
        result: dict[Key, Value] = {}

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
        # Don't create iterator yet - let keys()/values()/items() create
        # the appropriate iterator type (iterkeys vs iteritems)
        return RocksDBScan(self, options)


class _WriteOperationsMixin:
    """Mixin providing write operations for RocksDB contexts.

    Implements point writes (put, delete) and range writes (range_delete).
    Tracks modified keys for notification on commit.
    """

    # Type hints for mixed-in attributes
    _storage: RocksDBStorage
    _require_active: Any  # Method from _RocksDBContextBase
    _modified_keys: set[Key]  # Initialized in __init__

    def put(self, key: Key, value: Value) -> None:
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
            txn.put(encoded_key, encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to put key {key}: {e}") from e

        # Track modification for notifications
        self._modified_keys.add(key)

    def delete(self, key: Key) -> bool:
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
# Composed Classes
# =============================================================================


class RocksDBSnapshot(
    _RocksDBContextBase,
    _ReadOperationsMixin,
):
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

        if self._esrocks_txn is not None:
            try:
                # Rollback to release the snapshot
                self._esrocks_txn.rollback()
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

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager - auto close."""
        self.close()


class RocksDBWriteBatch(
    _RocksDBContextBase,
):
    """Write-only batch implementation for RocksDB.

    Provides efficient bulk write operations using esrocks.WriteBatch.
    Does not support read operations - optimized for write-heavy workloads.
    """

    def __init__(
        self,
        storage: RocksDBStorage,
        esrocks_batch: esrocks.WriteBatch,
    ) -> None:
        """Initialize write batch.

        Args:
            storage: Parent storage instance
            esrocks_batch: RocksDB write batch handle
        """
        super().__init__(storage, esrocks_batch)
        self._modified_keys: set[Key] = set()
        self._written = False
        self._aborted = False

    @property
    def writable(self) -> bool:
        """Always True for write batches."""
        return True

    def put(self, key: Key, value: Value) -> None:
        """Put key-value pair into batch.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If write fails
            StorageClosedError: If batch is closed
        """
        batch = self._require_active()
        codec = self._storage.codec

        # Encode key and value
        try:
            encoded_key = codec.encode_key(key)
            encoded_value = codec.encode_value(value)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key/value for {key}: {e}") from e

        # Add to batch
        try:
            batch.put(encoded_key, encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to put key {key}: {e}") from e

        # Track modification for notifications
        self._modified_keys.add(key)

    def delete(self, key: Key) -> bool:
        """Delete key from batch.

        Note: Since WriteBatch is write-only, this checks existence by
        reading from storage. For pure write-only semantics without reads,
        use this method only when you know the key exists.

        Args:
            key: Key to delete

        Returns:
            True if key existed in storage, False otherwise

        Raises:
            StorageDeleteError: If deletion fails
            StorageClosedError: If batch is closed
        """
        batch = self._require_active()
        codec = self._storage.codec

        try:
            encoded_key = codec.encode_key(key)
        except Exception as e:
            raise StorageDeleteError(f"Failed to encode key {key}: {e}") from e

        # Check if key exists in storage via snapshot
        # This is necessary to return accurate True/False per protocol
        try:
            exists = self._storage._db.get(encoded_key) is not None

            if not exists:
                return False

            # Add delete to batch
            batch.delete(encoded_key)
        except Exception as e:
            raise StorageDeleteError(f"Failed to delete key {key}: {e}") from e

        # Track modification for notifications
        self._modified_keys.add(key)
        return True

    def write(self) -> None:
        """Write batch and make changes permanent.

        Sends notifications for all modified keys after successful write.

        Raises:
            StorageTransactionError: If write fails
            StorageClosedError: If already written or aborted
        """
        if self._closed:
            logger.error("Cannot write, batch is closed", extra={"batch_id": str(self._uuid)})
            raise StorageClosedError("Write batch is closed")
        if self._written:
            logger.error("Cannot write, batch already written", extra={"batch_id": str(self._uuid)})
            raise StorageTransactionError("Write batch already written")
        if self._aborted:
            logger.error("Cannot write, batch already aborted", extra={"batch_id": str(self._uuid)})
            raise StorageTransactionError("Write batch already aborted")

        batch = self._require_active()

        # Write to RocksDB
        try:
            self._storage._db.write(batch)
        except Exception as e:
            logger.error(
                "Write batch write failed",
                extra={"batch_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionError(f"Failed to write batch: {e}") from e

        logger.info(
            "Write batch written",
            extra={"batch_id": str(self._uuid), "modified_keys": len(self._modified_keys)},
        )

        # Mark as written before notifications
        self._written = True
        self._mark_closed()

        # Notify observers of all modifications
        for key in self._modified_keys:
            self._storage._notify(key)

        # Remove from active batches
        self._storage._remove_write_batch(self)

    def abort(self) -> None:
        """Abort write batch and discard changes.

        Raises:
            StorageTransactionError: If abort fails
            StorageClosedError: If batch is closed
        """
        if self._closed:
            # Already closed, nothing to do
            logger.debug("Abort called on closed write batch", extra={"batch_id": str(self._uuid)})
            return

        try:
            logger.info(
                "Write batch aborted",
                extra={"batch_id": str(self._uuid), "discarded_keys": len(self._modified_keys)},
            )

            self._aborted = True
            self._mark_closed()
            self._storage._remove_write_batch(self)
        except Exception as e:
            logger.error(
                "Write batch abort failed",
                extra={"batch_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionError(f"Failed to abort write batch: {e}") from e

    def __enter__(self) -> RocksDBWriteBatch:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager - auto write or abort.

        If an exception occurred, abort the batch.
        Otherwise, write the batch.
        """
        if exc_type is not None:
            # Exception occurred - abort
            try:
                self.abort()
            except Exception as e:
                logger.error(
                    "Write batch abort failed",
                    extra={"batch_id": str(self._uuid), "error": str(e)},
                    exc_info=True,
                )
        else:
            # No exception - write if not already done
            if not self._written and not self._aborted:
                self.write()


class RocksDBTransaction(
    _RocksDBContextBase,
    _ReadOperationsMixin,
    _WriteOperationsMixin,
):
    """Read-write transaction implementation.

    Provides full read-write access with ACID guarantees.
    Composed from base context, read operations, write operations,
    and transaction control.
    """

    def __init__(
        self,
        storage: RocksDBStorage,
        esrocks_txn: esrocks.Transaction,
    ) -> None:
        """Initialize transaction.

        Args:
            storage: Parent storage instance
            esrocks_txn: RocksDB transaction handle
        """
        super().__init__(storage, esrocks_txn)
        self._modified_keys: set[Key] = set()
        self._committed = False
        self._aborted = False

    @property
    def writable(self) -> bool:
        """Always True for transactions."""
        return True

    def __enter__(self) -> RocksDBTransaction:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager - auto commit or abort.

        If an exception occurred, abort the transaction.
        Otherwise, commit the transaction.
        """
        if exc_type is not None:
            # Exception occurred - abort
            try:
                self.abort()
            except Exception as e:
                logger.error(
                    "Transaction abort failed",
                    extra={"txn_id": str(self._uuid), "error": str(e)},
                    exc_info=True,
                )
        else:
            # No exception - commit
            self.commit()

    def commit(self) -> None:
        """Commit all changes in the transaction.

        Sends notifications for all modified keys after successful commit.

        Raises:
            StorageTransactionError: If commit fails or transaction is invalid
            StorageClosedError: If context is closed
        """
        if self._committed:
            logger.error(
                "Cannot commit, transaction already committed", extra={"txn_id": str(self._uuid)}
            )
            raise StorageTransactionError("Transaction already committed")
        if self._aborted:
            logger.error(
                "Cannot commit, transaction already aborted", extra={"txn_id": str(self._uuid)}
            )
            raise StorageTransactionError("Transaction already aborted")

        txn = self._require_active()

        # Commit to RocksDB
        try:
            txn.commit()
        except Exception as e:
            logger.error(
                "Transaction commit failed",
                extra={"txn_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionError(f"Failed to commit transaction: {e}") from e

        logger.info(
            "Transaction committed",
            extra={"txn_id": str(self._uuid), "modified_keys": len(self._modified_keys)},
        )

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
            logger.error(
                "Cannot abort, transaction already committed", extra={"txn_id": str(self._uuid)}
            )
            raise StorageTransactionError("Transaction already committed")
        if self._aborted:
            logger.error(
                "Cannot abort, transaction already aborted", extra={"txn_id": str(self._uuid)}
            )
            raise StorageTransactionError("Transaction already aborted")

        txn = self._require_active()

        try:
            txn.rollback()

            logger.info(
                "Transaction aborted",
                extra={"txn_id": str(self._uuid), "discarded_keys": len(self._modified_keys)},
            )
        except Exception as e:
            logger.error(
                "Transaction abort failed",
                extra={"txn_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionAbortedError(f"Failed to abort transaction: {e}") from e
        finally:
            self._aborted = True
            self._mark_closed()
            self._storage._remove_transaction(self)


# =============================================================================
# OPTIMIZED Scan Iterator
# =============================================================================


class RocksDBScan:
    """OPTIMIZED scan iterator implementation conforming to ScanProtocol.

    Provides Pythonic iteration interface over a range of keys.

    KEY OPTIMIZATIONS:
    1. Uses iterkeys() when only keys needed (no value I/O from disk)
    2. Uses iteritems() when values needed
    3. For reverse iteration, seeks to end and uses prev() instead of caching
    """

    def __init__(
        self,
        context: _ReadOperationsMixin,
        options: StorageScanOptions,
    ) -> None:
        """Initialize scan iterator.

        Args:
            context: Storage context (transaction/snapshot) with _require_active and _storage
            options: Scan configuration
        """
        self._context = context
        self._storage = context._storage
        self._options = options

    @overload
    def _iterate_impl(
        self, iterator_type: Literal[IteratorType.KEYS]
    ) -> Generator[Key, None, None]: ...

    @overload
    def _iterate_impl(
        self, iterator_type: Literal[IteratorType.VALUES]
    ) -> Generator[Value, None, None]: ...

    @overload
    def _iterate_impl(
        self, iterator_type: Literal[IteratorType.ITEMS]
    ) -> Generator[tuple[Key, Value], None, None]: ...

    def _iterate_impl(self, iterator_type: IteratorType) -> Generator[object, None, None]:
        """Core iteration implementation.

        Args:
            iterator_type: Use iteritems(), itervalues() or iterkeys().

        Yields:
            Tuples of (decoded_key, encoded_value_or_None)
        """
        txn = self._context._require_active()
        codec = self._storage.codec
        options = self._options

        # Create appropriate iterator based on what we need
        need_values = False
        try:
            if iterator_type == IteratorType.KEYS:
                iterator = txn.iterkeys()  # Read ONLY keys from disk
            elif iterator_type == IteratorType.VALUES or iterator_type == IteratorType.ITEMS:
                iterator = txn.iteritems()  # Read ONLY values from disk
                need_values = True
            else:
                raise ValueError("Unknown iterator_type argument")
        except Exception as e:
            raise StorageOperationError(f"Failed to create iterator: {e}") from e

        try:
            # Validate length option
            if options.length == 0 or options.length < -1:
                raise StorageOperationError(f"Invalid scan length: {options.length}")

            # Encode bounds
            start_key_encoded = codec.encode_key(options.start) if options.start else b""
            end_key_encoded = codec.encode_key(options.end) if options.end else None

            # Seek to start/end based on direction
            try:
                if options.reverse:
                    # Seek to end of range (or last key if no end bound)
                    if end_key_encoded:
                        iterator.seek(end_key_encoded)
                        # If end_inclusive, we're at the right spot
                        # If not end_inclusive, we need to be before end_key
                        if not options.end_inclusive:
                            try:
                                # Move to previous key
                                encoded_key = iterator.get()[0] if need_values else iterator.get()
                                if encoded_key >= end_key_encoded:
                                    iterator.skip_back()
                            except (ValueError, IndexError):
                                return
                    else:
                        iterator.seek_to_last()
                else:
                    # Forward: seek to start
                    if start_key_encoded:
                        iterator.seek(start_key_encoded)
                    else:
                        iterator.seek_to_first()
            except ValueError:
                # Iterator exhausted immediately
                return

            # Track count for limit
            count = 0

            # Iterate through range
            while True:
                try:
                    if need_values:
                        encoded_key, encoded_value = iterator.get()
                    else:
                        encoded_key = iterator.get()
                        encoded_value = None
                except (ValueError, IndexError):
                    # Iterator exhausted
                    break

                # Decode key (needed for filtering)
                try:
                    key = codec.decode_key(encoded_key)
                except Exception as e:
                    raise StorageOperationError(f"Failed to decode key: {e}") from e

                # Check bounds based on direction
                if options.reverse:
                    # Going backward - check start bound
                    if start_key_encoded:
                        if options.start_inclusive:
                            if encoded_key < start_key_encoded:
                                break
                        else:
                            if encoded_key <= start_key_encoded:
                                break
                else:
                    # Going forward - check end bound
                    if end_key_encoded is not None:
                        if options.end_inclusive:
                            if encoded_key > end_key_encoded:
                                break
                        else:
                            if encoded_key >= end_key_encoded:
                                break

                # Check start/end bound (for non-primary direction)
                if options.reverse:
                    # Already checked start bound above, check end bound
                    if end_key_encoded is not None:
                        if options.end_inclusive:
                            if encoded_key > end_key_encoded:
                                try:
                                    iterator.skip_back()
                                except ValueError:
                                    break
                                continue
                        else:
                            if encoded_key >= end_key_encoded:
                                try:
                                    iterator.skip_back()
                                except ValueError:
                                    break
                                continue
                else:
                    # Already checked end bound above, check start bound
                    if options.start is not None:
                        if options.start_inclusive:
                            if key < options.start:
                                try:
                                    iterator.skip()
                                except ValueError:
                                    break
                                continue
                        else:
                            if key <= options.start:
                                try:
                                    iterator.skip()
                                except ValueError:
                                    break
                                continue

                # Length filter
                if options.length != -1 and len(key) != options.length:
                    try:
                        if options.reverse:
                            iterator.skip_back()
                        else:
                            iterator.skip()
                    except ValueError:
                        break
                    continue

                # Yield result
                value = None
                if need_values and encoded_value:
                    # Decode value
                    try:
                        value = codec.decode_value(encoded_value)
                    except Exception as e:
                        raise StorageOperationError(f"Failed to decode value: {e}") from e

                if iterator_type == IteratorType.ITEMS:
                    yield (key, value)
                elif iterator_type == IteratorType.VALUES:
                    yield value
                elif iterator_type == IteratorType.KEYS:
                    yield key

                count += 1

                # Check limit
                if options.limit is not None and count >= options.limit:
                    break

                # Advance iterator
                try:
                    if options.reverse:
                        iterator.skip_back()
                    else:
                        iterator.skip()
                except ValueError:
                    break

        except Exception as e:
            raise StorageOperationError(f"Failed during scan: {e}") from e
        finally:
            # Release iterator to free C++ resources
            del iterator

    def keys(self) -> Generator[Key, None, None]:
        """Iterate over keys only - uses iterkeys() for minimal I/O.

        Yields:
            Keys in scan range

        Raises:
            StorageOperationError: If iteration fails
        """
        yield from self._iterate_impl(iterator_type=IteratorType.KEYS)

    def values(self) -> Generator[Value, None, None]:
        """Iterate over values only - must use iteritems().

        Yields:
            Values in scan range

        Raises:
            StorageOperationError: If iteration fails
        """
        yield from self._iterate_impl(iterator_type=IteratorType.VALUES)

    def items(self) -> Generator[tuple[Key, Value], None, None]:
        """Iterate over (key, value) tuples - uses iteritems().

        Yields:
            Tuples of (key, value) for each item in scan range

        Raises:
            StorageOperationError: If iteration fails
        """
        yield from self._iterate_impl(iterator_type=IteratorType.ITEMS)

    def __iter__(self) -> Iterator[Key]:
        """Default iteration yields keys."""
        return self.keys()

    def __enter__(self) -> RocksDBScan:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
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
        observer: ObserverProtocol | None = None,
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
        self._db: esrocks.TransactionDB | None = None
        self._db_lock = threading.RLock()
        self._active_transactions: set[RocksDBTransaction] = set()
        self._active_write_batches: set[RocksDBWriteBatch] = set()
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
                options = esrocks.Options(**options_dict)
            except Exception as e:
                raise StorageError(f"Invalid RocksDB options: {e}") from e

            if self._wal_path is not None:
                options.wal_dir = str(self._wal_path)

            # Configure TransactionDB options
            txn_db_options = None
            if self._txn_db_options_dict:
                try:
                    txn_db_options = esrocks.TransactionDBOptions(**self._txn_db_options_dict)
                except Exception as e:
                    raise StorageError(f"Invalid TransactionDB options: {e}") from e

            # Open database
            try:
                self._db = esrocks.TransactionDB(
                    str(self._path),
                    options,
                    txn_db_options,
                )
            except Exception as e:
                raise StorageError(f"Failed to open RocksDB database: {e}") from e

            self._opened = True

    def close(self) -> None:
        """Close database and release all resources.

        All active transactions and write batches are aborted, snapshots are closed.

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
                except Exception as e:
                    logger.error(
                        "Transaction abort failed",
                        extra={"txn_id": str(self._uuid), "error": str(e)},
                        exc_info=True,
                    )

            # Close all active snapshots
            for snapshot in list(self._active_snapshots):
                try:
                    snapshot.close()
                except Exception as e:
                    logger.error(
                        "Snapshot close failed",
                        extra={"snapshot_id": str(self._uuid), "error": str(e)},
                        exc_info=True,
                    )

            # Abort all active write batches
            for write_batch in list(self._active_write_batches):
                try:
                    write_batch.abort()
                except Exception as e:
                    logger.error(
                        "Write batch abort failed",
                        extra={"write_batch_id": str(self._uuid), "error": str(e)},
                        exc_info=True,
                    )

            # Clear tracking sets
            self._active_transactions.clear()
            self._active_write_batches.clear()
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

    # =========================================================================
    # Subscriptions
    # =========================================================================

    def subscribe(self, options: SubscriptionOptions) -> Subscription:
        """Subscribe to key changes with flexible filtering.

        Args:
            options: Subscription options including filter specification (prefix, suffix, wildcard, length, composite)

        Returns:
            Subscription object for binding callbacks and managing lifecycle.

        Raises:
            StorageOperationError: If subscription fails or observer not configured.

        Examples:
            >>> from everyshape.storage.observer.subscription import (
            ...     PrefixFilter,
            ...     SubscriptionOptions,
            ... )
            >>> sub = storage.subscribe(
            ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
            ... )
            >>> sub.bind(lambda key: print(f"Changed: {key}"))
            >>> sub.close()
        """
        if self._observer is None:
            raise StorageOperationError("Observer not configured for this storage")

        try:
            return self._observer.subscribe(options)
        except Exception as e:
            raise StorageOperationError(f"Failed to subscribe: {e}") from e

    # =========================================================================
    # Transaction Management
    # =========================================================================

    @overload
    def begin(self, *, read_only: Literal[True]) -> SnapshotProtocol: ...

    @overload
    def begin(self, *, write_only: Literal[True]) -> WriteBatchProtocol: ...

    @overload
    def begin(
        self, *, read_only: Literal[False], write_only: Literal[False]
    ) -> TransactionProtocol: ...

    def begin(
        self,
        *,
        read_only: bool = False,
        write_only: bool = False,
    ) -> WriteBatchProtocol | SnapshotProtocol | TransactionProtocol:
        """Begin transaction or snapshot.

        Args:
            read_only: If True, creates a read-only snapshot
            write_only: If True, creates a write-only batch

        Returns:
            SnapshotProtocol if read_only=True
            WriteBatchProtocol if write_only=True
            TransactionProtocol otherwise

        Raises:
            StorageError: If begin fails
            StorageClosedError: If storage is not open
        """
        if read_only:
            return self.begin_snapshot()
        elif write_only:
            return self.begin_write_batch()
        else:
            return self.begin_transaction()

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
                txn_options = esrocks.TransactionOptions(**txn_options_dict)
            except Exception as e:
                raise StorageError(f"Invalid snapshot options: {e}") from e

            # Begin transaction with snapshot
            try:
                esrocks_txn = self._db.begin_transaction(txn_options)
                esrocks_txn.set_snapshot()
            except Exception as e:
                raise StorageError(f"Failed to begin snapshot: {e}") from e

            snapshot = RocksDBSnapshot(self, esrocks_txn)
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
                    txn_options = esrocks.TransactionOptions(**self._txn_options_dict)
                except Exception as e:
                    raise StorageError(f"Invalid transaction options: {e}") from e

            # Begin transaction
            try:
                if txn_options is not None:
                    esrocks_txn = self._db.begin_transaction(txn_options)
                else:
                    esrocks_txn = self._db.begin_transaction()
            except Exception as e:
                raise StorageError(f"Failed to begin transaction: {e}") from e

            transaction = RocksDBTransaction(self, esrocks_txn)
            self._active_transactions.add(transaction)
            return transaction

    def begin_write_batch(self) -> RocksDBWriteBatch:
        """Begin write-only batch.

        Creates a write batch for efficient bulk write operations.

        Returns:
            New write batch instance

        Raises:
            StorageOperationError: If batch creation fails
            StorageClosedError: If storage is closed
        """
        self._require_open()

        with self._db_lock:
            # Create esrocks WriteBatch
            esrocks_batch = esrocks.WriteBatch()

            # Wrap in RocksDBWriteBatch
            write_batch = RocksDBWriteBatch(self, esrocks_batch)
            self._active_write_batches.add(write_batch)
            return write_batch

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
            except Exception as e:
                logger.error(
                    "Transaction abort failed",
                    extra={"txn_id": str(self._uuid), "error": str(e)},
                    exc_info=True,
                )
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
            except Exception as e:
                logger.error(
                    "Snapshot close failed",
                    extra={"snapshot_id": str(self._uuid), "error": str(e)},
                    exc_info=True,
                )

    @contextmanager
    def batch_write(self) -> Iterator[WriteBatchProtocol]:
        """Context manager providing a write-batch-like interface.

        RocksDB write-batch is not implemented separately; use a transaction as a
        write batch. Commits on successful exit, aborts on exception.
        """
        # Use a transaction as a write-batch
        batch = self.begin_write_batch()
        try:
            yield batch
            if not batch._written and not batch._aborted:
                batch.write()
        except Exception:
            try:
                if not batch._written and not batch._aborted:
                    batch.abort()
            except Exception as e:
                logger.error(
                    "Write batch abort failed",
                    extra={"write_batch_id": str(self._uuid), "error": str(e)},
                    exc_info=True,
                )
            raise

    def _notify(self, key: Key) -> None:
        """Notify observer of key change.

        Args:
            key: Key that changed
        """
        if self._observer is not None:
            try:
                self._observer.notify(key)
            except Exception as e:
                logger.error(
                    "Observer notification failed",
                    extra={"observer_id": str(self._uuid), "error": str(e)},
                    exc_info=True,
                )

    def _remove_transaction(self, transaction: RocksDBTransaction) -> None:
        """Remove transaction from active set.

        Args:
            transaction: Transaction to remove
        """
        with self._db_lock:
            self._active_transactions.discard(transaction)

    def _remove_snapshot(self, snapshot: RocksDBSnapshot) -> None:
        """Remove snapshot from active set.

        Args:
            snapshot: Snapshot to remove
        """
        with self._db_lock:
            self._active_snapshots.discard(snapshot)

    def _remove_write_batch(self, write_batch: RocksDBWriteBatch) -> None:
        """Remove write batch from active set.

        Args:
            write_batch: Write batch to remove
        """
        with self._db_lock:
            self._active_write_batches.discard(write_batch)

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

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager - close storage."""
        self.close()


if TYPE_CHECKING:
    _: type[TransactionProtocol] = RocksDBTransaction
    __: type[SnapshotProtocol] = RocksDBSnapshot
