"""Dict shapes list reference — sequence of homogeneous shapes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import ensure_term
from everyshape import MutableShapesListRefBase, Slot

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from typing import Self

    from everyabc import Sentinel, Term
    from everyshape import Shape


__all__ = [
    "ShapesListRef",
]


class ShapesListRef[T: Shape](
    MutableShapesListRefBase[T],
    RefBase[list[dict]],
):
    """Dict shapes list reference — sequence of homogeneous shapes."""

    def __init__(
        self,
        address: str | int | Term,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shapes list reference."""
        super().__init__(address, parent, shape)
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given index."""
        return ShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            parent=self,
            shape=self._shape,
        )

    @classmethod
    def slot(cls, shape_type: type[T]) -> Self:
        """Create a slot for this shapes list ref type.

        Args:
            shape_type: Shape class for items.

        Returns:
            Slot that creates ShapesListRef instances.
        """
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
