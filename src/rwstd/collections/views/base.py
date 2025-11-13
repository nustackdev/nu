"""Base class for standard views."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from redwood.view import View


if TYPE_CHECKING:
    from redwood.storage import StorageContextType


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
    def create(
        cls,
        ctx: StorageContextType,
        views: tuple[type[View], ...] = (),
        default_parent_view: type[View] | None = None,
    ) -> Self:
        """Create a new View instance of this type."""
        # Import here to avoid circular imports
        from .bytearray_view import ByteArrayView
        from .dict_view import DictView
        from .frozenset_view import FrozenSetView
        from .list_view import ListView
        from .set_view import SetView
        from .tuple_view import TupleView

        default_parent_view = default_parent_view or DictView
        views = (DictView, ListView, TupleView, SetView, FrozenSetView, ByteArrayView, *views)

        return super().create(ctx, views, default_parent_view)
