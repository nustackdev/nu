from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import Generator

from ..transaction import with_snapshot
from ..types import ViewT

__all__ = [
    "create_snapshot_view_context_manager",
]


def create_snapshot_view_context_manager(
    view_factory: type[ViewT], *args, **kwargs
) -> AbstractContextManager[ViewT]:
    """
    Helper function to create snapshot context managers for view methods.

    This is used internally by State class methods like with_dict_view(snapshot=True).

    Args:
        view_factory: Function that creates a view object
        *args: Arguments to pass to view_factory
        **kwargs: Keyword arguments to pass to view_factory

    Returns:
        Context manager that yields a view with snapshot

    Example:
        ```python
        # Used internally by State.with_dict_view(snapshot=True)
        def with_dict_view(self, *, snapshot: bool = False):
            if snapshot:
                return create_snapshot_view_context_manager(
                    DictView,
                    backend=self.backend,
                    path=self.path,
                    snap=self.snap
                )
            else:
                return create_view_context_manager(...)
        ```
    """

    @contextmanager
    def snapshot_view_context() -> Generator[ViewT, None, None]:
        view_obj = view_factory(*args, **kwargs)
        with with_snapshot(view_obj) as snapshot_view:
            yield snapshot_view

    return snapshot_view_context()
