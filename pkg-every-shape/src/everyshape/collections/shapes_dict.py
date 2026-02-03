"""ShapesDict collection RefBases — mapping of homogeneous shapes.

ShapesDictRefBase         = Ref (no everybase inheritance — shapes are opaque dicts)
MutableShapesDictRefBase  + Existable + Lengthable + Clearable
ReactiveShapesDictRefBase + ViewObservable
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
    "MutableShapesDictRefBase",
    "ReactiveShapesDictRefBase",
    "ShapesDictRefBase",
]


# =============================================================================
# SHAPES DICT REF — three tiers
# =============================================================================


class ShapesDictRefBase[K, T: ShapeBase](Ref[dict[K, dict[str, object]]]):
    """Base for shapes dict refs — mappings of homogeneous shapes.

    Each value is a shape instance of type T, keyed by K. No everybase
    collection inheritance since shapes are opaque dicts, not typed
    primitives.

    Substrates extend with child ref creation for individual shape items.
    """


class MutableShapesDictRefBase[K, T: ShapeBase](
    ShapesDictRefBase[K, T],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Mutable shapes dict with collection operations."""


class ReactiveShapesDictRefBase[K, T: ShapeBase](
    MutableShapesDictRefBase[K, T],
    ViewObservableBase,
):
    """Shapes dict with collection operations + change observation."""
