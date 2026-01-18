"""Bitwise operations.

Unary: BitwiseNotOp
Binary: BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

Note: Python's & and | operators are blocked in type bases for safety.
Use .bitand(), .bitor(), .bitnot() methods instead.
"""

from __future__ import annotations

from everyshape.term import BinaryOp, UnaryOp
from everyshape.typing import INVALID, Sentinel


__all__ = [
    "BitwiseAndOp",
    "BitwiseNotOp",
    "BitwiseOrOp",
    "LShiftOp",
    "RShiftOp",
    "XorOp",
]


# =============================================================================
# UNARY BITWISE
# =============================================================================


class BitwiseNotOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Bitwise NOT: ~operand (two's complement).

    Note: Python's ~ operator is blocked in type bases.
    Use .bitnot() method instead.
    """

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        try:
            return ~operand  # type: ignore
        except TypeError:
            return INVALID


# =============================================================================
# BINARY BITWISE
# =============================================================================


class BitwiseAndOp[ResultT](BinaryOp[ResultT]):
    """Bitwise AND: left & right.

    Note: Distinct from AndOp (logical AND).
    Use .bitand() method to create this operation.
    """

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left & right  # type: ignore
        except TypeError:
            return INVALID


class BitwiseOrOp[ResultT](BinaryOp[ResultT]):
    """Bitwise OR: left | right.

    Note: Distinct from OrOp (logical OR).
    Use .bitor() method to create this operation.
    """

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left | right  # type: ignore
        except TypeError:
            return INVALID


class XorOp[ResultT](BinaryOp[ResultT]):
    """Bitwise XOR: left ^ right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left ^ right  # type: ignore
        except TypeError:
            return INVALID


class LShiftOp[ResultT](BinaryOp[ResultT]):
    """Left shift: left << right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left << right  # type: ignore
        except TypeError:
            return INVALID


class RShiftOp[ResultT](BinaryOp[ResultT]):
    """Right shift: left >> right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left >> right  # type: ignore
        except TypeError:
            return INVALID
