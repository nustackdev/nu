"""Text-based storage backend for debugging and development.

Human-readable JSON storage for inspecting data structures, tracing operations,
and understanding system behavior. Not intended for production use.

Features:
- Human-readable JSON format
- Simple file-based persistence
- Optional operation logging
- Implements StorageProtocol correctly

Limitations:
- No concurrent access safety
- Memory-bound (entire state in memory)
- Slow writes (rewrites entire file)
- Single process only
"""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from redwood.storage import (
    CallbackFn,
    CodecProtocol,
    ScanProtocol,
    SnapshotProtocol,
    StorageClosedError,
    StorageDeleteError,
    StorageError,
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
    "TextScan",
    "TextSnapshot",
    "TextStorage",
    "TextTransaction",
    "TextWriteBatch",
]


# =============================================================================
# Constants
# =============================================================================

STATE_FILE = "state.json"
OPERATIONS_FILE = "operations.jsonl"
STATE_VERSION = 1


# =============================================================================
# Helpers
# =============================================================================


class IteratorType(Enum):
    """Type of scan iteration."""

    KEYS = auto()
    VALUES = auto()
    ITEMS = auto()


# =============================================================================
# Base Context Class
# =============================================================================


class _TextContextBase:
    """Base class for text storage contexts.

    Provides common functionality for state management, validation, and
    resource cleanup.
    """

    def __init__(self, storage: TextStorage, state: dict[str, Any]) -> None:
        """Initialize context with storage reference and state snapshot.

        Args:
            storage: Parent storage instance
            state: State dictionary (may be shared or copied)
        """
        self._storage = storage
        self._state = state
        self._closed = False
        self._uuid = uuid4()

    def _require_active(self) -> dict[str, Any]:
        """Validate context is active and return state.

        Returns:
            Active state dictionary

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
        return isinstance(other, _TextContextBase) and self._uuid == other._uuid


# =============================================================================
# Operation Mixins
# =============================================================================


class _ReadOperationsMixin:
    """Mixin providing read operations for text storage contexts."""

    # Type hints for mixed-in attributes
    _storage: TextStorage
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
        if key_str not in state:
            raise StorageKeyError(f"Key {key} not found")

        # Decode and return value
        try:
            return codec.decode_value(state[key_str])
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
        return TextScan(self, options)  # type: ignore


class _WriteOperationsMixin:
    """Mixin providing write operations for text storage contexts."""

    # Type hints for mixed-in attributes
    _storage: TextStorage
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


class TextScan(ScanProtocol):
    """Scan iterator for text storage.

    Provides iteration over key-value pairs with filtering and ordering.
    """

    def __init__(self, context: _TextContextBase, options: StorageScanOptions) -> None:
        """Initialize scan.

        Args:
            context: Storage context (transaction or snapshot)
            options: Scan configuration
        """
        self._context = context
        self._storage = cast("TextStorage", context._storage)
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

        # Get all encoded keys and sort lexicographically
        encoded_keys = sorted(state.keys(), reverse=options.reverse)

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

            # Decode key and value
            try:
                key = codec.decode_key(key_str)
                value = codec.decode_value(state[key_str])
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


class TextSnapshot(_TextContextBase, _ReadOperationsMixin, SnapshotProtocol):
    """Read-only snapshot for text storage.

    Provides point-in-time view of storage state.
    """

    def __init__(self, storage: TextStorage, state: dict[str, Any]) -> None:
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

    def __enter__(self) -> TextSnapshot:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()


# =============================================================================
# Transaction
# =============================================================================


class TextTransaction(
    _TextContextBase, _ReadOperationsMixin, _WriteOperationsMixin, TransactionProtocol
):
    """Read-write transaction for text storage.

    Provides isolated workspace with commit/abort semantics.
    """

    def __init__(self, storage: TextStorage, state: dict[str, Any]) -> None:
        """Initialize transaction with workspace.

        Args:
            storage: Parent storage instance
            state: Workspace state (copy of current state)
        """
        super().__init__(storage, state)
        self._modified_keys: set[Key] = set()
        self._committed = False
        self._aborted = False

    def commit(self) -> None:
        """Commit transaction and make changes permanent.

        Raises:
            StorageTransactionError: If commit fails
            StorageClosedError: If already committed or aborted
        """
        if self._closed:
            raise StorageClosedError("Transaction is closed")
        if self._committed:
            raise StorageTransactionError("Transaction already committed")
        if self._aborted:
            raise StorageTransactionError("Transaction already aborted")

        try:
            # Write state to disk
            self._storage._write_state(self._state)

            # Log operation if enabled
            if self._storage._log_operations:
                self._storage._log_operation("commit", None, None, txn_id=str(self._uuid))

            self._committed = True
            self._mark_closed()
            self._storage._untrack_transaction(self)
        except Exception as e:
            raise StorageTransactionError(f"Failed to commit transaction: {e}") from e

    def abort(self) -> None:
        """Abort transaction and discard changes.

        Raises:
            StorageTransactionError: If abort fails
        """
        if self._closed:
            # Already closed, nothing to do
            return

        try:
            # Log operation if enabled
            if self._storage._log_operations:
                self._storage._log_operation("abort", None, None, txn_id=str(self._uuid))

            self._aborted = True
            self._mark_closed()
            self._storage._untrack_transaction(self)
        except Exception as e:
            raise StorageTransactionError(f"Failed to abort transaction: {e}") from e

    def __enter__(self) -> TextTransaction:
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


class TextWriteBatch(_TextContextBase, _WriteOperationsMixin, WriteBatchProtocol):
    """Write-only batch for text storage.

    Accumulates writes without read capabilities for efficient bulk operations.
    """

    def __init__(self, storage: TextStorage, state: dict[str, Any]) -> None:
        """Initialize write batch with workspace.

        Args:
            storage: Parent storage instance
            state: Workspace state (copy of current state)
        """
        super().__init__(storage, state)
        self._modified_keys: set[Key] = set()
        self._written = False
        self._aborted = False

    def write(self) -> None:
        """Write batch and make changes permanent.

        Raises:
            StorageTransactionError: If write fails
            StorageClosedError: If already written or aborted
        """
        if self._closed:
            raise StorageClosedError("Write batch is closed")
        if self._written:
            raise StorageTransactionError("Write batch already written")
        if self._aborted:
            raise StorageTransactionError("Write batch already aborted")

        try:
            # Write state to disk
            self._storage._write_state(self._state)

            # Log operation if enabled
            if self._storage._log_operations:
                self._storage._log_operation("write", None, None, txn_id=str(self._uuid))

            self._written = True
            self._mark_closed()
            self._storage._untrack_write_batch(self)
        except Exception as e:
            raise StorageTransactionError(f"Failed to write batch: {e}") from e

    def abort(self) -> None:
        """Abort write batch and discard changes.

        Raises:
            StorageTransactionError: If abort fails
        """
        if self._closed:
            # Already closed, nothing to do
            return

        try:
            # Log operation if enabled
            if self._storage._log_operations:
                self._storage._log_operation("abort", None, None, txn_id=str(self._uuid))

            self._aborted = True
            self._mark_closed()
            self._storage._untrack_write_batch(self)
        except Exception as e:
            raise StorageTransactionError(f"Failed to abort write batch: {e}") from e

    def __enter__(self) -> TextWriteBatch:
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


class TextStorage:
    """Text-based storage backend for debugging and development.

    Stores data as human-readable JSON with optional operation logging.
    Implements StorageProtocol but not optimized for production use.

    File structure:
        storage_dir/
        ├── state.json          # Current key-value state
        └── operations.jsonl    # Operation log (optional)

    Attributes:
        path: Storage directory path
        codec: Codec for key/value encoding
    """

    def __init__(
        self,
        path: str | Path,
        codec: CodecProtocol,
        log_operations: bool = False,
    ) -> None:
        """Initialize text storage.

        Args:
            path: Directory path for storage files
            codec: Codec for key/value encoding
            log_operations: Enable operation logging (default: False)
        """
        self.path = Path(path)
        self.codec = codec
        self._log_operations = log_operations

        # State
        self._state: dict[str, Any] = {}  # key_str -> value
        self._opened = False

        # Synchronization (use RLock to allow reentrant locking during close)
        self._lock = threading.RLock()

        # Context tracking
        self._active_transactions: set[TextTransaction] = set()
        self._active_snapshots: set[TextSnapshot] = set()
        self._active_write_batches: set[TextWriteBatch] = set()

    def _require_open(self) -> None:
        """Validate storage is open.

        Raises:
            StorageClosedError: If storage is not open
        """
        if not self._opened:
            raise StorageClosedError("Storage is not open")

    def _read_state(self) -> dict[str, Any]:
        """Read state from disk.

        Returns:
            State dictionary

        Raises:
            StorageError: If read fails
        """
        state_path = self.path / STATE_FILE

        if not state_path.exists():
            return {}

        try:
            with open(state_path) as f:
                data = json.load(f)

            # Validate version
            if data.get("version") != STATE_VERSION:
                raise StorageError(
                    f"Unsupported state version: {data.get('version')} (expected {STATE_VERSION})"
                )

            return data.get("data", {})
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to parse state file: {e}") from e
        except Exception as e:
            raise StorageError(f"Failed to read state file: {e}") from e

    def _write_state(self, state: dict[str, Any]) -> None:
        """Write state to disk atomically.

        Args:
            state: State dictionary to write

        Raises:
            StorageError: If write fails
        """
        state_path = self.path / STATE_FILE

        # Create directory if needed
        self.path.mkdir(parents=True, exist_ok=True)

        # Prepare data
        data = {"version": STATE_VERSION, "data": state}

        # Write to temp file
        temp_path = state_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
        except Exception as e:
            # Clean up temp file
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise StorageError(f"Failed to write state file: {e}") from e

        # Atomic rename
        try:
            temp_path.replace(state_path)
        except Exception as e:
            # Clean up temp file
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise StorageError(f"Failed to replace state file: {e}") from e

        # Update in-memory state
        with self._lock:
            self._state = state.copy()

    def _log_operation(
        self, op: str, key: Key | None, value: Value | None, txn_id: str | None = None
    ) -> None:
        """Log operation to operations.jsonl.

        Args:
            op: Operation name (put, delete, commit, abort, write)
            key: Key involved (if applicable)
            value: Value involved (if applicable)
            txn_id: Transaction ID (if applicable)
        """
        if not self._log_operations:
            return

        ops_path = self.path / OPERATIONS_FILE

        # Prepare log entry
        entry: dict[str, Any] = {
            "op": op,
            "ts": datetime.now(UTC).isoformat(),
        }

        if txn_id is not None:
            entry["txn"] = txn_id
        if key is not None:
            entry["key"] = key
        if value is not None:
            entry["value"] = value

        # Append to log file
        try:
            with open(ops_path, "a") as f:
                json.dump(entry, f, separators=(",", ":"))
                f.write("\n")
        except Exception:
            # Best effort logging, don't fail operations
            pass

    def _untrack_transaction(self, txn: TextTransaction) -> None:
        """Remove transaction from active set.

        Args:
            txn: Transaction to untrack
        """
        with self._lock:
            self._active_transactions.discard(txn)

    def _untrack_snapshot(self, snap: TextSnapshot) -> None:
        """Remove snapshot from active set.

        Args:
            snap: Snapshot to untrack
        """
        with self._lock:
            self._active_snapshots.discard(snap)

    def _untrack_write_batch(self, batch: TextWriteBatch) -> None:
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
        """Open storage and load state.

        Raises:
            StorageOperationError: If open fails
        """
        if self._opened:
            return

        try:
            # Read state from disk
            self._state = self._read_state()
            self._opened = True
        except Exception as e:
            raise StorageOperationError(f"Failed to open storage: {e}") from e

    def close(self) -> None:
        """Close storage and release resources.

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

            self._opened = False

    def __enter__(self) -> TextStorage:
        """Enter context manager."""
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()

    # =========================================================================
    # Subscriptions (Not Implemented)
    # =========================================================================

    def subscribe(
        self,
        pattern: Key,
        callback: CallbackFn,
        depth: int = 0,
    ) -> SubscriptionProtocol:
        """Subscribe to key pattern changes.

        Not implemented for text storage.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Subscriptions not supported by text storage")

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes.

        Not implemented for text storage.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Subscriptions not supported by text storage")

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

    def begin_snapshot(self) -> TextSnapshot:
        """Begin read-only snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageOperationError: If snapshot creation fails
        """
        self._require_open()

        with self._lock:
            # Create snapshot with copy of current state
            snapshot = TextSnapshot(self, self._state.copy())
            self._active_snapshots.add(snapshot)
            return snapshot

    def begin_transaction(self) -> TextTransaction:
        """Begin read-write transaction.

        Returns:
            New transaction instance

        Raises:
            StorageOperationError: If transaction creation fails
        """
        self._require_open()

        with self._lock:
            # Create transaction with copy of current state
            transaction = TextTransaction(self, self._state.copy())
            self._active_transactions.add(transaction)
            return transaction

    def begin_write_batch(self) -> TextWriteBatch:
        """Begin write-only batch.

        Returns:
            New write batch instance

        Raises:
            StorageOperationError: If batch creation fails
        """
        self._require_open()

        with self._lock:
            # Create write batch with copy of current state
            write_batch = TextWriteBatch(self, self._state.copy())
            self._active_write_batches.add(write_batch)
            return write_batch

    @contextmanager
    def transaction(self) -> Iterator[TextTransaction]:
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
    def snapshot(self) -> Iterator[TextSnapshot]:
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
    def batch_write(self) -> Iterator[TextWriteBatch]:
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
