"""Comparison morphisms.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp

All ops use every.BinaryMorphism with Operation mixin (pure).
"""

from __future__ import annotations

from everybase.core import INVALID, BinaryOperation, Sentinel


__all__ = [
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
]


class GtOp(BinaryOperation[bool]):
    """Greater than: left > right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left > right  # type: ignore
        except TypeError:
            return INVALID


class LtOp(BinaryOperation[bool]):
    """Less than: left < right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left < right  # type: ignore
        except TypeError:
            return INVALID


class EqOp(BinaryOperation[bool]):
    """Equality: left == right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left == right  # type: ignore
        except TypeError:
            return INVALID


class NeOp(BinaryOperation[bool]):
    """Not equal: left != right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left != right  # type: ignore
        except TypeError:
            return INVALID


class GeOp(BinaryOperation[bool]):
    """Greater than or equal: left >= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left >= right  # type: ignore
        except TypeError:
            return INVALID


class LeOp(BinaryOperation[bool]):
    """Less than or equal: left <= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left <= right  # type: ignore
        except TypeError:
            return INVALID


class IdCompOp(BinaryOperation[bool]):
    """Identity comparison: left is right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        return left is right
