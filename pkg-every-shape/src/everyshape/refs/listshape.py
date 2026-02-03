"""ShapesList ref hierarchy — shapes list bases + Ref navigation.

ShapesListRefBase         = ShapesListBase + Ref
MutableShapesListRefBase  = MutableShapesListBase + ShapesListRefBase
ReactiveShapesListRefBase = ReactiveShapesListBase + MutableShapesListRefBase
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from ..collections import MutableShapesListBase, ReactiveShapesListBase, ShapesListBase
from .base import Ref


if TYPE_CHECKING:
    from everyabc import Sentinel, Term

    from ..shape import Shape as ShapeBase
    from .structured import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "MutableShapesListRefBase",
    "ReactiveShapesListRefBase",
    "ShapesListRefBase",
]


class ShapesListRefBase[T: ShapeBase](
    ShapesListBase[T],
    Ref[list[dict[str, object]]],
):
    """Shapes list ref — sequence of shapes with navigation."""

    @abstractmethod
    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: int | Term[int]) -> ShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)


class MutableShapesListRefBase[T: ShapeBase](
    MutableShapesListBase[T],
    ShapesListRefBase[T],
):
    """Mutable shapes list ref — collection ops + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: int | Term[int]) -> MutableShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)


class ReactiveShapesListRefBase[T: ShapeBase](
    ReactiveShapesListBase[T],
    MutableShapesListRefBase[T],
):
    """Reactive shapes list ref — observation + collection ops + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: int | Term[int]) -> ReactiveShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)
