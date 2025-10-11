"""Unified context managers for both transactions and snapshots."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import attrs


if TYPE_CHECKING:
    from collections.abc import Generator

    from ...backend import ObservableStorage
    from ..types import ContextualT
    from .protocols import ContextType


__all__ = [
    "create_context",
    "with_context",
]


@contextmanager
def create_context(
    backend: ObservableStorage, *, snapshot: bool = False
) -> Generator[ContextType, None, None]:
    """Create a context manager for the given backend.

    Args:
        backend: Backend to create context from
        snapshot: If True, creates read-only snapshot. If False, creates transaction.

    Yields:
        Context instance (transaction or snapshot)

    Example:
        ```python
        # Transaction context
        with create_context(my_backend) as ctx:
            ctx.set(key1, value1)
            ctx.set(key2, value2)
            # Auto-commits on success, rollbacks on failure

        # Snapshot context
        with create_context(my_backend, snapshot=True) as ctx:
            value = ctx.get(key1)
            # Read-only operations only
            # Auto-cleanup on exit
        ```
    """
    if snapshot:
        # Create snapshot context
        snap = backend.begin_snapshot()
        try:
            yield snap
        finally:
            snap.close()
    else:
        # Create transaction context
        tx = backend.begin_transaction()
        try:
            yield tx
        except Exception:
            tx.rollback()
            raise
        else:
            tx.commit()


@contextmanager
def with_context(obj: ContextualT, *, snapshot: bool = False) -> Generator[ContextualT, None, None]:
    """Context manager that provides context for an object.

    Args:
        obj: Object that has backend and ctx attributes
        snapshot: If True, creates snapshot context. If False, creates transaction context.

    Yields:
        Object with appropriate context

    Raises:
        TypeError: If object doesn't support contexts or if attrs.evolve fails

    Example:
        ```python
        view = DictView(backend=backend, path=path, ctx=None)

        # Transaction context
        with with_context(view) as tx_view:
            tx_view.set(key, value)

        # Snapshot context
        with with_context(view, snapshot=True) as snap_view:
            value = snap_view.get(key)
        ```
    """
    # Validate object has required context attributes (same robustness as old system)
    if not hasattr(obj, "backend"):
        raise TypeError(
            f"Object {type(obj).__name__} must have 'backend' attribute for context support"
        )

    if not hasattr(obj, "ctx"):
        raise TypeError(
            f"Object {type(obj).__name__} must have 'ctx' attribute for context support"
        )

    backend = obj.backend
    current_ctx = obj.ctx

    if current_ctx is not None:
        # Noop - use existing context (like original with_transaction)
        yield obj
    else:
        # Create new context and manage its lifecycle
        new_ctx = backend.begin_snapshot() if snapshot else backend.begin_transaction()

        try:
            # Attempt to create object copy with context (robust like old system)
            obj_with_ctx = attrs.evolve(obj, ctx=new_ctx)
        except Exception as e:
            # If we can't create the copy, clean up the context immediately
            try:
                if snapshot:
                    new_ctx.close()
                else:
                    new_ctx.rollback()
            except Exception:
                pass  # Cleanup failed, but original error is more important

            context_type = "snapshot" if snapshot else "transaction"
            raise TypeError(
                f"Failed to create {context_type} copy of {type(obj).__name__}: {e}"
            ) from e

        created_ctx = True

        try:
            yield obj_with_ctx
        except Exception:
            # Cleanup only if we created the context
            if created_ctx:
                try:
                    if snapshot:
                        new_ctx.close()
                    else:
                        new_ctx.rollback()
                except Exception:
                    # Cleanup failed, but we still want to propagate the original exception
                    pass
            raise
        else:
            # Finalize only if we created the context
            if created_ctx:
                if snapshot:
                    new_ctx.close()
                else:
                    new_ctx.commit()
