"""Storage layer with subscriptions support.

Provides storage protocols, observer patterns, and subscription capabilities.
"""

from __future__ import annotations

from .codec import Codec, CodecProtocol, KeyCodecProtocol, ValueCodecProtocol
from .filter import (
    WILDCARD,
    And,
    Filter,
    LengthFilter,
    Or,
    PassAll,
    PassNone,
    PrefixFilter,
    SuffixFilter,
    WildcardFilter,
)
from .observer import (
    ObserverConnectionError,
    ObserverError,
    ObserverProtocol,
    ObserverSubscriptionError,
    ObserverValidationError,
    Subscription,
    SubscriptionCallback,
    SubscriptionOptions,
    SubscriptionReceiver,
    SubscriptionRegistry,
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
    "SubscriptionOptions",
    "SubscriptionCallback",
    "SubscriptionReceiver",
    "SubscriptionRegistry",
    ## Errors
    "ObserverError",
    "ObserverConnectionError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
    # Filter types
    "Filter",
    "And",
    "Or",
    "PrefixFilter",
    "SuffixFilter",
    "WildcardFilter",
    "LengthFilter",
    "PassAll",
    "PassNone",
    "WILDCARD",
    # Codec
    "CodecProtocol",
    "KeyCodecProtocol",
    "ValueCodecProtocol",
    "Codec",
    # Common types
    "CallbackFn",
]
