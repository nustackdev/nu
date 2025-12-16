"""Storage layer with subscriptions support.

Provides storage protocols, observer patterns, and subscription capabilities.
"""

from __future__ import annotations

from .codec import Codec, CodecProtocol, KeyCodecProtocol, ValueCodecProtocol
from .observer import (
    WILDCARD,
    CompositeFilter,
    LengthFilter,
    ObserverConnectionError,
    ObserverError,
    ObserverProtocol,
    ObserverSubscriptionError,
    ObserverValidationError,
    PrefixFilter,
    Subscription,
    SubscriptionCallback,
    SubscriptionFilter,
    SubscriptionOptions,
    SubscriptionReceiver,
    SubscriptionRegistry,
    SuffixFilter,
    WildcardFilter,
)
from .storage import (
    BaseContextProtocol,
    ReadAccessProtocol,
    ReadWriteAccessProtocol,
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
    TransactionProtocol,
    WriteAccessProtocol,
    WriteBatchProtocol,
)
from .types import CallbackFn


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
    "ReadWriteAccessProtocol",
    "SnapshotProtocol",
    "WriteBatchProtocol",
    "TransactionProtocol",
    "TransactionalStorageProtocol",
    ## Types
    "StorageScanOptions",
    "StorageContextType",
    # Observer
    "ObserverProtocol",
    "Subscription",
    ## Subscription types
    "Subscription",
    "SubscriptionOptions",
    "SubscriptionCallback",
    "SubscriptionReceiver",
    "SubscriptionRegistry",
    ## Filter types
    "SubscriptionFilter",
    "PrefixFilter",
    "SuffixFilter",
    "WildcardFilter",
    "LengthFilter",
    "CompositeFilter",
    "WILDCARD",
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
    # Common types
    "CallbackFn",
]
