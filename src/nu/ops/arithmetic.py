"""Arithmetic ops.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp

All ops use every.Op base classes with Calculation mixin (pure).
"""

from __future__ import annotations

from nu.terms import BinaryCalc, UnaryCalc


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


class NegOp[ResultT](UnaryCalc[ResultT]):
    """Negation: -operand."""

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return -operand  # type: ignore


class AbsOp[ResultT](UnaryCalc[ResultT]):
    """Absolute value: abs(operand)."""

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return abs(operand)  # type: ignore


class PosOp[ResultT](UnaryCalc[ResultT]):
    """Unary plus: +operand."""

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return +operand  # type: ignore


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class AddOp[ResultT](BinaryCalc[ResultT]):
    """Addition: left + right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left + right  # type: ignore


class SubOp[ResultT](BinaryCalc[ResultT]):
    """Subtraction: left - right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left - right  # type: ignore


class MulOp[ResultT](BinaryCalc[ResultT]):
    """Multiplication: left * right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left * right  # type: ignore


class DivOp[ResultT](BinaryCalc[ResultT]):
    """Division: left / right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left / right  # type: ignore


class FloorDivOp[ResultT](BinaryCalc[ResultT]):
    """Floor division: left // right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left // right  # type: ignore


class ModOp[ResultT](BinaryCalc[ResultT]):
    """Modulo: left % right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left % right  # type: ignore


class PowOp[ResultT](BinaryCalc[ResultT]):
    """Power: left ** right."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left**right  # type: ignore
