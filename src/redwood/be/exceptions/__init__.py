"""Exception system for backend components of the redwood package."""

from __future__ import annotations

from .observer import (
    ObserverConnectionError,
    ObserverError,
    ObserverSubscriptionError,
    ObserverValidationError,
)
from .storage import (
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


__all__ = [
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
