"""Virtuals shapes list reference — sequence of homogeneous shapes.

Index descent (``ref[i]``) is overridden to return a substrate-backed virtuals
``ShapeRef`` at the index, with this ref as ``parent_ref``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Any, Iterator, List
from nu.domains.shape import ReactiveShapesSequenceRef, Slot

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.collections import MutableSequenceBase


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](ReactiveShapesSequenceRef[T], ViewRef[list[dict]]):
    """Virtuals shapes list reference — sequence of homogeneous shapes."""

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
        address: str | int | Nu,
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
    def slot[S: Shape](
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
