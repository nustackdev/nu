"""Bitwise ops.

Unary: BitwiseNotOp
Binary: BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

Note: Python's & and | operators are blocked in traits for safety.
Use .bitand(), .bitor(), .bitnot() methods instead.
"""

from __future__ import annotations

from nu.terms import BinaryOp, UnaryOp


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


class BitwiseNotOp[ResultT](UnaryOp[ResultT]):
    """Bitwise NOT: ~operand (two's complement).

    Note: Python's ~ operator is blocked in traits.
    Use .bitnot() method instead.
    """

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return ~operand  # type: ignore


# =============================================================================
# BINARY BITWISE
# =============================================================================


class BitwiseAndOp[ResultT](BinaryOp[ResultT]):
    """Bitwise AND: left & right.

    Note: Distinct from AndOp (logical AND).
    Use .bitand() method to create this operation.
    """

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left & right  # type: ignore


class BitwiseOrOp[ResultT](BinaryOp[ResultT]):
    """Bitwise OR: left | right.

    Note: Distinct from OrOp (logical OR).
    Use .bitor() method to create this operation.
    """

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left | right  # type: ignore


class XorOp[ResultT](BinaryOp[ResultT]):
    """Bitwise XOR: left ^ right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left ^ right  # type: ignore


class LShiftOp[ResultT](BinaryOp[ResultT]):
    """Left shift: left << right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left << right  # type: ignore


class RShiftOp[ResultT](BinaryOp[ResultT]):
    """Right shift: left >> right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left >> right  # type: ignore
