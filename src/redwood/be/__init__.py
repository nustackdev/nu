"""Backend."""

from __future__ import annotations

from .codec import CodecProtocol, KeyCodecProtocol, ValueCodecProtocol
from .observer import (
    ObserverConnectionError,
    ObserverError,
    ObserverProtocol,
    ObserverSubscriptionError,
    ObserverValidationError,
    SubscriptionProtocol,
)
from .storage import (
    BaseContextProtocol,
    ReadAccessProtocol,
    ScanOptions,
    ScanProtocol,
    SnapshotProtocol,
    StorageClosedError,
    StorageDeleteError,
    StorageError,
    StorageIteratorError,
    StorageKeyError,
    StorageLookupError,
    StorageOperationError,
    StorageProtocol,
    StorageTransactionAbortedError,
    StorageTransactionConflictError,
    StorageTransactionError,
    StorageWriteError,
    TransactionalStorageProtocol,
    TransactionControlProtocol,
    TransactionProtocol,
    WriteAccessProtocol,
    WriteBatchProtocol,
)


__all__ = [  # noqa: RUF022
    # Storage
    "StorageProtocol",
    "ScanProtocol",
    ## Errors
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
    ## Transaction Protocols
    "BaseContextProtocol",
    "ReadAccessProtocol",
    "WriteAccessProtocol",
    "TransactionControlProtocol",
    "SnapshotProtocol",
    "WriteBatchProtocol",
    "TransactionProtocol",
    "TransactionalStorageProtocol",
    ## Types
    "ScanOptions",
    # Observer
    "ObserverProtocol",
    "SubscriptionProtocol",
    ## Errors
    "ObserverError",
    "ObserverConnectionError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
    # Codec
    "CodecProtocol",
    "KeyCodecProtocol",
    "ValueCodecProtocol",
]
