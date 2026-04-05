"""Comparison ops.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp

All ops use every.BinaryOp with Calculation mixin (pure).
"""

from __future__ import annotations

from nu.terms import BinaryCalc


__all__ = [
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
]


class GtOp(BinaryCalc[bool]):
    """Greater than: left > right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left > right  # type: ignore


class LtOp(BinaryCalc[bool]):
    """Less than: left < right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left < right  # type: ignore


class EqOp(BinaryCalc[bool]):
    """Equality: left == right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left == right  # type: ignore


class NeOp(BinaryCalc[bool]):
    """Not equal: left != right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left != right  # type: ignore


class GeOp(BinaryCalc[bool]):
    """Greater than or equal: left >= right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left >= right  # type: ignore


class LeOp(BinaryCalc[bool]):
    """Less than or equal: left <= right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left <= right  # type: ignore


class IdCompOp(BinaryCalc[bool]):
    """Identity comparison: left is right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left is right
