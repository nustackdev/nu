"""Comparison morphisms.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp

All ops use every.BinaryMorphism with Operation mixin (pure).
"""

from __future__ import annotations

from everyabc import INVALID, BinaryMorphism, Operation, Sentinel


__all__ = [
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
]


class GtOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Greater than: left > right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left > right  # type: ignore
        except TypeError:
            return INVALID


class LtOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Less than: left < right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left < right  # type: ignore
        except TypeError:
            return INVALID


class EqOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Equality: left == right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left == right  # type: ignore
        except TypeError:
            return INVALID


class NeOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Not equal: left != right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left != right  # type: ignore
        except TypeError:
            return INVALID


class GeOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Greater than or equal: left >= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left >= right  # type: ignore
        except TypeError:
            return INVALID


class LeOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Less than or equal: left <= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        try:
            return left <= right  # type: ignore
        except TypeError:
            return INVALID


class IdCompOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Identity comparison: left is right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        return left is right
