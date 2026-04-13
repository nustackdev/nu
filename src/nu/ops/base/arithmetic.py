"""Arithmetic ops.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp
"""

from __future__ import annotations

from nu.terms import BinaryOp, UnaryOp


__all__ = [
    "AbsOp",
    "AddOp",
    "DivOp",
    "FloorDivOp",
    "ModOp",
    "MulOp",
    "NegOp",
    "PosOp",
    "PowOp",
    "SubOp",
]


# =============================================================================
# UNARY ARITHMETIC
# =============================================================================


class NegOp[ResultT](UnaryOp[ResultT]):
    """Negation: -operand."""

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return -operand  # type: ignore


class AbsOp[ResultT](UnaryOp[ResultT]):
    """Absolute value: abs(operand)."""

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return abs(operand)  # type: ignore


class PosOp[ResultT](UnaryOp[ResultT]):
    """Unary plus: +operand."""

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return +operand  # type: ignore


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class AddOp[ResultT](BinaryOp[ResultT]):
    """Addition: left + right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left + right  # type: ignore


class SubOp[ResultT](BinaryOp[ResultT]):
    """Subtraction: left - right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left - right  # type: ignore


class MulOp[ResultT](BinaryOp[ResultT]):
    """Multiplication: left * right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left * right  # type: ignore


class DivOp[ResultT](BinaryOp[ResultT]):
    """Division: left / right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left / right  # type: ignore


class FloorDivOp[ResultT](BinaryOp[ResultT]):
    """Floor division: left // right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left // right  # type: ignore


class ModOp[ResultT](BinaryOp[ResultT]):
    """Modulo: left % right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left % right  # type: ignore


class PowOp[ResultT](BinaryOp[ResultT]):
    """Power: left ** right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left**right  # type: ignore
