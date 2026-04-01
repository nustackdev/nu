"""Arithmetic ops.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp

All ops use every.Op base classes with Calculation mixin (pure).
"""

from __future__ import annotations

from nu.terms import INVALID, BinaryCalc, Sentinel, UnaryCalc


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

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return -operand  # type: ignore
        except TypeError:
            return INVALID


class AbsOp[ResultT](UnaryCalc[ResultT]):
    """Absolute value: abs(operand)."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return abs(operand)  # type: ignore
        except TypeError:
            return INVALID


class PosOp[ResultT](UnaryCalc[ResultT]):
    """Unary plus: +operand."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return +operand  # type: ignore
        except TypeError:
            return INVALID


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class AddOp[ResultT](BinaryCalc[ResultT]):
    """Addition: left + right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left + right  # type: ignore
        except TypeError:
            return INVALID


class SubOp[ResultT](BinaryCalc[ResultT]):
    """Subtraction: left - right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left - right  # type: ignore
        except TypeError:
            return INVALID


class MulOp[ResultT](BinaryCalc[ResultT]):
    """Multiplication: left * right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left * right  # type: ignore
        except TypeError:
            return INVALID


class DivOp[ResultT](BinaryCalc[ResultT]):
    """Division: left / right. Returns Invalid on division by zero."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left / right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class FloorDivOp[ResultT](BinaryCalc[ResultT]):
    """Floor division: left // right. Returns Invalid on division by zero."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left // right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class ModOp[ResultT](BinaryCalc[ResultT]):
    """Modulo: left % right. Returns Invalid on division by zero."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left % right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class PowOp[ResultT](BinaryCalc[ResultT]):
    """Power: left ** right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left**right  # type: ignore
        except TypeError:
            return INVALID
