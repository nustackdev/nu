"""ShapesList collection RefBases — sequence of homogeneous shapes.

ShapesListRefBase         = Ref (no everybase inheritance — shapes are opaque dicts)
MutableShapesListRefBase  + Existable + Lengthable + Clearable
ReactiveShapesListRefBase + ViewObservable
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionLengthableBase,
    ViewObservableBase,
)

from ..ref import Ref


if TYPE_CHECKING:
    from ..shape import Shape as ShapeBase


__all__ = [
    "MutableShapesListRefBase",
    "ReactiveShapesListRefBase",
    "ShapesListRefBase",
]


# =============================================================================
# SHAPES LIST REF — three tiers
# =============================================================================


class ShapesListRefBase[T: ShapeBase](Ref[list[dict[str, object]]]):
    """Base for shapes list refs — sequences of homogeneous shapes.

    Each element is a shape instance of type T. No everybase collection
    inheritance since shapes are opaque dicts, not typed primitives.

    Substrates extend with child ref creation for individual shape items.
    """


class MutableShapesListRefBase[T: ShapeBase](
    ShapesListRefBase[T],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Mutable shapes list with collection operations."""


class ReactiveShapesListRefBase[T: ShapeBase](
    MutableShapesListRefBase[T],
    ViewObservableBase,
):
    """Shapes list with collection operations + change observation."""
