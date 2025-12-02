"""Shape."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.shape import RValue
from everyshape.shape import Shape as ShapeBase


if TYPE_CHECKING:
    from .commands import StoreCmd
    from .operations import ExtractOp


__all__ = [
    "Shape",
]


class Shape(ShapeBase):
    """Dict based shape implementation."""

    def extract(self) -> ExtractOp[dict]:
        """Extract value."""
        ...

    def store[T: dict](self, data: T | RValue[T]) -> StoreCmd[T]:
        """Store data."""
        ...
