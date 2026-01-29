"""Bitwise morphisms.

Unary: BitwiseNotOp
Binary: BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

Note: Python's & and | operators are blocked in traits for safety.
Use .bitand(), .bitor(), .bitnot() methods instead.
"""

from __future__ import annotations

from everyabc import INVALID, BinaryMorphism, Operation, Sentinel, UnaryMorphism


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


class BitwiseNotOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
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


class BitwiseAndOp[ResultT](Operation, BinaryMorphism[ResultT]):
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


class BitwiseOrOp[ResultT](Operation, BinaryMorphism[ResultT]):
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


class XorOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Bitwise XOR: left ^ right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left ^ right  # type: ignore
        except TypeError:
            return INVALID


class LShiftOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Left shift: left << right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left << right  # type: ignore
        except TypeError:
            return INVALID


class RShiftOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Right shift: left >> right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left >> right  # type: ignore
        except TypeError:
            return INVALID
