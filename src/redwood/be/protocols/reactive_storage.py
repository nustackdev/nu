"""Protocol definitions for coddec, storage, and observer."""

from __future__ import annotations

from typing import Protocol

from .observer import ObserverProtocol
from .storage import StorageProtocol


__all__ = [
    "ReactiveStorageProtocol",
]


class ReactiveStorageProtocol[EncodedKeyT, EncodedValueT](
    StorageProtocol[EncodedKeyT, EncodedValueT], ObserverProtocol[EncodedKeyT], Protocol
):
    """Protocol for reactive storage adapters.

    Combines storage and observer protocols to provide
    a unified interface for reactive state storage.

    Type Parameters:
        EncodedKeyT: The type of encoded keys (covariant)
        EncodedValueT: The type of encoded values (covariant)
    """

    ...
