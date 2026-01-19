"""Storage layer protocols and types.

This module defines the abstract interfaces and types for the storage layer.
Implementations (LMDB, RocksDB, etc.) must conform to these protocols.

The storage layer is organized around three orthogonal concerns:

1. Access Interface (how you interact with data):
   - Point: get, put, has, delete
   - Batch: multiget, multiput, multidelete
   - Range: iterator, scan, range_delete

2. Transaction/Isolation (consistency guarantees):
   - Read-only snapshots (SnapshotProtocol)
   - Read-write transactions (TransactionProtocol)
   - Write-only batches (WriteBatchProtocol)
   - ACID guarantees with configurable isolation levels

3. Subscriptions (reactivity):
   - Subscribe to key pattern changes
   - Receive notifications on mutations
   - Pattern-based matching
"""

from __future__ import annotations

from .context import (
    BaseContextProtocol,
    ReadAccessProtocol,
    ReadWriteAccessProtocol,
    SnapshotProtocol,
    TransactionalStorageProtocol,
    TransactionProtocol,
    WriteAccessProtocol,
    WriteBatchProtocol,
)
from .exceptions import (
    StorageClosedError,
    StorageDeleteError,
    StorageError,
    StorageInterfaceError,
    StorageIteratorError,
    StorageKeyError,
    StorageLookupError,
    StorageOperationError,
    StorageTransactionAbortedError,
    StorageTransactionConflictError,
    StorageTransactionError,
    StorageWriteError,
)
from .scan import ScanProtocol
from .storage import (
    StorageProtocol,
)
from .types import (
    StorageContextType,
    StorageScanOptions,
)


__all__ = [  # noqa: RUF022
    # Exceptions
    "StorageClosedError",
    "StorageDeleteError",
    "StorageError",
    "StorageIteratorError",
    "StorageKeyError",
    "StorageLookupError",
    "StorageOperationError",
    "StorageTransactionAbortedError",
    "StorageTransactionConflictError",
    "StorageTransactionError",
    "StorageWriteError",
    "StorageInterfaceError",
    # Core Protocols
    "StorageProtocol",
    "ScanProtocol",
    # Transaction Protocols
    "BaseContextProtocol",
    "ReadAccessProtocol",
    "WriteAccessProtocol",
    "ReadWriteAccessProtocol",
    "SnapshotProtocol",
    "WriteBatchProtocol",
    "TransactionProtocol",
    "TransactionalStorageProtocol",
    # Types
    "StorageScanOptions",
    "StorageContextType",
]
