"""Backend."""

from __future__ import annotations

from .codec import Codec, CodecProtocol, KeyCodecProtocol, ValueCodecProtocol
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
    ScanProtocol,
    SnapshotProtocol,
    StorageClosedError,
    StorageContextType,
    StorageDeleteError,
    StorageError,
    StorageInterfaceError,
    StorageIteratorError,
    StorageKeyError,
    StorageLookupError,
    StorageOperationError,
    StorageProtocol,
    StorageScanOptions,
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
    "StorageInterfaceError",
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
    "StorageScanOptions",
    "StorageContextType",
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
    "Codec",
]
