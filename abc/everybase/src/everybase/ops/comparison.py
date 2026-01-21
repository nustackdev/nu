"""Comparison operations.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp

All ops inherit from BinaryOp and implement `_apply_op()`.
"""

from __future__ import annotations

from every import INVALID, Sentinel
from everybase.bases import BinaryOp


__all__ = [
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
]


class GtOp(BinaryOp[bool | Sentinel]):
    """Greater than: left > right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left > right  # type: ignore
        except TypeError:
            return INVALID


class LtOp(BinaryOp[bool | Sentinel]):
    """Less than: left < right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left < right  # type: ignore
        except TypeError:
            return INVALID


class EqOp(BinaryOp[bool | Sentinel]):
    """Equality: left == right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left == right  # type: ignore
        except TypeError:
            return INVALID


class NeOp(BinaryOp[bool | Sentinel]):
    """Not equal: left != right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left != right  # type: ignore
        except TypeError:
            return INVALID


class GeOp(BinaryOp[bool | Sentinel]):
    """Greater than or equal: left >= right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left >= right  # type: ignore
        except TypeError:
            return INVALID


class LeOp(BinaryOp[bool | Sentinel]):
    """Less than or equal: left <= right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left <= right  # type: ignore
        except TypeError:
            return INVALID


class IdCompOp(BinaryOp[bool | Sentinel]):
    """Identity comparison: left is right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left is right  # type: ignore
        except TypeError:
            return INVALID
