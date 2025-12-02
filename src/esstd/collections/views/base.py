"""Base class for standard views."""

from __future__ import annotations

from everyshape.view import View


__all__ = [
    "StdView",
]


class StdView(View):
    """Base class for standard views.

    Type Parameters:
        AddressT: Type of addresses/keys this view accepts (default: str | int)
        ValueT: Type of values this view stores/returns (default: Value)
    """

    @classmethod
    def get_available_views(cls) -> tuple[type[View], ...]:
        """Returns tuple of views defined in collections module."""
        from .bytearray_view import ByteArrayView
        from .dict_view import DictView
        from .frozenset_view import FrozenSetView
        from .list_view import ListView
        from .set_view import SetView
        from .tuple_view import TupleView

        return (ByteArrayView, DictView, FrozenSetView, ListView, SetView, TupleView)

    @classmethod
    def get_default_parent_view(cls) -> type[View]:
        """Returns DictView as a default view."""
        from .dict_view import DictView

        return DictView
