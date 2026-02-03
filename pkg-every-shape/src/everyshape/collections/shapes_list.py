"""ShapesList collection bases — sequence of homogeneous shapes.

ShapesListBase         = marker base (no everybase inheritance — shapes are opaque dicts)
MutableShapesListBase  + Existable + Lengthable + Clearable
ReactiveShapesListBase + ViewObservable
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionLengthableBase,
    ViewObservableBase,
)


if TYPE_CHECKING:
    from ..shape import Shape as ShapeBase


__all__ = [
    "MutableShapesListBase",
    "ReactiveShapesListBase",
    "ShapesListBase",
]


# =============================================================================
# SHAPES LIST — three tiers
# =============================================================================


class ShapesListBase[T: ShapeBase]:
    """Base for shapes lists — sequences of homogeneous shapes.

    Each element is a shape instance of type T. No everybase collection
    inheritance since shapes are opaque dicts, not typed primitives.

    Substrates extend with child ref creation for individual shape items.
    """


class MutableShapesListBase[T: ShapeBase](
    ShapesListBase[T],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Mutable shapes list with collection operations."""


class ReactiveShapesListBase[T: ShapeBase](
    MutableShapesListBase[T],
    ViewObservableBase,
):
    """Shapes list with collection operations + change observation."""
