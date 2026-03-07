# ruff: noqa: D102
"""Dict shapes list reference — sequence of homogeneous shapes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from everybase.abc import ensure_term
from everybase.shape import MutableShapesSequenceRefBase, Slot

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from everybase import Sentinel, Term
    from everybase.shape import Shape


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](
    MutableShapesSequenceRefBase[T],
    RefBase[list[dict]],
):
    """Dict shapes list reference — sequence of homogeneous shapes."""

    def __init__(
        self,
        *,
        shape_type: type[T],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ShapeRef[T]:
        return ShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot(cls, shape_type: type[T]) -> Self:
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
