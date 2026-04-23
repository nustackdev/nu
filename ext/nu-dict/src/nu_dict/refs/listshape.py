# ruff: noqa: D102
"""Dict shapes list reference — sequence of homogeneous shapes."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import ensure_nu
from nu.shapes import MutableShapesSequenceRef, Slot
from nu.terms import Mode

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Nu, Sentinel, Shape


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](
    MutableShapesSequenceRef[T],
    RefBase[list[dict]],
):
    """Dict shapes list reference — sequence of homogeneous shapes."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        shape_type: type[T],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Nu[int | Sentinel]) -> ShapeRef[T]:
        return ShapeRef(
            address=ensure_nu(index),
            shape_type=self._shape_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[S: Shape](cls, shape_type: type[S]) -> ShapesListRef[S]:
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
