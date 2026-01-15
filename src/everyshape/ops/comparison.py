"""Comparison operations.

Binary: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp

All ops inherit from BinaryOp and implement `_apply_op()`.
"""

from __future__ import annotations

from everyshape.term import BinaryOp
from everyshape.typing import NAN, Sentinel


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
            return NAN


class LtOp(BinaryOp[bool | Sentinel]):
    """Less than: left < right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left < right  # type: ignore
        except TypeError:
            return NAN


class EqOp(BinaryOp[bool | Sentinel]):
    """Equality: left == right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left == right  # type: ignore
        except TypeError:
            return NAN


class NeOp(BinaryOp[bool | Sentinel]):
    """Not equal: left != right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left != right  # type: ignore
        except TypeError:
            return NAN


class GeOp(BinaryOp[bool | Sentinel]):
    """Greater than or equal: left >= right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left >= right  # type: ignore
        except TypeError:
            return NAN


class LeOp(BinaryOp[bool | Sentinel]):
    """Less than or equal: left <= right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left <= right  # type: ignore
        except TypeError:
            return NAN


class IdCompOp(BinaryOp[bool | Sentinel]):
    """Identity comparison: left is right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left is right  # type: ignore
        except TypeError:
            return NAN
