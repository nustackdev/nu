"""
Unified context managers for both transactions and snapshots.

This module provides context management that works with both transaction
and snapshot contexts, replacing the separate transaction and snapshot
context manager systems.
"""

from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import Generator, Optional

import attrs

from ..backend import BackendProtocol
from ..types import ContextualT
from .protocols import ContextType, SnapshotContextProtocol, TransactionContextProtocol

__all__ = [
    "create_context",
    "create_view_context_manager",
    "with_context",
]


@contextmanager
def create_context(
    backend: BackendProtocol, *, snapshot: bool = False
) -> Generator[ContextType, None, None]:
    """
    Create a context manager for the given backend.

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


def create_view_context_manager(
    view_factory: type[ContextualT], *, snapshot: bool = False, **kwargs
) -> AbstractContextManager[ContextualT]:
    """
    Create a unified context manager for view objects.

    This replaces both create_view_context_manager and create_snapshot_view_context_manager
    with a single unified implementation that handles both transactions and snapshots.

    Args:
        view_factory: Function that creates a view object
        snapshot: If True, creates snapshot context. If False, creates transaction context.
        **kwargs: Arguments to pass to view_factory (must include 'backend')

    Returns:
        Context manager that yields a view with appropriate context

    Example:
        ```python
        # Transaction-based view
        def with_dict_view(self):
            return create_view_context_manager(
                DictView,
                snapshot=False,
                backend=self.backend,
                path=self.path,
                tree=self.__class__
            )

        # Snapshot-based view
        def with_dict_view_snapshot(self):
            return create_view_context_manager(
                DictView,
                snapshot=True,
                backend=self.backend,
                path=self.path,
                tree=self.__class__
            )
        ```
    """

    @contextmanager
    def view_context() -> Generator[ContextualT, None, None]:
        backend = kwargs.get("backend")
        if backend is None:
            raise ValueError("Backend must be provided in kwargs")

        with create_context(backend, snapshot=snapshot) as ctx:
            # Create view with context, ensuring ctx is properly set
            kwargs_with_ctx = {**kwargs, "ctx": ctx}
            view_obj = view_factory(**kwargs_with_ctx)
            yield view_obj

    return view_context()


@contextmanager
def with_context(obj: ContextualT, *, snapshot: bool = False) -> Generator[ContextualT, None, None]:
    """
    Context manager that provides context for an object.

    This replaces both with_transaction and with_snapshot with a unified approach.

    Args:
        obj: Object that has backend and ctx attributes
        snapshot: If True, creates snapshot context. If False, creates transaction context.

    Yields:
        Object with appropriate context

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
    with create_context(obj.backend, snapshot=snapshot) as ctx:
        yield attrs.evolve(obj, ctx=ctx)


# Backward compatibility functions
@contextmanager
def create_transaction_context(
    backend: BackendProtocol,
) -> Generator[TransactionContextProtocol, None, None]:
    """
    Create a transaction context manager from a backend.

    Args:
        backend: Backend to create transaction from

    Yields:
        Transaction instance

    Note:
        This function is provided for backward compatibility.
        New code should use create_context(backend, snapshot=False).
    """
    with create_context(backend, snapshot=False) as ctx:
        assert isinstance(ctx, TransactionContextProtocol)
        yield ctx


@contextmanager
def create_snapshot_context(
    backend: BackendProtocol, snap: Optional[SnapshotContextProtocol] = None
) -> Generator[SnapshotContextProtocol, None, None]:
    """
    Create a snapshot context for the given backend and optional snapshot.

    Args:
        backend: Backend to create snapshots from
        snap: Optional existing snapshot

    Yields:
        Snapshot context

    Note:
        This function is provided for backward compatibility.
        New code should use create_context(backend, snapshot=True).
    """
    if snap is not None:
        # Use provided snapshot (noop pattern)
        yield snap
    else:
        # Create and manage new snapshot
        with create_context(backend, snapshot=True) as ctx:
            assert isinstance(ctx, SnapshotContextProtocol)
            yield ctx


@contextmanager
def with_transaction(obj: ContextualT) -> Generator[ContextualT, None, None]:
    """
    Context manager that provides transaction context for an object.

    Args:
        obj: Object that has backend and ctx attributes

    Yields:
        Object with transaction context

    Note:
        This function is provided for backward compatibility.
        New code should use with_context(obj, snapshot=False).
    """
    with with_context(obj, snapshot=False) as tx_obj:
        yield tx_obj


@contextmanager
def with_snapshot(obj: ContextualT) -> Generator[ContextualT, None, None]:
    """
    Context manager that provides snapshot context for an object.

    Args:
        obj: Object that has backend and ctx attributes

    Yields:
        Object with snapshot context

    Note:
        This function is provided for backward compatibility.
        New code should use with_context(obj, snapshot=True).
    """
    with with_context(obj, snapshot=True) as snap_obj:
        yield snap_obj
