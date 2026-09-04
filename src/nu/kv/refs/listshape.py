"""Virtuals shapes list reference: sequence of homogeneous shapes.

Index descent (``ref[i]``) is overridden to return a substrate-backed virtuals
``ShapeRef`` at the index, with this ref as ``parent_ref``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import ReactiveShapesSequenceRef, Slot
from nu.forms import Any, Iterator, List

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, Nu, StrArg
    from virtuals.collections import MutableSequenceBase


__all__ = [
    "ShapesListRef",
]


T = TypeVar("T", bound="Shape")


S = TypeVar("S", bound="Shape")


class ShapesListRef(ReactiveShapesSequenceRef[T], ViewRef[list[dict]], Generic[T]):
    """An ordered list of one shape type in KV storage, indexed into by position.

    Indexing lands on a shape ref at that position rather than on a value, so
    a row's fields are reachable and writable one at a time:
    ``rows[0].symbol.set(...)``.

    Notes:
        - Every row is stored decomposed, field by field, so writing one
          field of one row does not read or rewrite the others.
        - A position does not vivify: writing a field at an index the list
          does not reach raises IndexError. Grow the list first, by
          appending the row or setting the whole list.
        - Reading a field at an out-of-range index is not an error; it
          yields EMPTY.
        - The index may be an expression or a ref, so the position can be
          computed at run time.
        - ListRef is the sibling for lists of plain values.

    Example:
        class Order(Shape):
            symbol = StrRef.slot()
        class Portfolio(Shape):
            orders = ShapesListRef.slot(Order)
        run(Portfolio.orders.append({"symbol": "SOL"}), ctx)
        run(Portfolio.orders[0].symbol, ctx)
    """

    def _wrap_item_ref(self, address: object) -> ShapeRef:
        """Navigate to the shape at ``address`` as a substrate-backed virtuals ShapeRef."""
        from virtuals.views import DictView

        return ShapeRef(
            address,
            shape_type=self._payload["item_shape_type"],
            view_type=DictView,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> List:
        """Wrap a sequence-level op result as a List."""
        return List(op)

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        return Iterator(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> List:
        return List(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        shape_type: type[T],
        view_type: type[MutableSequenceBase] | None = None,
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        if view_type is None:
            from virtuals.views import ListView

            view_type = ListView
        super().__init__(
            address,
            item_shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self._payload["segment"] = address
        self._payload["type_marker"] = view_type
        self._payload["item_type"] = dict

    @classmethod
    def slot(
        cls, shape_type: type[S], view_type: type[MutableSequenceBase] | None = None
    ) -> ShapesListRef[S]:
        """Declare a slot holding a sequence of ``shape_type`` shapes."""
        from virtuals.views import ListView

        return Slot(cls, shape_type=shape_type, view_type=view_type or ListView)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``ShapesListRef[S]``."""
        from virtuals.views import ListView

        (shape_type,) = args
        return {"shape_type": shape_type, "view_type": ListView}
