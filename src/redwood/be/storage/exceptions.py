"""Storage exception hierarchy.

Defines an exception system for storage operations.
Exceptions are designed to be backend-agnostic and composable.
"""

from __future__ import annotations

from redwood._rw_exception import RedwoodError


class StorageError(RedwoodError):
    """Base exception for all storage errors."""


class StorageInterfaceError(StorageError):
    """Permission error.

    Raised when called operation violates context interface,
    e.g. calling get() on BatchWrite or put() on Snapshot.
    """


class StorageOperationError(StorageError):
    """General operation failure.

    Raised when a storage operation fails for reasons not covered by
    more specific exceptions.
    """


class StorageKeyError(StorageError, KeyError):
    """Key not found or key-related error.

    Raised when attempting to access a key that doesn't exist, or when
    a key-related constraint is violated.
    """


class StorageLookupError(StorageOperationError, LookupError):
    """Lookup/retrieval operation failed.

    Raised when data retrieval fails for reasons other than missing keys.
    """


class StorageWriteError(StorageOperationError):
    """Write operation failed.

    Raised when put, delete, or other write operations fail.
    """


class StorageDeleteError(StorageWriteError):
    """Delete operation failed.

    Raised specifically when deletion fails.
    """


class StorageTransactionError(StorageError):
    """Transaction-related error.

    Base class for all transaction-specific errors.
    """


class StorageTransactionConflictError(StorageTransactionError):
    """Transaction conflict detected.

    Raised when optimistic locking detects conflicting concurrent modifications.
    """


class StorageTransactionAbortedError(StorageTransactionError):
    """Transaction was aborted.

    Raised when a transaction is explicitly aborted or rolled back.
    """


class StorageClosedError(StorageError):
    """Operation attempted on closed resource.

    Raised when operations are attempted on closed storage, transactions,
    or iterators.
    """


class StorageIteratorError(StorageError):
    """Iterator operation failed.

    Raised when iterator operations encounter errors.
    """


__all__ = [
    "StorageClosedError",
    "StorageDeleteError",
    "StorageError",
    "StorageIteratorError",
    "StorageKeyError",
    "StorageLookupError",
    "StorageOperationError",
    "StoragePermissionError",
    "StorageTransactionAbortedError",
    "StorageTransactionConflictError",
    "StorageTransactionError",
    "StorageWriteError",
]
