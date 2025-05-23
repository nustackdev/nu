from __future__ import annotations

from contextlib import contextmanager

from ..transaction import with_transaction

__all__ = [
    "create_view_context_manager",
]


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
