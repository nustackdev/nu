"""Arithmetic operations.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp

All ops inherit from arity bases and implement `_apply_op()`.
"""

from __future__ import annotations

from every import INVALID, Sentinel
from everybase.bases import BinaryOp, UnaryOp


__all__ = [  # noqa: RUF022
    # Unary
    "AbsOp",
    "NegOp",
    "PosOp",
    # Binary
    "AddOp",
    "DivOp",
    "FloorDivOp",
    "ModOp",
    "MulOp",
    "PowOp",
    "SubOp",
]


# =============================================================================
# UNARY ARITHMETIC
# =============================================================================


class NegOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Negation: -operand."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        try:
            return -operand  # type: ignore
        except TypeError:
            return INVALID


class AbsOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Absolute value: abs(operand)."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        try:
            return abs(operand)  # type: ignore
        except TypeError:
            return INVALID


class PosOp[ResultT](UnaryOp[ResultT | Sentinel]):
    """Unary plus: +operand."""

    def _apply_op(self, operand: object) -> ResultT | Sentinel:
        try:
            return +operand  # type: ignore
        except TypeError:
            return INVALID


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class AddOp[ResultT](BinaryOp[ResultT]):
    """Addition: left + right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left + right  # type: ignore
        except TypeError:
            return INVALID


class SubOp[ResultT](BinaryOp[ResultT]):
    """Subtraction: left - right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left - right  # type: ignore
        except TypeError:
            return INVALID


class MulOp[ResultT](BinaryOp[ResultT]):
    """Multiplication: left * right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left * right  # type: ignore
        except TypeError:
            return INVALID


class DivOp[ResultT](BinaryOp[ResultT]):
    """Division: left / right. Returns Invalid on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left / right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class FloorDivOp[ResultT](BinaryOp[ResultT]):
    """Floor division: left // right. Returns Invalid on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left // right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class ModOp[ResultT](BinaryOp[ResultT]):
    """Modulo: left % right. Returns Invalid on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left % right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class PowOp[ResultT](BinaryOp[ResultT]):
    """Power: left ** right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left**right  # type: ignore
        except (TypeError, OverflowError):
            return INVALID
