"""Backend integration protocols.

This module defines the abstract interfaces for pluggable backends.
Concrete implementations are in storage, observer, etc.
"""

from __future__ import annotations

from .context import (
    SnapshotProtocol,
    StorageContextProtocol,
    StorageContextType,
    TransactionProtocol,
)
from .protocols import (
    CodecProtocol,
    KeyCodecProtocol,
    ObserverProtocol,
    SnapshotContextManagerProtocol,
    SnapshotHandlerProtocol,
    StorageProtocol,
    SubscriptionProtocol,
    TransactionalHandlerProtocol,
    TransactionContextManagerProtocol,
    ValueCodecProtocol,
)
from .types import (
    StorageMode,
)


__all__ = [  # noqa: RUF022
    # Protocols
    "KeyCodecProtocol",
    "ValueCodecProtocol",
    "CodecProtocol",
    "StorageProtocol",
    "SnapshotContextManagerProtocol",
    "SnapshotHandlerProtocol",
    "TransactionContextManagerProtocol",
    "TransactionalHandlerProtocol",
    "ObserverProtocol",
    "SubscriptionProtocol",
    # Contexts
    "SnapshotProtocol",
    "StorageContextProtocol",
    "StorageContextType",
    "TransactionProtocol",
    # Types
    "StorageMode",
]
