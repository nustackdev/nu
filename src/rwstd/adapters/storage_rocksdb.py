"""RocksDB storage backend with transaction and snapshot support."""

from __future__ import annotations

import threading
from functools import cached_property
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import attrs
from frozendict import frozendict
from mesh import Attach, ResourceSpec, Spec

from redwood.be import (
    SnapshotError,
    StorageCapabilities,
    StorageConnectionError,
    StorageError,
    StorageKeyError,
    StorageOperationError,
    StorageScanOptions,
    TransactionError,
    TransactionInvalidError,
)
from rwstd.lazy_import import lazy_import

from .bases import BaseStorage


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    import rwrocks as _rwrocks  # type: ignore[import]
    from redwood.abc import TupleKey, Value
    from redwood.be import (
        CodecProtocol,
        SnapshotProtocol,
        StorageProtocol,
        TransactionProtocol,
    )


logger = getLogger(__name__)


__all__ = [
    "RocksDBStorage",
    "RocksDBStorageSnapshot",
    "RocksDBStorageSpec",
    "RocksDBStorageTransaction",
]

rwrocks = cast(
    "_rwrocks",
    lazy_import("rwrocks", "rwrocks is required for RocksDBStorage."),
)


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


def _collect_prefixed_items(
    iterator: Any,
    encoded_prefix: bytes,
    decode_key: Callable[[bytes], TupleKey],
    decode_value: Callable[[bytes], Value],
    prefix: TupleKey,
    depth: int,
) -> list[tuple[TupleKey, Value]]:
    """Collect key/value pairs matching the encoded prefix."""
    items: list[tuple[TupleKey, Value]] = []
    try:
        if encoded_prefix:
            iterator.seek(encoded_prefix)
        else:
            iterator.seek_to_first()

        while True:
            try:
                encoded_key, encoded_value = iterator.get()
            except ValueError:
                break

            if not encoded_key.startswith(encoded_prefix):
                break

            decoded_key = decode_key(encoded_key)
            if depth != -1 and len(decoded_key) - len(prefix) != depth:
                try:
                    iterator.skip()
                except ValueError:
                    break
                continue

            decoded_value = decode_value(encoded_value)
            items.append((decoded_key, decoded_value))

            try:
                iterator.skip()
            except ValueError:
                break
    finally:
        del iterator

    return items


def _scan_prefixed_items(
    iterator: Any,
    codec: CodecProtocol[bytes, bytes],
    options: StorageScanOptions,
) -> list[tuple[TupleKey, Value]]:
    """Collect key/value pairs honouring scan options."""
    if options.limit == 0:
        return []

    encoded_prefix = codec.encode_key(options.prefix)
    encoded_start = codec.encode_key(options.start) if options.start is not None else encoded_prefix
    seek_key = encoded_start if encoded_start >= encoded_prefix else encoded_prefix

    items: list[tuple[TupleKey, Value]] = []

    try:
        if seek_key:
            iterator.seek(seek_key)
        else:
            iterator.seek_to_first()
    except ValueError:
        return items

    while True:
        try:
            encoded_key, encoded_value = iterator.get()
        except ValueError:
            break

        if not encoded_key.startswith(encoded_prefix):
            break

        decoded_key = codec.decode_key(encoded_key)

        if options.start is not None and decoded_key < options.start:
            try:
                iterator.skip()
            except ValueError:
                break
            continue

        if options.end is not None and decoded_key >= options.end:
            break

        if options.depth != -1 and len(decoded_key) - len(options.prefix) != options.depth:
            try:
                iterator.skip()
            except ValueError:
                break
            continue

        decoded_value = codec.decode_value(encoded_value)
        items.append((decoded_key, decoded_value))

        if not options.reverse and options.limit is not None and len(items) >= options.limit:
            break

        try:
            iterator.skip()
        except ValueError:
            break

    if options.reverse:
        items.reverse()

    if options.limit is not None:
        items = items[: options.limit]

    return items


class RocksDBStorage(BaseStorage[bytes, bytes]):
    """RocksDB storage implementation leveraging the rwrocks bindings."""

    codec: CodecProtocol[bytes, bytes] = Attach()

    spec: RocksDBStorageSpec

    @cached_property
    def codec_cached(self) -> CodecProtocol[bytes, bytes]:
        """Cached property for codec to avoid repeated lookups."""
        return self.codec

    @classmethod
    def capabilities(cls) -> StorageCapabilities:
        """RocksDB backend exposes full scan capability and range deletes."""
        return StorageCapabilities(scan=True, range_delete=True, approximate_size=True)

    def setup(self) -> None:
        """Prepare filesystem locations and synchronization primitives."""
        self.path = (
            self.spec.path.resolve()
            if isinstance(self.spec.path, Path)
            else Path(self.spec.path).resolve()
        )

        wal_path_spec = self.spec.wal_path
        if wal_path_spec is not None:
            self._wal_path = (
                wal_path_spec.resolve()
                if isinstance(wal_path_spec, Path)
                else Path(wal_path_spec).resolve()
            )
        else:
            self._wal_path = None

        self._db: rwrocks.TransactionDB | None = None
        self._options: rwrocks.Options | None = None
        self._txn_db_options: rwrocks.TransactionDBOptions | None = None

        self._db_lock = threading.RLock()
        self._active_transactions: set[RocksDBStorageTransaction] = set()
        self._active_snapshots: set[RocksDBStorageSnapshot] = set()

        self._write_kwargs = {
            "sync": self.spec.sync_writes,
            "disable_wal": self.spec.disable_wal,
        }

        super().setup()

    def _connect_impl(self) -> None:
        """Open the RocksDB database using the configured specification."""
        with self._db_lock:
            if self.mode == "write":
                self.path.mkdir(parents=True, exist_ok=True)
                if self._wal_path is not None:
                    self._wal_path.mkdir(parents=True, exist_ok=True)
            else:
                if not self.path.exists():
                    raise StorageConnectionError(
                        f"RocksDB path {self.path} does not exist in read mode"
                    )
                if self._wal_path is not None and not self._wal_path.exists():
                    raise StorageConnectionError(
                        f"WAL path {self._wal_path} does not exist in read mode"
                    )

            options_kwargs = dict(self.spec.options_kwargs)
            if "create_if_missing" not in options_kwargs:
                options_kwargs["create_if_missing"] = (
                    self.mode == "write" and self.spec.create_if_missing
                )

            try:
                self._options = rwrocks.Options(**options_kwargs)
            except Exception as e:
                raise StorageError(f"Invalid RocksDB options: {e}") from e

            if self._wal_path is not None:
                self._options.wal_dir = str(self._wal_path)

            txn_db_kwargs = dict(self.spec.txn_db_options_kwargs)
            try:
                self._txn_db_options = (
                    rwrocks.TransactionDBOptions(**txn_db_kwargs) if txn_db_kwargs else None
                )
            except Exception as e:
                raise StorageError(f"Invalid RocksDB transaction options: {e}") from e

            try:
                self._db = rwrocks.TransactionDB(
                    str(self.path),
                    self._options,
                    self._txn_db_options,
                )
            except Exception as e:
                raise StorageConnectionError(f"Failed to open RocksDB: {e}") from e

        logger.debug("Connected to RocksDB at %s in %s mode", self.path, self.mode)

    def _disconnect_impl(self) -> None:
        """Close the RocksDB database and clean up active resources."""
        with self._db_lock:
            for transaction in list(self._active_transactions):
                try:
                    transaction.rollback()
                except Exception as exc:
                    logger.error(
                        "Failed to rollback RocksDB transaction during disconnect: %s",
                        exc,
                    )

            for snapshot in list(self._active_snapshots):
                try:
                    snapshot.close()
                except Exception as exc:
                    logger.error(
                        "Failed to close RocksDB snapshot during disconnect: %s",
                        exc,
                    )

            self._active_transactions.clear()
            self._active_snapshots.clear()

            if self._db is not None:
                try:
                    self._db.close()
                finally:
                    self._db = None
            self._options = None
            self._txn_db_options = None

        logger.debug("Disconnected from RocksDB")

    def _get_db(self) -> rwrocks.TransactionDB:
        db = self._db
        if db is None:
            raise StorageConnectionError("RocksDB instance is not connected")
        return db

    def _get_impl(self, key: TupleKey) -> Value:
        encoded_key = self.codec_cached.encode_key(key)

        with self._db_lock:
            try:
                encoded_value = self._get_db().get(encoded_key)
            except Exception as e:
                raise StorageOperationError(f"Failed to get key {key}: {e}") from e

        if encoded_value is None:
            raise StorageKeyError(f"Key {key} not found")

        try:
            return self.codec_cached.decode_value(encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to decode value for key {key}: {e}") from e

    def _set_impl(self, key: TupleKey, value: Value) -> None:
        encoded_key = self.codec_cached.encode_key(key)
        encoded_value = self.codec_cached.encode_value(value)

        with self._db_lock:
            try:
                self._get_db().put(encoded_key, encoded_value, **self._write_kwargs)
            except Exception as e:
                raise StorageOperationError(f"Failed to set key {key}: {e}") from e

    def _delete_impl(self, key: TupleKey) -> None:
        encoded_key = self.codec_cached.encode_key(key)

        with self._db_lock:
            db = self._get_db()
            try:
                existing = db.get(encoded_key)
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

            if existing is None:
                raise StorageKeyError(f"Key {key} not found")

            try:
                db.delete(encoded_key, **self._write_kwargs)
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

    def _exists_impl(self, key: TupleKey) -> bool:
        encoded_key = self.codec_cached.encode_key(key)

        with self._db_lock:
            try:
                return self._get_db().get(encoded_key) is not None
            except Exception as e:
                raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def _list_keys_impl(
        self,
        prefix: TupleKey,
        depth: int,
    ) -> Generator[TupleKey, None, None]:
        encoded_prefix = self.codec_cached.encode_key(prefix)

        try:
            with self._db_lock:
                iterator = self._get_db().iteritems()
                keys = _collect_prefixed_keys(
                    iterator,
                    encoded_prefix,
                    self.codec_cached.decode_key,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

        yield from keys

    def _list_values_impl(
        self,
        prefix: TupleKey,
        depth: int,
    ) -> Generator[Value, None, None]:
        encoded_prefix = self.codec_cached.encode_key(prefix)

        try:
            with self._db_lock:
                iterator = self._get_db().iteritems()
                items = _collect_prefixed_items(
                    iterator,
                    encoded_prefix,
                    self.codec_cached.decode_key,
                    self.codec_cached.decode_value,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list values under {prefix}: {e}") from e

        for _, value in items:
            yield value

    def _list_items_impl(
        self,
        prefix: TupleKey,
        depth: int,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        encoded_prefix = self.codec_cached.encode_key(prefix)

        try:
            with self._db_lock:
                iterator = self._get_db().iteritems()
                items = _collect_prefixed_items(
                    iterator,
                    encoded_prefix,
                    self.codec_cached.decode_key,
                    self.codec_cached.decode_value,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list items under {prefix}: {e}") from e

        yield from items

    def _scan_items_impl(
        self,
        options: StorageScanOptions,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        try:
            with self._db_lock:
                iterator = self._get_db().iteritems()
                items = _scan_prefixed_items(iterator, self.codec, options)
        except Exception as e:
            raise StorageOperationError(f"Failed to scan items under {options.prefix}: {e}") from e

        yield from items

    def _begin_transaction_impl(self) -> RocksDBStorageTransaction:
        with self._db_lock:
            txn_options_kwargs = dict(self.spec.transaction_options_kwargs)
            txn_options = (
                rwrocks.TransactionOptions(**txn_options_kwargs) if txn_options_kwargs else None
            )

            db = self._get_db()
            try:
                txn = (
                    db.begin_transaction(txn_options)
                    if txn_options is not None
                    else db.begin_transaction()
                )
            except Exception as e:
                raise StorageError(f"Failed to begin RocksDB transaction: {e}") from e

            transaction = RocksDBStorageTransaction(self, txn)
            self._active_transactions.add(transaction)
            return transaction

    def _begin_snapshot_impl(self) -> RocksDBStorageSnapshot:
        with self._db_lock:
            txn_options_kwargs = dict(self.spec.snapshot_options_kwargs)
            txn_options_kwargs.setdefault("set_snapshot", True)
            try:
                txn_options = rwrocks.TransactionOptions(**txn_options_kwargs)
            except Exception as e:
                raise StorageError(f"Invalid RocksDB snapshot options: {e}") from e

            db = self._get_db()
            try:
                txn = db.begin_transaction(txn_options)
            except Exception as e:
                raise StorageError(f"Failed to begin RocksDB snapshot: {e}") from e

            try:
                txn.set_snapshot()
            except Exception as e:
                raise StorageError(f"Failed to initialize RocksDB snapshot: {e}") from e

            snapshot = RocksDBStorageSnapshot(self, txn)
            self._active_snapshots.add(snapshot)
            return snapshot

    def _remove_transaction(self, transaction: RocksDBStorageTransaction) -> None:
        self._active_transactions.discard(transaction)

    def _remove_snapshot(self, snapshot: RocksDBStorageSnapshot) -> None:
        self._active_snapshots.discard(snapshot)


class RocksDBStorageTransaction:
    """Transaction wrapper implementing Redwood's transaction protocol."""

    def __init__(self, storage: RocksDBStorage, txn: rwrocks.Transaction) -> None:
        self._storage = storage
        self._txn: rwrocks.Transaction | None = txn
        self._committed = False
        self._rolled_back = False
        self._uuid = uuid4()

    def _require_txn(self) -> rwrocks.Transaction:
        if self._committed:
            raise TransactionInvalidError("Transaction already committed")
        if self._rolled_back:
            raise TransactionInvalidError("Transaction already rolled back")
        if self._txn is None:
            raise TransactionInvalidError("Transaction handle is closed")
        return self._txn

    def get(self, key: TupleKey) -> Value:
        txn = self._require_txn()
        encoded_key = self._storage.codec_cached.encode_key(key)

        with self._storage._db_lock:
            try:
                encoded_value = txn.get(encoded_key)
            except Exception as e:
                raise StorageOperationError(f"Failed to get key {key}: {e}") from e

        if encoded_value is None:
            raise StorageKeyError(f"Key {key} not found")

        try:
            return self._storage.codec_cached.decode_value(encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to decode value for key {key}: {e}") from e

    def set(self, key: TupleKey, value: Value) -> None:
        txn = self._require_txn()
        encoded_key = self._storage.codec_cached.encode_key(key)
        encoded_value = self._storage.codec_cached.encode_value(value)

        with self._storage._db_lock:
            try:
                txn.put(encoded_key, encoded_value)
            except Exception as e:
                raise StorageOperationError(f"Failed to set key {key}: {e}") from e

    def delete(self, key: TupleKey) -> None:
        txn = self._require_txn()
        encoded_key = self._storage.codec_cached.encode_key(key)

        with self._storage._db_lock:
            try:
                existing = txn.get(encoded_key)
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

            if existing is None:
                raise StorageKeyError(f"Key {key} not found")

            try:
                txn.delete_single(encoded_key)
            except Exception as e:
                raise StorageOperationError(f"Failed to delete key {key}: {e}") from e

    def exists(self, key: TupleKey) -> bool:
        txn = self._require_txn()
        encoded_key = self._storage.codec_cached.encode_key(key)

        with self._storage._db_lock:
            try:
                return txn.get(encoded_key) is not None
            except Exception as e:
                raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        txn = self._require_txn()
        encoded_prefix = self._storage.codec_cached.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                keys = _collect_prefixed_keys(
                    iterator,
                    encoded_prefix,
                    self._storage.codec_cached.decode_key,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

        yield from keys

    def list_values(self, prefix: TupleKey, depth: int = 1) -> Generator[Value, None, None]:
        txn = self._require_txn()
        encoded_prefix = self._storage.codec_cached.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                items = _collect_prefixed_items(
                    iterator,
                    encoded_prefix,
                    self._storage.codec_cached.decode_key,
                    self._storage.codec_cached.decode_value,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list values under {prefix}: {e}") from e

        for _, value in items:
            yield value

    def list_items(
        self,
        prefix: TupleKey,
        depth: int = 1,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        txn = self._require_txn()
        encoded_prefix = self._storage.codec_cached.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                items = _collect_prefixed_items(
                    iterator,
                    encoded_prefix,
                    self._storage.codec_cached.decode_key,
                    self._storage.codec_cached.decode_value,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list items under {prefix}: {e}") from e

        yield from items

    def scan_keys(self, options: StorageScanOptions, /) -> Generator[TupleKey, None, None]:
        """Perform ordered scan within transaction context."""
        for key, _ in self.scan_items(options):
            yield key

    def scan_items(
        self,
        options: StorageScanOptions,
        /,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Perform ordered scan yielding key/value pairs within transaction context."""
        txn = self._require_txn()

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                items = _scan_prefixed_items(iterator, self._storage.codec_cached, options)
        except Exception as e:
            raise StorageOperationError(f"Failed to scan items under {options.prefix}: {e}") from e

        yield from items

    def commit(self) -> None:
        txn = self._require_txn()

        with self._storage._db_lock:
            try:
                txn.commit()
            except Exception as e:
                raise TransactionError(f"Failed to commit RocksDB transaction: {e}") from e

            self._committed = True
            self._txn = None
            self._storage._remove_transaction(self)

    def rollback(self) -> None:
        txn = self._require_txn()

        with self._storage._db_lock:
            try:
                txn.rollback()
            except Exception as e:
                raise TransactionError(f"Failed to rollback RocksDB transaction: {e}") from e

            self._rolled_back = True
            self._txn = None
            self._storage._remove_transaction(self)

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RocksDBStorageTransaction) and self._uuid == other._uuid


class RocksDBStorageSnapshot:
    """Read-only snapshot backed by a RocksDB transaction snapshot."""

    def __init__(self, storage: RocksDBStorage, txn: rwrocks.Transaction) -> None:
        self._storage = storage
        self._txn: rwrocks.Transaction | None = txn
        self._closed = False
        self._uuid = uuid4()

    def _require_txn(self) -> rwrocks.Transaction:
        if self._closed or self._txn is None:
            raise SnapshotError("Snapshot is already closed")
        return self._txn

    def get(self, key: TupleKey) -> Value:
        txn = self._require_txn()
        encoded_key = self._storage.codec_cached.encode_key(key)

        with self._storage._db_lock:
            try:
                encoded_value = txn.get(encoded_key)
            except Exception as e:
                raise StorageOperationError(f"Failed to get key {key}: {e}") from e

        if encoded_value is None:
            raise StorageKeyError(f"Key {key} not found")

        try:
            return self._storage.codec_cached.decode_value(encoded_value)
        except Exception as e:
            raise StorageOperationError(f"Failed to decode value for key {key}: {e}") from e

    def exists(self, key: TupleKey) -> bool:
        txn = self._require_txn()
        encoded_key = self._storage.codec_cached.encode_key(key)

        with self._storage._db_lock:
            try:
                return txn.get(encoded_key) is not None
            except Exception as e:
                raise StorageOperationError(f"Failed to check key {key}: {e}") from e

    def list_keys(self, prefix: TupleKey, depth: int = 1) -> Generator[TupleKey, None, None]:
        txn = self._require_txn()
        encoded_prefix = self._storage.codec_cached.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                keys = _collect_prefixed_keys(
                    iterator,
                    encoded_prefix,
                    self._storage.codec_cached.decode_key,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list keys under {prefix}: {e}") from e

        yield from keys

    def list_values(self, prefix: TupleKey, depth: int = 1) -> Generator[Value, None, None]:
        txn = self._require_txn()
        encoded_prefix = self._storage.codec_cached.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                items = _collect_prefixed_items(
                    iterator,
                    encoded_prefix,
                    self._storage.codec_cached.decode_key,
                    self._storage.codec_cached.decode_value,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list values under {prefix}: {e}") from e

        for _, value in items:
            yield value

    def list_items(
        self,
        prefix: TupleKey,
        depth: int = 1,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        txn = self._require_txn()
        encoded_prefix = self._storage.codec_cached.encode_key(prefix)

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                items = _collect_prefixed_items(
                    iterator,
                    encoded_prefix,
                    self._storage.codec_cached.decode_key,
                    self._storage.codec_cached.decode_value,
                    prefix,
                    depth,
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to list items under {prefix}: {e}") from e

        for key, value in items:
            yield key, value

    def scan_keys(self, options: StorageScanOptions, /) -> Generator[TupleKey, None, None]:
        """Perform ordered scan within snapshot context."""
        for key, _ in self.scan_items(options):
            yield key

    def scan_items(
        self,
        options: StorageScanOptions,
        /,
    ) -> Generator[tuple[TupleKey, Value], None, None]:
        """Perform ordered scan yielding key/value pairs within snapshot context."""
        txn = self._require_txn()

        try:
            with self._storage._db_lock:
                iterator = txn.iteritems()
                items = _scan_prefixed_items(iterator, self._storage.codec_cached, options)
        except Exception as e:
            raise StorageOperationError(f"Failed to scan items under {options.prefix}: {e}") from e

        for key, value in items:
            yield key, value

    def close(self) -> None:
        if self._closed:
            return

        txn = self._txn
        if txn is None:
            self._closed = True
            self._storage._remove_snapshot(self)
            return

        with self._storage._db_lock:
            try:
                txn.rollback()
            except Exception as e:
                raise SnapshotError(f"Failed to close RocksDB snapshot: {e}") from e
            finally:
                self._closed = True
                self._txn = None
                self._storage._remove_snapshot(self)

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RocksDBStorageSnapshot) and self._uuid == other._uuid


@attrs.define(frozen=True, slots=True, kw_only=True)
class RocksDBStorageSpec(ResourceSpec):
    """Specification for configuring a RocksDBStorage resource."""

    name: str = "rocksdb_storage"
    factory: type = RocksDBStorage
    mode: str = "write"
    path: Path | str = Path(".db")
    wal_path: Path | str | None = None
    codec: Spec
    create_if_missing: bool = True
    options_kwargs: frozendict = attrs.field(factory=frozendict)
    txn_db_options_kwargs: frozendict = attrs.field(factory=frozendict)
    transaction_options_kwargs: frozendict = attrs.field(factory=frozendict)
    snapshot_options_kwargs: frozendict = attrs.field(factory=frozendict)
    sync_writes: bool = False
    disable_wal: bool = False


if TYPE_CHECKING:
    _: type[StorageProtocol] = RocksDBStorage
    __: type[TransactionProtocol] = RocksDBStorageTransaction
    ___: type[SnapshotProtocol] = RocksDBStorageSnapshot
