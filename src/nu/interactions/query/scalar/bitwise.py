"""Bitwise ops.

Unary: BitwiseNot
Binary: BitwiseAnd, BitwiseOr, Xor, LShift, RShift

Note: Python's & and | operators are blocked in traits for safety.
Use .bitand(), .bitor(), .bitnot() methods instead.
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryScalar, Mode, UnaryScalar


__all__ = [
    "BitwiseAnd",
    "BitwiseNot",
    "BitwiseOr",
    "LShift",
    "RShift",
    "Xor",
]


# =============================================================================
# UNARY BITWISE
# =============================================================================


class BitwiseNot[ResultT](UnaryScalar[ResultT]):
    """Bitwise NOT: ~operand (two's complement).

    Note: Python's ~ operator is blocked in traits.
    Use .bitnot() method instead.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return ~operand  # type: ignore


# =============================================================================
# BINARY BITWISE
# =============================================================================


class BitwiseAnd[ResultT](BinaryScalar[ResultT]):
    """Bitwise AND: left & right.

    Note: Distinct from And (logical AND).
    Use .bitand() method to create this operation.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left & right  # type: ignore


class BitwiseOr[ResultT](BinaryScalar[ResultT]):
    """Bitwise OR: left | right.

    Note: Distinct from Or (logical OR).
    Use .bitor() method to create this operation.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left | right  # type: ignore


class Xor[ResultT](BinaryScalar[ResultT]):
    """Bitwise XOR: left ^ right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left ^ right  # type: ignore


class LShift[ResultT](BinaryScalar[ResultT]):
    """Left shift: left << right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left << right  # type: ignore


class RShift[ResultT](BinaryScalar[ResultT]):
    """Right shift: left >> right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left >> right  # type: ignore
