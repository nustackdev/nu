"""In-memory storage backend with copy-on-write transaction isolation.

Fast, ephemeral key-value storage for testing and prototyping. Uses overlay pattern
for efficient transaction isolation without full state copies.

Features:
- Copy-on-write transaction isolation (overlay pattern)
- Thread-safe with RLock
- Optional observer support for notifications
- No persistence - all data lost on close
- Implements full StorageProtocol

Limitations:
- No durability (in-memory only)
- No conflict detection (last commit wins)
- Memory-bound by dataset size
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from enum import Enum, auto
from logging import getLogger
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from redwood.storage import (
    CallbackFn,
    CodecProtocol,
    ObserverProtocol,
    ScanProtocol,
    SnapshotProtocol,
    StorageClosedError,
    StorageDeleteError,
    StorageKeyError,
    StorageOperationError,
    StorageScanOptions,
    StorageTransactionError,
    SubscriptionProtocol,
    TransactionProtocol,
    WriteBatchProtocol,
)


if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from redwood.loc.key import Key
    from redwood.types import Value


__all__ = [
    "InMemoryScan",
    "InMemorySnapshot",
    "InMemoryStorage",
    "InMemoryTransaction",
    "InMemoryWriteBatch",
]


# =============================================================================
# Copy-on-Write Overlay
# =============================================================================


logger = getLogger(__name__)


class _TransactionState:
    """Copy-on-write state overlay for transactions.

    Provides isolated view over shared parent state without copying.
    Only modified keys are stored locally.
    """

    def __init__(self, parent: dict[str, Any]):
        """Initialize overlay with parent state reference.

        Args:
            parent: Shared parent state (not copied)
        """
        self._parent = parent
        self._local: dict[str, Any] = {}  # Modified keys
        self._deleted: set[str] = set()  # Deleted keys

    def get(self, key: str) -> Any:
        """Get value by key.

        Args:
            key: Key to retrieve

        Returns:
            Value at key

        Raises:
            KeyError: If key not found
        """
        if key in self._deleted:
            raise KeyError(key)
        if key in self._local:
            return self._local[key]
        return self._parent[key]  # Read-through to parent

    def __contains__(self, key: str) -> bool:
        """Check if key exists in overlay.

        Args:
            key: Key to check

        Returns:
            True if key exists and not deleted
        """
        if key in self._deleted:
            return False
        return key in self._local or key in self._parent

    def __setitem__(self, key: str, value: Any) -> None:
        """Set key-value pair in overlay.

        Args:
            key: Key to set
            value: Value to store
        """
        self._deleted.discard(key)
        self._local[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete key from overlay.

        Args:
            key: Key to delete
        """
        self._deleted.add(key)
        self._local.pop(key, None)

    def keys(self) -> set[str]:
        """Get all visible keys (parent + local - deleted).

        Returns:
            Set of all visible keys
        """
        all_keys = set(self._parent.keys()) | set(self._local.keys())
        return all_keys - self._deleted

    def to_dict(self) -> dict[str, Any]:
        """Merge overlay to final state dictionary.

        Returns:
            Merged state with all modifications applied
        """
        result = self._parent.copy()
        for k in self._deleted:
            result.pop(k, None)
        result.update(self._local)
        return result


# =============================================================================
# Base Context Class
# =============================================================================


class _InMemoryContextBase:
    """Base class for in-memory storage contexts.

    Provides common functionality for state management, validation, and
    resource cleanup.
    """

    def __init__(self, storage: InMemoryStorage, state: dict[str, Any] | _TransactionState) -> None:
        """Initialize context with storage reference and state.

        Args:
            storage: Parent storage instance
            state: State dictionary or overlay
        """
        self._storage = storage
        self._state = state
        self._closed = False
        self._uuid = uuid4()

    def _require_active(self) -> dict[str, Any] | _TransactionState:
        """Validate context is active and return state.

        Returns:
            Active state

        Raises:
            StorageClosedError: If context is closed
        """
        if self._closed:
            raise StorageClosedError("Context is closed")
        return self._state

    def _mark_closed(self) -> None:
        """Mark context as closed."""
        self._closed = True

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
        return isinstance(other, _InMemoryContextBase) and self._uuid == other._uuid


# =============================================================================
# Operation Mixins
# =============================================================================


class _ReadOperationsMixin:
    """Mixin providing read operations for in-memory storage contexts."""

    # Type hints for mixed-in attributes
    _storage: InMemoryStorage
    _require_active: Any

    def get(self, key: Key) -> Value:
        """Get value by key.

        Args:
            key: Key to retrieve

        Returns:
            Value at key

        Raises:
            StorageKeyError: If key not found
            StorageOperationError: If operation fails
            StorageClosedError: If context is closed
        """
        state = self._require_active()
        codec = self._storage.codec

        # Encode key using codec
        try:
            key_str = codec.encode_key(key)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key {key}: {e}") from e

        # Check if key exists
        try:
            if isinstance(state, _TransactionState):
                value_encoded = state.get(key_str)
            else:
                if key_str not in state:
                    raise StorageKeyError(f"Key {key} not found")
                value_encoded = state[key_str]
        except KeyError:
            raise StorageKeyError(f"Key {key} not found") from None

        # Decode and return value
        try:
            return codec.decode_value(value_encoded)
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
        state = self._require_active()
        codec = self._storage.codec

        try:
            key_str = codec.encode_key(key)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key {key}: {e}") from e

        return key_str in state

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
        return InMemoryScan(self, options)  # type: ignore


class _WriteOperationsMixin:
    """Mixin providing write operations for in-memory storage contexts."""

    # Type hints for mixed-in attributes
    _storage: InMemoryStorage
    _require_active: Any
    _modified_keys: set[Key]

    def put(self, key: Key, value: Value) -> None:
        """Put key-value pair.

        Args:
            key: Key to set
            value: Value to store

        Raises:
            StorageOperationError: If write fails
            StorageClosedError: If context is closed
        """
        state = self._require_active()
        codec = self._storage.codec

        # Encode key using codec
        try:
            key_str = codec.encode_key(key)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode key {key}: {e}") from e

        # Encode and store value
        try:
            state[key_str] = codec.encode_value(value)
        except Exception as e:
            raise StorageOperationError(f"Failed to encode value for key {key}: {e}") from e

        # Track modification
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
        state = self._require_active()
        codec = self._storage.codec

        try:
            key_str = codec.encode_key(key)
        except Exception as e:
            raise StorageDeleteError(f"Failed to encode key {key}: {e}") from e

        # Check if key exists
        if key_str not in state:
            return False

        # Delete the key
        del state[key_str]

        # Track modification
        self._modified_keys.add(key)
        return True


# =============================================================================
# Scan
# =============================================================================


class IteratorType(Enum):
    """Type of scan iteration."""

    KEYS = auto()
    VALUES = auto()
    ITEMS = auto()


class InMemoryScan(ScanProtocol):
    """Scan iterator for in-memory storage.

    Provides iteration over key-value pairs with filtering and ordering.
    """

    def __init__(self, context: _InMemoryContextBase, options: StorageScanOptions) -> None:
        """Initialize scan.

        Args:
            context: Storage context (transaction or snapshot)
            options: Scan configuration
        """
        self._context = context
        self._storage = cast("InMemoryStorage", context._storage)
        self._options = options

    def _iterate_impl(self, iterator_type: IteratorType) -> Generator[object, None, None]:
        """Core iteration implementation.

        Args:
            iterator_type: Type of iteration (keys/values/items)

        Yields:
            Keys, values, or (key, value) tuples based on iterator_type
        """
        state = self._context._require_active()
        options = self._options
        codec = self._storage.codec

        # Encode bounds for comparison
        start_str = codec.encode_key(options.start) if options.start is not None else None
        end_str = codec.encode_key(options.end) if options.end is not None else None

        # Get all encoded keys
        if isinstance(state, _TransactionState):
            encoded_keys = list(state.keys())
        else:
            encoded_keys = list(state.keys())

        # Sort lexicographically
        encoded_keys.sort(reverse=options.reverse)

        # Iterate over sorted encoded keys
        count = 0
        for key_str in encoded_keys:
            # Check start bound (compare encoded keys)
            if start_str is not None:
                if options.start_inclusive:
                    if key_str < start_str:
                        continue
                else:
                    if key_str <= start_str:
                        continue

            # Check end bound (compare encoded keys)
            if end_str is not None:
                if options.end_inclusive:
                    if key_str > end_str:
                        continue
                else:
                    if key_str >= end_str:
                        continue

            # Get value from state
            try:
                if isinstance(state, _TransactionState):
                    value_encoded = state.get(key_str)
                else:
                    value_encoded = state[key_str]
            except KeyError:
                continue

            # Decode key and value
            try:
                key = codec.decode_key(key_str)
                value = codec.decode_value(value_encoded)
            except Exception as e:
                raise StorageOperationError(f"Failed to decode key/value {key_str}: {e}") from e

            # Check key length filter
            if options.length > 0 and len(key) != options.length:
                continue

            # Check result limit
            if options.limit is not None and count >= options.limit:
                break

            # Yield based on iterator type
            if iterator_type == IteratorType.KEYS:
                yield key
            elif iterator_type == IteratorType.VALUES:
                yield value
            elif iterator_type == IteratorType.ITEMS:
                yield (key, value)

            count += 1

    def items(self) -> Generator[tuple[Key, Value], None, None]:
        """Iterate over (key, value) tuples.

        Yields:
            Tuples of (key, value) for each item in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        return cast(
            "Generator[tuple[Key, Value], None, None]", self._iterate_impl(IteratorType.ITEMS)
        )

    def keys(self) -> Generator[Key, None, None]:
        """Iterate over keys only.

        Yields:
            Keys in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        return cast("Generator[Key, None, None]", self._iterate_impl(IteratorType.KEYS))

    def values(self) -> Generator[Value, None, None]:
        """Iterate over values only.

        Yields:
            Values in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        return cast("Generator[Value, None, None]", self._iterate_impl(IteratorType.VALUES))


# =============================================================================
# Snapshot
# =============================================================================


class InMemorySnapshot(_InMemoryContextBase, _ReadOperationsMixin, SnapshotProtocol):
    """Read-only snapshot for in-memory storage.

    Provides point-in-time view of storage state with full copy isolation.
    """

    def __init__(self, storage: InMemoryStorage, state: dict[str, Any]) -> None:
        """Initialize snapshot with copied state.

        Args:
            storage: Parent storage instance
            state: Snapshot of state (copied, not shared)
        """
        super().__init__(storage, state)

    @property
    def writable(self) -> bool:
        """Check if snapshot is writable.

        Returns:
            Always False for snapshots.
        """
        return False

    def close(self) -> None:
        """Close snapshot and release resources."""
        if not self._closed:
            self._mark_closed()
            self._storage._untrack_snapshot(self)

    def __enter__(self) -> InMemorySnapshot:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()


# =============================================================================
# Transaction
# =============================================================================


class InMemoryTransaction(
    _InMemoryContextBase, _ReadOperationsMixin, _WriteOperationsMixin, TransactionProtocol
):
    """Read-write transaction for in-memory storage.

    Provides isolated workspace with copy-on-write overlay and commit/abort semantics.
    """

    def __init__(self, storage: InMemoryStorage, state: _TransactionState) -> None:
        """Initialize transaction with overlay state.

        Args:
            storage: Parent storage instance
            state: Overlay state (copy-on-write)
        """
        super().__init__(storage, state)
        self._modified_keys: set[Key] = set()
        self._committed = False
        self._aborted = False

    @property
    def writable(self) -> bool:
        """Check if transaction is writable.

        Returns:
            Always True for transactions.
        """
        return True

    def commit(self) -> None:
        """Commit transaction and make changes permanent.

        Raises:
            StorageTransactionError: If commit fails
            StorageClosedError: If already committed or aborted
        """
        if self._closed:
            logger.error("Cannot commit, transaction is closed", extra={"txn_id": str(self._uuid)})
            raise StorageClosedError("Transaction is closed")
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

        try:
            # Merge overlay into parent state
            state = cast("_TransactionState", self._state)
            merged = state.to_dict()

            with self._storage._lock:
                self._storage._state = merged

            logger.info(
                "Transaction committed",
                extra={"txn_id": str(self._uuid), "modified_keys": len(self._modified_keys)},
            )

            self._committed = True
            self._mark_closed()

            # Notify observers
            for key in self._modified_keys:
                self._storage._notify(key)

            self._storage._untrack_transaction(self)
        except Exception as e:
            logger.error(
                "Transaction commit failed",
                extra={"txn_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionError(f"Failed to commit transaction: {e}") from e

    def abort(self) -> None:
        """Abort transaction and discard changes.

        Raises:
            StorageTransactionError: If abort fails
        """
        if self._closed:
            # Already closed, nothing to do
            logger.debug("Abort called on closed transaction", extra={"txn_id": str(self._uuid)})
            return

        try:
            logger.info(
                "Transaction aborted",
                extra={"txn_id": str(self._uuid), "discarded_keys": len(self._modified_keys)},
            )

            self._aborted = True
            self._mark_closed()
            self._storage._untrack_transaction(self)
        except Exception as e:
            logger.error(
                "Transaction abort failed",
                extra={"txn_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionError(f"Failed to abort transaction: {e}") from e

    def __enter__(self) -> InMemoryTransaction:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        if exc_type is not None:
            # Exception occurred, abort
            self.abort()
        else:
            # Success, commit if not already done
            if not self._committed and not self._aborted:
                self.commit()


# =============================================================================
# Write Batch
# =============================================================================


class InMemoryWriteBatch(_InMemoryContextBase, _WriteOperationsMixin, WriteBatchProtocol):
    """Write-only batch for in-memory storage.

    Accumulates writes without read capabilities for efficient bulk operations.
    Uses copy-on-write overlay like transactions.
    """

    def __init__(self, storage: InMemoryStorage, state: _TransactionState) -> None:
        """Initialize write batch with overlay state.

        Args:
            storage: Parent storage instance
            state: Overlay state (copy-on-write)
        """
        super().__init__(storage, state)
        self._modified_keys: set[Key] = set()
        self._written = False
        self._aborted = False

    @property
    def writable(self) -> bool:
        """Check if write batch is writable.

        Returns:
            Always True for write batches.
        """
        return True

    def write(self) -> None:
        """Write batch and make changes permanent.

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

        try:
            # Merge overlay into parent state
            state = cast("_TransactionState", self._state)
            merged = state.to_dict()

            with self._storage._lock:
                self._storage._state = merged

            logger.info(
                "Write batch written",
                extra={"batch_id": str(self._uuid), "modified_keys": len(self._modified_keys)},
            )

            self._written = True
            self._mark_closed()

            # Notify observers
            for key in self._modified_keys:
                self._storage._notify(key)

            self._storage._untrack_write_batch(self)
        except Exception as e:
            logger.error(
                "Write batch write failed",
                extra={"batch_id": str(self._uuid), "error": str(e)},
                exc_info=True,
            )
            raise StorageTransactionError(f"Failed to write batch: {e}") from e

    def abort(self) -> None:
        """Abort write batch and discard changes.

        Raises:
            StorageTransactionError: If abort fails
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
            self._storage._untrack_write_batch(self)
        except Exception as e:
            raise StorageTransactionError(f"Failed to abort write batch: {e}") from e

    def __enter__(self) -> InMemoryWriteBatch:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        if exc_type is not None:
            # Exception occurred, abort
            self.abort()
        else:
            # Success, write if not already done
            if not self._written and not self._aborted:
                self.write()


# =============================================================================
# Storage
# =============================================================================


class InMemoryStorage:
    """In-memory storage backend with copy-on-write transaction isolation.

    Fast, ephemeral key-value storage using overlay pattern for efficient
    transaction isolation. All data is lost when storage is closed.

    Attributes:
        codec: Codec for key/value encoding
    """

    def __init__(
        self,
        codec: CodecProtocol,
        observer: ObserverProtocol | None = None,
    ) -> None:
        """Initialize in-memory storage.

        Args:
            codec: Codec for key/value encoding
            observer: Optional observer for change notifications
        """
        self.codec = codec
        self._observer = observer

        # State
        self._state: dict[str, Any] = {}  # key_str -> value
        self._opened = False

        # Synchronization (use RLock to allow reentrant locking)
        self._lock = threading.RLock()

        # Context tracking
        self._active_transactions: set[InMemoryTransaction] = set()
        self._active_snapshots: set[InMemorySnapshot] = set()
        self._active_write_batches: set[InMemoryWriteBatch] = set()

    def _require_open(self) -> None:
        """Validate storage is open.

        Raises:
            StorageClosedError: If storage is not open
        """
        if not self._opened:
            raise StorageClosedError("Storage is not open")

    def _notify(self, key: Key) -> None:
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

    def _untrack_transaction(self, txn: InMemoryTransaction) -> None:
        """Remove transaction from active set.

        Args:
            txn: Transaction to untrack
        """
        with self._lock:
            self._active_transactions.discard(txn)

    def _untrack_snapshot(self, snap: InMemorySnapshot) -> None:
        """Remove snapshot from active set.

        Args:
            snap: Snapshot to untrack
        """
        with self._lock:
            self._active_snapshots.discard(snap)

    def _untrack_write_batch(self, batch: InMemoryWriteBatch) -> None:
        """Remove write batch from active set.

        Args:
            batch: Write batch to untrack
        """
        with self._lock:
            self._active_write_batches.discard(batch)

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def open(self) -> None:
        """Open storage and initialize resources.

        Raises:
            StorageOperationError: If open fails
        """
        if self._opened:
            return

        try:
            self._state = {}
            self._opened = True
        except Exception as e:
            raise StorageOperationError(f"Failed to open storage: {e}") from e

    def close(self) -> None:
        """Close storage and release resources.

        All data is lost. Active transactions/snapshots are aborted/closed.

        Raises:
            StorageOperationError: If close fails
        """
        if not self._opened:
            return

        with self._lock:
            # Close all active transactions
            for txn in list(self._active_transactions):
                try:
                    txn.abort()
                except Exception:
                    pass

            # Close all active snapshots
            for snap in list(self._active_snapshots):
                try:
                    snap.close()
                except Exception:
                    pass

            # Close all active write batches
            for batch in list(self._active_write_batches):
                try:
                    batch.abort()
                except Exception:
                    pass

            # Clear tracking sets
            self._active_transactions.clear()
            self._active_snapshots.clear()
            self._active_write_batches.clear()

            # Clear state
            self._state = {}
            self._opened = False

    def __enter__(self) -> InMemoryStorage:
        """Enter context manager."""
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()

    # =========================================================================
    # Subscriptions
    # =========================================================================

    def subscribe(
        self,
        pattern: Key,
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
            StorageOperationError: If subscription fails or observer not configured
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

    # =========================================================================
    # Transaction Management
    # =========================================================================

    def begin(
        self,
        *,
        read_only: bool = False,
        write_only: bool = False,
    ) -> WriteBatchProtocol | SnapshotProtocol | TransactionProtocol:
        """Begin new transaction with specified access level.

        Args:
            read_only: If True, creates a read-only snapshot
            write_only: If True, creates a write-only batch

        Returns:
            SnapshotProtocol if read_only=True
            WriteBatchProtocol if write_only=True
            TransactionProtocol otherwise

        Raises:
            StorageOperationError: If transaction creation fails
        """
        if read_only:
            return self.begin_snapshot()
        elif write_only:
            return self.begin_write_batch()
        else:
            return self.begin_transaction()

    def begin_snapshot(self) -> InMemorySnapshot:
        """Begin read-only snapshot.

        Returns:
            New snapshot instance with full state copy

        Raises:
            StorageOperationError: If snapshot creation fails
        """
        self._require_open()

        with self._lock:
            # Create snapshot with copy of current state
            snapshot = InMemorySnapshot(self, self._state.copy())
            self._active_snapshots.add(snapshot)
            return snapshot

    def begin_transaction(self) -> InMemoryTransaction:
        """Begin read-write transaction.

        Returns:
            New transaction instance with copy-on-write overlay

        Raises:
            StorageOperationError: If transaction creation fails
        """
        self._require_open()

        with self._lock:
            # Create transaction with overlay (no copy)
            overlay = _TransactionState(self._state)
            transaction = InMemoryTransaction(self, overlay)
            self._active_transactions.add(transaction)
            return transaction

    def begin_write_batch(self) -> InMemoryWriteBatch:
        """Begin write-only batch.

        Returns:
            New write batch instance with copy-on-write overlay

        Raises:
            StorageOperationError: If batch creation fails
        """
        self._require_open()

        with self._lock:
            # Create write batch with overlay (no copy)
            overlay = _TransactionState(self._state)
            write_batch = InMemoryWriteBatch(self, overlay)
            self._active_write_batches.add(write_batch)
            return write_batch

    @contextmanager
    def transaction(self) -> Iterator[InMemoryTransaction]:
        """Context manager for transactions: commit on success, abort on exception."""
        txn = self.begin_transaction()
        try:
            yield txn
        except Exception:
            if not txn._committed and not txn._aborted:
                txn.abort()
            raise
        else:
            if not txn._committed and not txn._aborted:
                txn.commit()

    @contextmanager
    def snapshot(self) -> Iterator[InMemorySnapshot]:
        """Context manager for read-only snapshots: always closes snapshot on exit."""
        snap = self.begin_snapshot()
        try:
            yield snap
        finally:
            try:
                snap.close()
            except Exception:
                pass

    @contextmanager
    def batch_write(self) -> Iterator[InMemoryWriteBatch]:
        """Context manager for write batches: write on success, abort on exception."""
        batch = self.begin_write_batch()
        try:
            yield batch
        except Exception:
            if not batch._written and not batch._aborted:
                batch.abort()
            raise
        else:
            if not batch._written and not batch._aborted:
                batch.write()


if TYPE_CHECKING:
    _: type[TransactionProtocol] = InMemoryTransaction
    __: type[SnapshotProtocol] = InMemorySnapshot
