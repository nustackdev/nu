"""ShapesDict collection bases — mapping of homogeneous shapes.

ShapesDictBase         = marker base (no everybase inheritance — shapes are opaque dicts)
MutableShapesDictBase  + Existable + Lengthable + Clearable
ReactiveShapesDictBase + ViewObservable
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
    "MutableShapesDictBase",
    "ReactiveShapesDictBase",
    "ShapesDictBase",
]


# =============================================================================
# SHAPES DICT — three tiers
# =============================================================================


class ShapesDictBase[K, T: ShapeBase]:
    """Base for shapes dicts — mappings of homogeneous shapes.

    Each value is a shape instance of type T, keyed by K. No everybase
    collection inheritance since shapes are opaque dicts, not typed
    primitives.

    Substrates extend with child ref creation for individual shape items.
    """


class MutableShapesDictBase[K, T: ShapeBase](
    ShapesDictBase[K, T],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Mutable shapes dict with collection operations."""


class ReactiveShapesDictBase[K, T: ShapeBase](
    MutableShapesDictBase[K, T],
    ViewObservableBase,
):
    """Shapes dict with collection operations + change observation."""
