"""ShapesList ref hierarchy — shapes list bases + Ref navigation.

ShapesListRefBase         = ShapesListBase + Ref
MutableShapesListRefBase  = MutableShapesListBase + ShapesListRefBase
ReactiveShapesListRefBase = ReactiveShapesListBase + MutableShapesListRefBase
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..collections import MutableShapesListBase, ReactiveShapesListBase, ShapesListBase
from .base import Ref


if TYPE_CHECKING:
    from ..shape import Shape as ShapeBase


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


class MutableShapesListRefBase[T: ShapeBase](
    MutableShapesListBase[T],
    ShapesListRefBase[T],
):
    """Mutable shapes list ref — collection ops + navigation."""


class ReactiveShapesListRefBase[T: ShapeBase](
    ReactiveShapesListBase[T],
    MutableShapesListRefBase[T],
):
    """Reactive shapes list ref — observation + collection ops + navigation."""
