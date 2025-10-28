"""Backend integration protocols.

This module defines the abstract interfaces for pluggable backends.
Concrete implementations are in storage, observer, etc.
"""

from __future__ import annotations

from .codec import (
    CodecProtocol,
    KeyCodecProtocol,
    ValueCodecProtocol,
)
from .observer import (
    ObserverProtocol,
    SubscriptionProtocol,
)
from .reactive_storage import ReactiveStorageProtocol
from .storage import (
    StorageProtocol,
)
from .transaction import (
    SnapshotContextManagerProtocol,
    SnapshotHandlerProtocol,
    SnapshotProtocol,
    StorageContextProtocol,
    StorageContextType,
    TransactionalHandlerProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)


__all__ = [
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
]
