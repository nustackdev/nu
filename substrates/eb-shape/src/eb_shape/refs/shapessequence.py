"""ShapesSequence ref hierarchy — sequence of shapes + Ref navigation.

ShapesSequenceRefBase         = SequenceBase[dict[str, object], ...] + Ref
MutableShapesSequenceRefBase  = MutableSequenceBase[dict[str, object], ...] + Ref
ReactiveShapesSequenceRefBase = ReactiveSequenceBase[dict[str, object], ...] + Ref

Specialized sequence refs where each element is a shape (dict[str, object]).
Child navigation returns ShapeRef variants instead of ItemRef.

Type Parameters:
    T: Shape type (bound to ShapeBase)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from eb_shape.collections import MutableSequenceBase, ReactiveSequenceBase, SequenceBase

from .base import Ref


if TYPE_CHECKING:
    from everybase import IntArg, Sentinel

    from ..shape import Shape as ShapeBase
    from .structured import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "MutableShapesSequenceRefBase",
    "ReactiveShapesSequenceRefBase",
    "ShapesSequenceRefBase",
]


class ShapesSequenceRefBase[T: ShapeBase](
    SequenceBase[dict[str, object], object, object],
    Ref[list[dict[str, object]]],
):
    """Shapes sequence ref — read-only sequence of shapes with navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)


class MutableShapesSequenceRefBase[T: ShapeBase](
    MutableSequenceBase[dict[str, object], object, object],
    ShapesSequenceRefBase[T],
):
    """Mutable shapes sequence ref — mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> MutableShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)


class ReactiveShapesSequenceRefBase[T: ShapeBase](
    ReactiveSequenceBase[dict[str, object], object, object],
    MutableShapesSequenceRefBase[T],
):
    """Reactive shapes sequence ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ReactiveShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)
