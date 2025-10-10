from __future__ import annotations

from typing import Any, Protocol

from .kv import StorageProtocol
from .observer import ObserverProtocol


__all__ = [
    "ObservableStorageProtocol",
]


class ObservableStorageProtocol(StorageProtocol, ObserverProtocol, Protocol):
    """Protocol for observable state storage adapters."""

    def __hash__(self) -> int:
        """Get hash of the storage.

        Returns:
            Hash value of the storage
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """Check equality of the storage.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...
