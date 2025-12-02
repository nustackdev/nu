"""Unified context managers for both transactions and snapshots."""

from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from logging import getLogger
from typing import TYPE_CHECKING, Any

import attrs


logger = getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Generator

    from everyshape.storage import StorageContextType, StorageProtocol


def create_view_context_manager(
    view_factory: type, *, snapshot: bool = False, **kwargs: object
) -> AbstractContextManager[Any]:
    """Create a unified context manager for view objects.

    Args:
        view_factory: Function that creates a view object
        snapshot: If True, creates snapshot context. If False, creates transaction context.
        **kwargs: Arguments to pass to view_factory

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
                tree=self.__class__,
            )


        # Snapshot-based view
        def with_dict_view_snapshot(self):
            return create_view_context_manager(
                DictView,
                snapshot=True,
                backend=self.backend,
                path=self.path,
                tree=self.__class__,
            )
        ```
    """

    @contextmanager
    def view_context() -> Generator[object, None, None]:
        # Step 1: Create view (potentially with None context)
        view_obj = view_factory(**kwargs)

        # Step 2: Wrap view with context management
        with with_context(view_obj, snapshot=snapshot) as context_wrapped_view:
            yield context_wrapped_view

    return view_context()


@contextmanager
def create_context(
    backend: StorageProtocol, *, snapshot: bool = False
) -> Generator[StorageContextType, None, None]:
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
            tx.abort()
            raise
        else:
            tx.commit()


@contextmanager
def with_context(obj: Any, *, snapshot: bool = False) -> Generator[Any, None, None]:  # noqa: ANN401
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

    backend: StorageProtocol = obj.backend
    current_ctx: StorageContextType = obj.ctx

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
            except Exception as e:
                logger.error(f"Error during storage context cleanup: {e}")
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
                except Exception as e:
                    logger.error(f"Error during storage context cleanup: {e}")
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
