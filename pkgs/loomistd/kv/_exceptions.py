from __future__ import annotations

__all__ = [
    "StorageError",
    "StorageConnectionError",
    "StorageOperationError",
    "StorageKeyError",
    "StorageValidationError",
    "TransactionError",
    "TransactionConflictError",
    "TransactionInvalidError",
]


class StorageError(Exception):
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
