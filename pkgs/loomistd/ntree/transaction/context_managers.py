"""
Context managers for transaction handling in the tree package.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

import attrs

from ..backend import BackendProtocol, TransactionProtocol
from ..types import TransactionalT

__all__ = [
    "TransactionContext",
    "with_transaction",
    "create_transaction_context",
]


class TransactionContext:
    """
    Context manager for conditional transaction handling.

    If a transaction is provided, uses that transaction with no additional
    management (noop pattern). If no transaction is provided, creates a new
    transaction and manages its lifecycle (commit on success, rollback on error).

    Args:
        backend: The backend to create transactions from
        tx: Optional existing transaction. If None, a new transaction is created

    Example:
        ```python
        # With existing transaction (noop - no commit/rollback)
        existing_tx = backend.begin_transaction()
        with TransactionContext(backend, tx=existing_tx) as tx:
            tx.set(("key",), "value")
        # No automatic commit - caller manages existing_tx

        # Without transaction (auto-managed)
        with TransactionContext(backend) as tx:
            tx.set(("key",), "value")
        # Automatically committed on success, rolled back on exception
        ```
    """

    def __init__(
        self,
        backend: BackendProtocol,
        tx: Optional[TransactionProtocol] = None,
        /,
    ):
        """
        Initialize the transaction context manager.

        Args:
            backend: The backend to create transactions from
            tx: Optional existing transaction
        """
        self.backend = backend
        self.provided_tx = tx
        self.managed_tx: Optional[TransactionProtocol] = None
        self.should_manage = tx is None

    def __enter__(self) -> TransactionProtocol:
        """
        Enter the context and return the transaction to use.

        Returns:
            TransactionProtocol: Transaction to use for operations
        """
        if self.provided_tx is not None:
            # Use provided transaction
            return self.provided_tx
        else:
            # Create and manage new transaction
            self.managed_tx = self.backend.begin_transaction()
            return self.managed_tx

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context and handle transaction cleanup.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.should_manage and self.managed_tx is not None:
            # Only manage transaction if we created it
            if exc_type is None:
                # No exception - commit
                self.managed_tx.commit()
            else:
                # Exception occurred - rollback
                self.managed_tx.rollback()

        # Return False to propagate exception
        return False


@contextmanager
def with_transaction(obj: TransactionalT) -> Generator[TransactionalT, None, None]:
    """
    Generic transaction context manager for any object with transaction support.

    This is the core utility that handles transaction lifecycle for frozen objects.
    If the object already has a transaction, uses it. Otherwise creates a new one
    and returns a copy with the transaction set.

    Args:
        obj: Any object with backend and tx attributes

    Yields:
        Object with transaction context (either original or copy)

    Raises:
        TypeError: If object doesn't support transactions

    Example:
        ```python
        # Used internally by State.with_dict_view()
        @contextmanager
        def with_dict_view(self):
            dict_view_obj = DictView(backend=self.backend, path=self.path, tx=self.tx)
            with with_transaction(dict_view_obj) as tx_view:
                yield tx_view

        # Direct usage (advanced)
        dict_view_obj = DictView(backend=my_backend, path=my_path)
        with with_transaction(dict_view_obj) as tx_view:
            tx_view.set("key", "value")
        ```
    """
    # Validate object has required transaction attributes
    if not hasattr(obj, "backend"):
        raise TypeError(
            f"Object {type(obj).__name__} must have 'backend' attribute for transaction support"
        )

    if not hasattr(obj, "tx"):
        raise TypeError(
            f"Object {type(obj).__name__} must have 'tx' attribute for transaction support"
        )

    backend = getattr(obj, "backend")
    current_tx = getattr(obj, "tx")

    if current_tx is None:
        # Need to create transaction - return copy with transaction set
        new_tx = backend.begin_transaction()
        try:
            obj_with_tx = attrs.evolve(obj, tx=new_tx)
        except Exception as e:
            # If we can't create the copy, clean up the transaction
            try:
                new_tx.rollback()
            except Exception:
                pass  # Rollback failed, but original error is more important
            raise TypeError(
                f"Failed to create transaction copy of {type(obj).__name__}: {e}"
            ) from e

        created_tx = True
    else:
        # Already have transaction - use as-is
        obj_with_tx = obj
        new_tx = current_tx
        created_tx = False

    try:
        yield obj_with_tx
    except Exception:
        # Rollback only if we created the transaction
        if created_tx:
            try:
                new_tx.rollback()
            except Exception:
                # Rollback failed, but we still want to propagate the original exception
                pass
        raise
    else:
        # Commit only if we created the transaction
        if created_tx:
            new_tx.commit()


@contextmanager
def create_transaction_context(
    backend: BackendProtocol,
) -> Generator[TransactionProtocol, None, None]:
    """
    Create a transaction context manager from a backend.

    Args:
        backend: Backend to create transaction from

    Yields:
        Transaction instance

    Example:
        ```python
        with create_transaction_context(my_backend) as tx:
            # Use tx with multiple objects
            view1 = obj1.with_transaction(tx)
            view2 = obj2.with_transaction(tx)
            view1.do_something()
            view2.do_something_else()
            # tx committed automatically on success
        ```
    """
    tx = backend.begin_transaction()
    try:
        yield tx
    except Exception:
        tx.rollback()
        raise
    else:
        tx.commit()
