from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import Generator

from ..context import with_context
from ..types import ContextualT

__all__ = [
    "create_view_context_manager",
]


def create_view_context_manager(
    view_factory: type[ContextualT], *, snapshot: bool = False, **kwargs
) -> AbstractContextManager[ContextualT]:
    """
    Create a unified context manager for view objects.

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
        # Step 1: Create view (potentially with None context)
        view_obj = view_factory(**kwargs)

        # Step 2: Wrap view with context management
        with with_context(view_obj, snapshot=snapshot) as context_wrapped_view:
            yield context_wrapped_view

    return view_context()
