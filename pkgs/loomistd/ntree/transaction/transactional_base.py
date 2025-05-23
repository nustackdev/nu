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

from typing import Any, Optional, TypeGuard

import attrs

from ..backend import BackendProtocol, TransactionProtocol

__all__ = ["TransactionalBase", "is_transactional"]


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
    backend: BackendProtocol = attrs.field(eq=False, hash=False)

    # Current transaction if any
    tx: Optional[TransactionProtocol] = attrs.field(default=None, eq=False, hash=False)

    def with_transaction(self, tx: TransactionProtocol):
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


def is_transactional(obj: Any) -> TypeGuard[TransactionalBase]:
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
