"""ShapesList ref hierarchy — list type + Ref navigation.

ShapesListRefBase         = ListBase + Ref          (list IS mutable)
ReactiveShapesListRefBase = ReactiveListBase + Ref  (+ observation)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everyshape.types import ListBase, ReactiveListBase

from .base import Ref


if TYPE_CHECKING:
    from everybase import IntArg, Sentinel

    from ..shape import Shape as ShapeBase
    from .structured import MutableShapeRef, ReactiveShapeRef


__all__ = [
    "ReactiveShapesListRefBase",
    "ShapesListRefBase",
]


class ShapesListRefBase[T: ShapeBase](
    ListBase[dict[str, object]],
    Ref[list[dict[str, object]]],
):
    """Shapes list ref — mutable list of shapes with navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> MutableShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)


class ReactiveShapesListRefBase[T: ShapeBase](
    ReactiveListBase[dict[str, object]],
    ShapesListRefBase[T],
):
    """Reactive shapes list ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> ReactiveShapeRef[T]:
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)
