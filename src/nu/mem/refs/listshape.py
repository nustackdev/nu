"""Dict shapes list reference — sequence of homogeneous shapes.

Index descent (``ref[i]``) is the blueprint's ``__getitem__``: it returns a
``ShapeRef`` at the index with this ref as ``parent_ref``. The element shape type
is passed to the blueprint as ``item_shape_type``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.shape import MutableShapesSequenceRef, Slot

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](MutableShapesSequenceRef, RefBase[list[dict]]):
    """Dict shapes list reference — sequence of homogeneous shapes."""

    def __getitem__(self, index: object) -> ShapeRef:
        """Navigate to the shape at ``index`` as a substrate-backed mem ShapeRef."""
        return ShapeRef(
            index,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def __init__(
        self,
        address: str | int | Nu,
        *,
        shape_type: type[T],
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            item_shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self.payload["item_type"] = dict

    @classmethod
    def slot[S: Shape](cls, shape_type: type[S]) -> ShapesListRef[S]:
        """Declare a slot holding a sequence of ``shape_type`` shapes."""
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
