"""Comparison ops.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp

All ops use every.BinaryOp with Calculation mixin (pure).
"""

from __future__ import annotations

from nu.terms import INVALID, BinaryCalc, Sentinel


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

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left > right  # type: ignore
        except TypeError:
            return INVALID


class LtOp(BinaryCalc[bool]):
    """Less than: left < right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left < right  # type: ignore
        except TypeError:
            return INVALID


class EqOp(BinaryCalc[bool]):
    """Equality: left == right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left == right  # type: ignore
        except TypeError:
            return INVALID


class NeOp(BinaryCalc[bool]):
    """Not equal: left != right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left != right  # type: ignore
        except TypeError:
            return INVALID


class GeOp(BinaryCalc[bool]):
    """Greater than or equal: left >= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left >= right  # type: ignore
        except TypeError:
            return INVALID


class LeOp(BinaryCalc[bool]):
    """Less than or equal: left <= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left <= right  # type: ignore
        except TypeError:
            return INVALID


class IdCompOp(BinaryCalc[bool]):
    """Identity comparison: left is right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        return left is right
