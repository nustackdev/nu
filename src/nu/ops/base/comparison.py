"""Comparison ops.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp
"""

from __future__ import annotations

from nu.terms import BinaryOp


__all__ = [
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
]


class GtOp(BinaryOp[bool]):
    """Greater than: left > right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left > right  # type: ignore


class LtOp(BinaryOp[bool]):
    """Less than: left < right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left < right  # type: ignore


class EqOp(BinaryOp[bool]):
    """Equality: left == right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left == right  # type: ignore


class NeOp(BinaryOp[bool]):
    """Not equal: left != right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left != right  # type: ignore


class GeOp(BinaryOp[bool]):
    """Greater than or equal: left >= right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left >= right  # type: ignore


class LeOp(BinaryOp[bool]):
    """Less than or equal: left <= right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left <= right  # type: ignore


class IdCompOp(BinaryOp[bool]):
    """Identity comparison: left is right."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return left is right
