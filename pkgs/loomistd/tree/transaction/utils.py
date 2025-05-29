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

from typing import Optional

import attrs

from ..backend import BackendProtocol
from ..types import TransactionalT

__all__ = [
    "ensure_transaction",
]


def ensure_transaction(
    obj: TransactionalT, backend: Optional[BackendProtocol] = None
) -> TransactionalT:
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
