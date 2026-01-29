"""Arithmetic morphisms.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp

All ops use every.Morphism base classes with Operation mixin (pure).
"""

from __future__ import annotations

from everyabc import INVALID, BinaryMorphism, Operation, Sentinel, UnaryMorphism


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


class NegOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Negation: -operand."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        try:
            return -operand  # type: ignore
        except TypeError:
            return INVALID


class AbsOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Absolute value: abs(operand)."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        try:
            return abs(operand)  # type: ignore
        except TypeError:
            return INVALID


class PosOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Unary plus: +operand."""

    def _apply(self, operand: object) -> ResultT | Sentinel:
        try:
            return +operand  # type: ignore
        except TypeError:
            return INVALID


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class AddOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Addition: left + right."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left + right  # type: ignore
        except TypeError:
            return INVALID


class SubOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Subtraction: left - right."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left - right  # type: ignore
        except TypeError:
            return INVALID


class MulOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Multiplication: left * right."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left * right  # type: ignore
        except TypeError:
            return INVALID


class DivOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Division: left / right. Returns Invalid on division by zero."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left / right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class FloorDivOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Floor division: left // right. Returns Invalid on division by zero."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left // right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class ModOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Modulo: left % right. Returns Invalid on division by zero."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left % right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return INVALID


class PowOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Power: left ** right."""

    def _apply(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left**right  # type: ignore
        except (TypeError, OverflowError):
            return INVALID
