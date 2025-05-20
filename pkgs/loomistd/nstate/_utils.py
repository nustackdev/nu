"""
Utilities for the state management system.

This module contains shared utilities and helper functions used throughout
the state management system, including:
- Empty sentinel for distinguishing between None and nonexistent values
- Transaction context management
- Type guards and helpers
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Optional, TypeGuard

from ._state.backend import ObservableKVBackend, ObservableKVTransaction


class Empty:
    """
    Sentinel object representing an empty value, distinct from None.

    Used for distinguishing between a legitimate None value and a
    nonexistent value in operations that may return None normally.
    """

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<Empty>"

    def __str__(self) -> str:
        """String representation for display."""
        return "Empty"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False


def is_empty(value: Any) -> TypeGuard[Empty]:
    """
    Check if a value is the EMPTY sentinel.

    Args:
        value: Value to check

    Returns:
        True if value is the EMPTY sentinel, False otherwise
    """
    return isinstance(value, Empty)


class TransactionContext:
    """
    Context manager for transaction handling.

    This class provides a consistent way to handle transactions
    throughout the state management system, with automatic
    commit/rollback handling.
    """

    def __init__(
        self,
        backend: ObservableKVBackend,
        transaction: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize the transaction context.

        Args:
            backend: The backend storage interface
            transaction: Optional existing transaction to use
        """
        self._backend = backend
        self._transaction = transaction
        self._created_transaction = False

    def __enter__(self) -> ObservableKVTransaction:
        """
        Enter the context and get a transaction.

        Returns the existing transaction if provided, or creates
        a new one if no transaction was provided.

        Returns:
            ObservableKVTransaction: The transaction to use
        """
        if self._transaction is not None:
            return self._transaction

        # Create a new transaction
        self._transaction = self._backend.begin_transaction()
        self._created_transaction = True
        return self._transaction

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """
        Exit the context, handling commit/rollback.

        If an exception was raised, the transaction is rolled back.
        Otherwise, the transaction is committed.

        Only manages transactions that were created by this context.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised

        Returns:
            bool: False to allow exceptions to propagate, True to suppress them
                (this implementation always returns False to allow exceptions to propagate)
        """
        if not self._created_transaction:
            # We didn't create this transaction, so don't manage it
            return False

        if self._transaction is None:
            # No transaction to manage
            return False

        try:
            if exc_type is not None:
                # Exception occurred, rollback
                self._transaction.rollback()
                return False  # Allow exception to propagate
            # No exception, commit
            self._transaction.commit()
            return False  # No exception to propagate
        finally:
            # Clear the transaction reference
            self._transaction = None
