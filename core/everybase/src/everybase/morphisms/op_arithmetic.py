"""Arithmetic morphisms.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp

All ops use every.Morphism base classes with Operation mixin (pure).
"""

from __future__ import annotations

from everyabc import INVALID, BinaryOperation, Sentinel, UnaryOperation


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


class NegOp[ResultT](UnaryOperation[ResultT]):
    """Negation: -operand."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return -operand  # type: ignore
        except TypeError:
            return INVALID


class AbsOp[ResultT](UnaryOperation[ResultT]):
    """Absolute value: abs(operand)."""

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return abs(operand)  # type: ignore
        except TypeError:
            return INVALID


class PosOp[ResultT](UnaryOperation[ResultT]):
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


class AddOp[ResultT](BinaryOperation[ResultT]):
    """Addition: left + right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left + right  # type: ignore
        except TypeError:
            return INVALID


class SubOp[ResultT](BinaryOperation[ResultT]):
    """Subtraction: left - right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left - right  # type: ignore
        except TypeError:
            return INVALID


class MulOp[ResultT](BinaryOperation[ResultT]):
    """Multiplication: left * right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left * right  # type: ignore
        except TypeError:
            return INVALID


class DivOp[ResultT](BinaryOperation[ResultT]):
    """Division: left / right. Returns Invalid on division by zero."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left / right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class FloorDivOp[ResultT](BinaryOperation[ResultT]):
    """Floor division: left // right. Returns Invalid on division by zero."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left // right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class ModOp[ResultT](BinaryOperation[ResultT]):
    """Modulo: left % right. Returns Invalid on division by zero."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left % right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class PowOp[ResultT](BinaryOperation[ResultT]):
    """Power: left ** right."""

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        try:
            return left**right  # type: ignore
        except (TypeError, OverflowError):
            return INVALID
