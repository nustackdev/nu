"""Bitwise morphisms.

Unary: BitwiseNotOp
Binary: BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

Note: Python's & and | operators are blocked in traits for safety.
Use .bitand(), .bitor(), .bitnot() methods instead.
"""

from __future__ import annotations

from everyabc import INVALID, BinaryOperation, Sentinel, UnaryOperation


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


class BitwiseNotOp[ResultT](UnaryOperation[ResultT]):
    """Bitwise NOT: ~operand (two's complement).

    Note: Python's ~ operator is blocked in traits.
    Use .bitnot() method instead.
    """

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return ~operand  # type: ignore
        except TypeError:
            return INVALID


# =============================================================================
# BINARY BITWISE
# =============================================================================


class BitwiseAndOp[ResultT](BinaryOperation[ResultT]):
    """Bitwise AND: left & right.

    Note: Distinct from AndOp (logical AND).
    Use .bitand() method to create this operation.
    """

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left & right  # type: ignore
        except TypeError:
            return INVALID


class BitwiseOrOp[ResultT](BinaryOperation[ResultT]):
    """Bitwise OR: left | right.

    Note: Distinct from OrOp (logical OR).
    Use .bitor() method to create this operation.
    """

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left | right  # type: ignore
        except TypeError:
            return INVALID


class XorOp[ResultT](BinaryOperation[ResultT]):
    """Bitwise XOR: left ^ right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left ^ right  # type: ignore
        except TypeError:
            return INVALID


class LShiftOp[ResultT](BinaryOperation[ResultT]):
    """Left shift: left << right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left << right  # type: ignore
        except TypeError:
            return INVALID


class RShiftOp[ResultT](BinaryOperation[ResultT]):
    """Right shift: left >> right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left >> right  # type: ignore
        except TypeError:
            return INVALID
