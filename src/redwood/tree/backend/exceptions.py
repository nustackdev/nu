from __future__ import annotations


__all__ = [
    "StorageError",
    "StorageKeyError",
]


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageKeyError(StorageError):
    """Raised when storage key does not exist."""

    pass
