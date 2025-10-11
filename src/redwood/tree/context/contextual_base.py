"""Base class for objects that support unified context management.

This module provides ContextualBase, which replaces TransactionalBase
with support for both transactions and snapshots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, TypeGuard

import attrs

from .protocols import ContextType, SnapshotContextProtocol, TransactionContextProtocol


if TYPE_CHECKING:
    from ..backend import ObservableStorage


__all__ = ["ContextualBase", "is_contextual"]


@attrs.define(frozen=True, kw_only=True)
class ContextualBase:
    """Base class for immutable objects with unified context support.

    This provides context attributes and utilities for both transaction
    and snapshot contexts, but does NOT implement context manager methods
    (__enter__/__exit__). This keeps views as pure frozen dataclasses while
    providing context support.

    Context manager functionality is provided by the State class methods like
    with_dict_view(), which use unified context managers internally.

    Example:
        ```python
        @attrs.define(frozen=True, kw_only=True)
        class DictView(ContextualBase):
            path: StatePath

            def set(self, key, value):
                # Automatically validates context supports writes
                tx = self.get_transaction_context()
                tx.set(key, value)

            def get(self, key):
                # Works with both transaction and snapshot contexts
                ctx = self.get_ensured_context()
                return ctx.get(key)


        # Direct usage
        view = DictView(backend=my_backend, path=my_path)
        view.get("key")  # Works if context is available

        # Context manager usage (via State methods)
        with state.with_dict_view() as view:
            view.set("key", "value")  # Automatic transaction context

        with state.with_dict_view(snapshot=True) as view:
            value = view.get("key")  # Read-only snapshot context
        ```
    """

    # Backend instance for context management
    backend: ObservableStorage = attrs.field()

    # Current context if any (transaction or snapshot)
    ctx: ContextType | None = attrs.field(default=None)

    def with_context(self, ctx: ContextType) -> Self:
        """Create a copy of this object with a specific context.

        Args:
            ctx: Context to use (transaction or snapshot)

        Returns:
            New object with the specified context

        Example:
            ```python
            tx = backend.begin_transaction()
            try:
                tx_view = view.with_context(tx)
                tx_view.set("key", "value")
                tx.commit()
            except Exception:
                tx.rollback()
                raise
            ```
        """
        return attrs.evolve(self, ctx=ctx)

    def without_context(self) -> Self:
        """Create a copy of this object without any context.

        Returns:
            New object with no context

        Example:
            ```python
            clean_view = ctx_view.without_context()
            # clean_view has no context
            ```
        """
        return attrs.evolve(self, ctx=None)

    def has_context(self) -> bool:
        """Check if this object has an active context.

        Returns:
            True if object has a context (transaction or snapshot)
        """
        return self.ctx is not None

    def get_ensured_context(self) -> ContextType:
        """Get context or raise error if none available.

        Returns:
            Active context (transaction or snapshot)

        Raises:
            ValueError: If no context is available

        Example:
            ```python
            ctx = obj.get_ensured_context()
            value = ctx.get(key)  # Works with any context type
            ```
        """
        if self.ctx is None:
            raise ValueError("Object has no context")
        return self.ctx

    def is_transaction_context(self) -> bool:
        """Check if current context supports write operations.

        Returns:
            True if context is a transaction (supports writes)

        Example:
            ```python
            if obj.is_transaction_context():
                obj.set("key", "value")  # Safe to write
            else:
                value = obj.get("key")  # Read-only
            ```
        """
        return isinstance(self.ctx, TransactionContextProtocol)

    def is_snapshot_context(self) -> bool:
        """Check if current context is read-only.

        Returns:
            True if context is a snapshot (read-only)

        Example:
            ```python
            if obj.is_snapshot_context():
                # Read-only operations only
                value = obj.get("key")
            ```
        """
        return isinstance(self.ctx, SnapshotContextProtocol)

    def get_transaction_context(self) -> TransactionContextProtocol:
        """Get transaction context or raise error if context is read-only.

        Returns:
            Transaction context that supports write operations

        Raises:
            ValueError: If no context available or context is read-only

        Example:
            ```python
            try:
                tx = obj.get_transaction_context()
                tx.set(key, value)  # Safe to write
            except ValueError:
                # Context is read-only (snapshot)
                handle_read_only_context()
            ```
        """
        ctx = self.get_ensured_context()
        if not isinstance(ctx, TransactionContextProtocol):
            raise ValueError(
                "Context is read-only (snapshot). Write operations not allowed. "
                "Use a transaction context for write operations."
            )
        return ctx


def is_contextual(obj: object) -> TypeGuard[ContextualBase]:
    """Check if an object supports contexts.

    Args:
        obj: Object to check

    Returns:
        True if object supports contexts

    Example:
        ```python
        if is_contextual(my_obj):
            with with_context(my_obj) as ctx_obj:
                ctx_obj.do_work()
        else:
            my_obj.do_work()
        ```
    """
    return hasattr(obj, "backend") and hasattr(obj, "ctx")
