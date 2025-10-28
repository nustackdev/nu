"""Backend integration protocols.

This module defines the abstract interfaces for pluggable backends.
Concrete implementations are in storage, observer, etc.
"""

from __future__ import annotations

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
    ScanOptions,
    StorageCapabilities,
    StorageDescriptor,
    StorageMode,
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
    "ScanOptions",
    "StorageCapabilities",
    "StorageDescriptor",
    "StorageMode",
]
