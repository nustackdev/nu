"""
Clean transaction management for frozen dataclasses using contextlib.

This module provides transaction handling for immutable dataclass objects using
a pure contextlib-based approach with clear separation between direct access
and context manager usage.

Typical usage:
    # Context manager usage (automatic transaction)
    with state.with_dict_view() as users:
        users.set("alice", {"name": "Alice"})
        users.set("bob", {"name": "Bob"})
    # Transaction automatically committed

    # Direct usage (manual transaction management)
    users = state.dict_view()
    users.set("alice", {"name": "Alice"})  # No automatic transaction

    # Manual transaction with direct access
    tx = state.begin_transaction()
    try:
        users = state.dict_view(tx=tx)
        users.set("alice", {"name": "Alice"})
        tx.commit()
    except Exception:
        tx.rollback()
        raise
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Optional, TypeVar

import attrs

from .._state.backend import ObservableKVBackend, ObservableKVTransaction

__all__ = ["with_transaction", "TransactionalBase", "create_transaction_context"]

T = TypeVar("T", bound="TransactionalBase")


@contextmanager
def with_transaction(obj: T) -> Generator[T, None, None]:
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


@attrs.define(frozen=True, kw_only=True)
class TransactionalBase:
    """
    Base class for immutable objects with transaction support.

    This provides the basic transaction attributes and utilities, but does NOT
    implement context manager methods (__enter__/__exit__). This keeps views
    as pure frozen dataclasses while providing transaction support.

    Context manager functionality is provided by the State class methods like
    with_dict_view(), which use the with_transaction() function internally.

    Example:
        ```python
        @attrs.define(frozen=True, kw_only=True)
        class DictView(TransactionalBase):
            path: StatePath

            def set(self, key, value):
                # Your business logic here
                pass

        # Direct usage
        view = DictView(backend=my_backend, path=my_path)
        view.set("key", "value")  # No automatic transaction

        # Context manager usage (via State methods)
        with state.with_dict_view() as view:
            view.set("key", "value")  # Automatic transaction
        ```
    """

    # Backend instance for transaction management
    backend: ObservableKVBackend = attrs.field(eq=False, hash=False)

    # Current transaction if any
    tx: Optional[ObservableKVTransaction] = attrs.field(default=None, eq=False, hash=False)

    def with_transaction(self, tx: ObservableKVTransaction):
        """
        Create a copy of this object with a specific transaction.

        Args:
            tx: Transaction to use

        Returns:
            New object with the specified transaction

        Example:
            ```python
            tx = backend.begin_transaction()
            try:
                tx_view = view.with_transaction(tx)
                tx_view.set("key", "value")
                tx.commit()
            except Exception:
                tx.rollback()
                raise
            ```
        """
        return attrs.evolve(self, tx=tx)

    def without_transaction(self):
        """
        Create a copy of this object without any transaction.

        Returns:
            New object with no transaction

        Example:
            ```python
            clean_view = tx_view.without_transaction()
            # clean_view has no transaction context
            ```
        """
        return attrs.evolve(self, tx=None)

    def has_transaction(self) -> bool:
        """
        Check if this object has an active transaction.

        Returns:
            True if object has a transaction
        """
        return self.tx is not None


@contextmanager
def create_transaction_context(
    backend: ObservableKVBackend,
) -> Generator[ObservableKVTransaction, None, None]:
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


def ensure_transaction(obj: T, backend: Optional[ObservableKVBackend] = None) -> T:
    """
    Ensure an object has a transaction, creating one if needed.

    This is a utility function for cases where you need to guarantee
    an object has a transaction but don't want to use a context manager.

    Args:
        obj: Object to ensure has a transaction
        backend: Backend to use if creating new transaction (optional if obj has backend)

    Returns:
        Object with transaction (either original or copy)

    Raises:
        ValueError: If no backend available and object has no transaction
        TypeError: If object doesn't support transactions

    Example:
        ```python
        # Ensure object has transaction for a single operation
        tx_obj = ensure_transaction(my_obj)
        result = tx_obj.do_something()

        # Note: You need to manage commit/rollback manually
        if not my_obj.has_transaction():
            # We created the transaction, so we should commit it
            tx_obj.tx.commit()
        ```
    """
    if not hasattr(obj, "tx"):
        raise TypeError(f"Object {type(obj).__name__} doesn't support transactions")

    if obj.tx is not None:
        return obj

    # Need to create transaction
    if backend is None:
        if hasattr(obj, "backend"):
            backend = obj.backend
        else:
            raise ValueError("No backend available to create transaction")

    tx = backend.begin_transaction()
    return attrs.evolve(obj, tx=tx)


def is_transactional(obj: Any) -> bool:
    """
    Check if an object supports transactions.

    Args:
        obj: Object to check

    Returns:
        True if object supports transactions

    Example:
        ```python
        if is_transactional(my_obj):
            with with_transaction(my_obj) as tx_obj:
                tx_obj.do_work()
        else:
            my_obj.do_work()
        ```
    """
    return hasattr(obj, "backend") and hasattr(obj, "tx")


# Utility type for context manager creation
def create_view_context_manager(view_factory, *args, **kwargs):
    """
    Helper function to create context managers for view methods.

    This is used internally by State class methods like with_dict_view().

    Args:
        view_factory: Function that creates a view object
        *args: Arguments to pass to view_factory
        **kwargs: Keyword arguments to pass to view_factory

    Returns:
        Context manager that yields a view with transaction

    Example:
        ```python
        # Used internally by State.with_dict_view()
        def with_dict_view(self):
            return create_view_context_manager(
                DictView,
                backend=self.backend,
                path=self.path,
                tx=self.tx
            )
        ```
    """

    @contextmanager
    def view_context():
        view_obj = view_factory(*args, **kwargs)
        with with_transaction(view_obj) as transactional_view:
            yield transactional_view

    return view_context()


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
        backend: ObservableKVBackend,
        tx: Optional[ObservableKVTransaction] = None,
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
        self.managed_tx: Optional[ObservableKVTransaction] = None
        self.should_manage = tx is None

    def __enter__(self) -> ObservableKVTransaction:
        """
        Enter the context and return the transaction to use.

        Returns:
            ObservableKVTransaction: Transaction to use for operations
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
