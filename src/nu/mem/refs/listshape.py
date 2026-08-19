"""Dict shapes list reference: sequence of homogeneous shapes.

Index descent (``ref[i]``) is the blueprint's ``__getitem__``: it returns a
``ShapeRef`` at the index with this ref as ``parent_ref``. The element shape type
is passed to the blueprint as ``item_shape_type``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import MutableShapesSequenceRef, Slot

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, StrArg


__all__ = [
    "ShapesListRef",
]


T = TypeVar("T", bound="Shape")


S = TypeVar("S", bound="Shape")


class ShapesListRef(MutableShapesSequenceRef[T], RefBase[list[dict]], Generic[T]):
    """Dict shapes list reference: sequence of homogeneous shapes."""

    def _wrap_item_ref(self, address: object) -> ShapeRef:
        """Navigate to the shape at ``address`` as a substrate-backed mem ShapeRef."""
        return ShapeRef(
            address,
            shape_type=self._payload["item_shape_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def __init__(
        self,
        address: StrArg | IntArg,
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
        self._payload["item_type"] = dict

    @classmethod
    def slot(cls, shape_type: type[S]) -> ShapesListRef[S]:
        """Declare a slot holding a sequence of ``shape_type`` shapes."""
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``ShapesListRef[S]``."""
        (shape_type,) = args
        return {"shape_type": shape_type}
