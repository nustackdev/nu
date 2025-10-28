"""Storage-specific exceptions."""

from __future__ import annotations

from redwood._rw_exception import RedwoodError


__all__ = [
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


class StorageError(RedwoodError):
    """Base exception for storage errors."""

    pass


class StorageConnectionError(StorageError):
    """Raised when storage connection fails."""

    pass


class StorageOperationError(StorageError):
    """Raised when storage operation fails."""

    pass


class StorageKeyError(StorageOperationError):
    """Raised when storage key does not exist."""

    pass


class StorageValidationError(StorageOperationError):
    """Raised when storage key does not exist."""

    pass


class SnapshotError(StorageError):
    """Raised when snapshot operation fails."""

    pass


class TransactionError(StorageError):
    """Raised when transaction fails."""

    pass


class TransactionConflictError(TransactionError):
    """Raised when transaction is invalid."""

    pass


class TransactionInvalidError(TransactionError):
    """Raised when transaction is invalid."""

    pass
