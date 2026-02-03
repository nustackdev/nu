"""ShapesDict ref hierarchy — shapes dict bases + Ref navigation.

ShapesDictRefBase         = ShapesDictBase + Ref
MutableShapesDictRefBase  = MutableShapesDictBase + ShapesDictRefBase
ReactiveShapesDictRefBase = ReactiveShapesDictBase + MutableShapesDictRefBase
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..collections import MutableShapesDictBase, ReactiveShapesDictBase, ShapesDictBase
from .base import Ref


if TYPE_CHECKING:
    from ..shape import Shape as ShapeBase


__all__ = [
    "MutableShapesDictRefBase",
    "ReactiveShapesDictRefBase",
    "ShapesDictRefBase",
]


class ShapesDictRefBase[K, T: ShapeBase](
    ShapesDictBase[K, T],
    Ref[dict[K, dict[str, object]]],
):
    """Shapes dict ref — mapping of shapes with navigation."""


class MutableShapesDictRefBase[K, T: ShapeBase](
    MutableShapesDictBase[K, T],
    ShapesDictRefBase[K, T],
):
    """Mutable shapes dict ref — collection ops + navigation."""


class ReactiveShapesDictRefBase[K, T: ShapeBase](
    ReactiveShapesDictBase[K, T],
    MutableShapesDictRefBase[K, T],
):
    """Reactive shapes dict ref — observation + collection ops + navigation."""
