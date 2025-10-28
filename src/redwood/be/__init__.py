"""Backend integration protocols.

This module defines the abstract interfaces for pluggable backends.
Concrete implementations are in storage, observer, etc.
"""

from __future__ import annotations

from .exceptions import (
    ObserverConnectionError,
    ObserverError,
    ObserverSubscriptionError,
    ObserverValidationError,
    SnapshotError,
    StorageConnectionError,
    StorageError,
    StorageKeyError,
    StorageOperationError,
    StorageValidationError,
    TransactionConflictError,
    TransactionError,
    TransactionInvalidError,
)
from .protocols import (
    CodecProtocol,
    KeyCodecProtocol,
    ObserverProtocol,
    ReactiveStorageProtocol,
    SnapshotContextManagerProtocol,
    SnapshotHandlerProtocol,
    SnapshotProtocol,
    StorageContextProtocol,
    StorageContextType,
    StorageProtocol,
    SubscriptionProtocol,
    TransactionalHandlerProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
    ValueCodecProtocol,
)
from .types import (
    StorageCapabilities,
    StorageDescriptor,
    StorageMode,
    StorageScanOptions,
)


__all__ = [  # noqa: RUF022
    # Protocols
    "CodecProtocol",
    "KeyCodecProtocol",
    "ObserverProtocol",
    "ReactiveStorageProtocol",
    "SnapshotContextManagerProtocol",
    "SnapshotHandlerProtocol",
    "SnapshotProtocol",
    "StorageContextProtocol",
    "StorageContextType",
    "StorageProtocol",
    "SubscriptionProtocol",
    "TransactionContextManagerProtocol",
    "TransactionProtocol",
    "TransactionalHandlerProtocol",
    "ValueCodecProtocol",
    # Types
    "StorageScanOptions",
    "StorageCapabilities",
    "StorageDescriptor",
    "StorageMode",
    # Exceptions
    "ObserverConnectionError",
    "ObserverError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
    "SnapshotError",
    "StorageConnectionError",
    "StorageError",
    "StorageKeyError",
    "StorageOperationError",
    "StorageValidationError",
    "TransactionConflictError",
    "TransactionError",
    "TransactionInvalidError",
]
