"""ShapesSequence ref hierarchy — sequence of shapes + Ref navigation.

ShapesSequenceRefBase         = SequenceI[dict[str, object], ...] + Ref
MutableShapesSequenceRefBase  = MutableSequenceI[dict[str, object], ...] + Ref
ReactiveShapesSequenceRefBase = ReactiveSequenceI[dict[str, object], ...] + Ref

Specialized sequence refs where each element is a shape (dict[str, object]).
Child navigation returns ShapeRef variants instead of ItemRef.

Type Parameters:
    T: Shape type (bound to ShapeBase)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from nu.shapes.collections import MutableSequenceI, ReactiveSequenceI, SequenceI
from .base import Ref


if TYPE_CHECKING:
    from nu import IntArg, Sentinel

    from nu.shapes.shape import Shape as ShapeBase
    from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "MutableShapesSequenceRefBase",
    "ReactiveShapesSequenceRefBase",
    "ShapesSequenceRefBase",
]


class ShapesSequenceRefBase[T: ShapeBase](
    SequenceI[dict[str, object], object, object],
    Ref[list[dict[str, object]]],
):
    """Shapes sequence ref — read-only sequence of shapes with navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at index.

        Return type is T (the Shape class) for Pyright slot navigation.
        Runtime returns ShapeRef[T].
        """
        return self._create_item_ref(index)  # type: ignore[return-value]


class MutableShapesSequenceRefBase[T: ShapeBase](
    MutableSequenceI[dict[str, object], object, object],
    ShapesSequenceRefBase[T],
):
    """Mutable shapes sequence ref — mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)  # type: ignore[return-value]


class ReactiveShapesSequenceRefBase[T: ShapeBase](
    ReactiveSequenceI[dict[str, object], object, object],
    MutableShapesSequenceRefBase[T],
):
    """Reactive shapes sequence ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_item_ref(self, index: IntArg | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given index."""
        ...

    def __getitem__(self, index: IntArg) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at index."""
        return self._create_item_ref(index)  # type: ignore[return-value]
