"""Binary operations with graceful special value handling.

This module provides type-safe binary operations, each as its own atomic class:

Arithmetic: AddOp, SubOp, MulOp, DivOp, ModOp, PowOp
Comparison: GtOp, LtOp, EqOp, NeOp, GeOp, LeOp
Logical: AndOp, OrOp

Design principles:
1. Atomic classes: one operator = one class
2. Graceful degradation: return NAN/Empty instead of raising exceptions
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve generic T for type inference
5. Explicit handling: no generic try-catches, specific error cases handled
6. Backward compatibility: BinaryOp factory maintains string-based API

Usage:
    # Direct instantiation (specific operator class)
    AddOp(price.get(), LiteralValue(10))
    GtOp(balance.get(), LiteralValue(100))

    # Factory (string-based, backward compatible)
    BinaryOp("add", price.get(), LiteralValue(10))

    # Via operator overloading (ergonomics.py)
    price_var + 10    # → AddOp(price_var, LiteralValue(10))
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from redwood.types import NAN, SpecialValue, propagate_special

from ..term import Operation


if TYPE_CHECKING:
    from ..context import Context
    from ..term import RValue
    from .ergonomics import ErgonomicsMixin


type OpArgument = RValue | ErgonomicsMixin


__all__ = [
    "AddOp",
    "AndOp",
    "BinaryOp",
    "DivOp",
    "EqOp",
    "GeOp",
    "GtOp",
    "LeOp",
    "LtOp",
    "ModOp",
    "MulOp",
    "NeOp",
    "OrOp",
    "PowOp",
    "SubOp",
]


# =============================================================================
# ABSTRACT BINARY OPERATION
# =============================================================================


class BinaryOp[T](Operation[T], ABC):
    """Base class for binary operations.

    Defines execution pattern: evaluate operands → handle special values →
    apply operator → return result.

    Subclasses implement specific operators (AddOp, SubOp, etc.).
    """

    def __init__(self, left: OpArgument, right: OpArgument) -> None:
        """Initialize binary operation.

        Args:
            op: Operator name
            left: Left operand
            right: Right operand
        """
        self.children = (cast("RValue", left), cast("RValue", right))

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute binary operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN if operands are special values
        """
        # Evaluate operands
        left_val = self.children[0].execute(context)
        right_val = self.children[1].execute(context)

        # Handle special values (Empty, NaN)
        special = propagate_special(left_val, right_val)
        if special is not None:
            return special

        # Apply operator-specific logic
        return self._apply_op(left_val, right_val)  # type: ignore[return-value]

    @abstractmethod
    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        """Apply the operator to operands.

        Subclasses override with operator-specific logic.

        Args:
            left: Left operand (not special)
            right: Right operand (not special)

        Returns:
            Operation result or NaN for errors
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r}, {self.children[1]!r})"


# =============================================================================
# ARITHMETIC OPERATIONS
# =============================================================================


class AddOp[T](BinaryOp[T]):
    """Addition: left + right."""

    op: str = "add"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left + right  # type: ignore
        except TypeError:
            return NAN


class SubOp[T](BinaryOp[T]):
    """Subtraction: left - right."""

    op: str = "sub"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left - right  # type: ignore
        except TypeError:
            return NAN


class MulOp[T](BinaryOp[T]):
    """Multiplication: left * right."""

    op: str = "mul"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left * right  # type: ignore
        except TypeError:
            return NAN


class DivOp[T](BinaryOp[T]):
    """Division: left / right. Returns NaN on division by zero."""

    op: str = "div"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        # Explicit zero check before division
        if right == 0:
            return NAN
        try:
            return left / right  # type: ignore
        except TypeError:
            return NAN


class ModOp[T](BinaryOp[T]):
    """Modulo: left % right. Returns NaN on division by zero."""

    op: str = "mod"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        # Explicit zero check before modulo
        if right == 0:
            return NAN
        try:
            return left % right  # type: ignore
        except TypeError:
            return NAN


class PowOp[T](BinaryOp[T]):
    """Power: left ** right."""

    op: str = "pow"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left**right  # type: ignore
        except (TypeError, OverflowError):
            return NAN


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


class GtOp[T](BinaryOp[T]):
    """Greater than: left > right."""

    op: str = "gt"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left > right  # type: ignore
        except TypeError:
            return NAN


class LtOp[T](BinaryOp[T]):
    """Less than: left < right."""

    op: str = "lt"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left < right  # type: ignore
        except TypeError:
            return NAN


class EqOp[T](BinaryOp[T]):
    """Equality: left == right."""

    op: str = "eq"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left == right  # type: ignore
        except TypeError:
            return NAN


class NeOp[T](BinaryOp[T]):
    """Not equal: left != right."""

    op: str = "ne"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left != right  # type: ignore
        except TypeError:
            return NAN


class GeOp[T](BinaryOp[T]):
    """Greater than or equal: left >= right."""

    op: str = "ge"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left >= right  # type: ignore
        except TypeError:
            return NAN


class LeOp[T](BinaryOp[T]):
    """Less than or equal: left <= right."""

    op: str = "le"

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        try:
            return left <= right  # type: ignore
        except TypeError:
            return NAN


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class AndOp[T](BinaryOp[T]):
    """Logical AND: left and right. Short-circuits at Python level."""

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute AND with short-circuit evaluation.

        Evaluates left, and only if truthy, evaluates right.

        Args:
            context: Execution context

        Returns:
            Result of left and right, or NaN if special values
        """
        left_val = self.children[0].execute(context)

        # Handle special values for left
        sp = propagate_special(left_val)
        if sp is not None:
            return sp

        # Short-circuit: if left is falsy, return left
        if not left_val:
            return left_val

        # Evaluate right
        right_val = self.children[1].execute(context)

        # Handle special values for right
        special = propagate_special(right_val)
        if special is not None:
            return special

        return left_val and right_val

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        # Unreachable code, added for type checkers
        raise NotImplementedError


class OrOp[T](BinaryOp[T]):
    """Logical OR: left or right. Short-circuits at Python level."""

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute OR with short-circuit evaluation.

        Evaluates left, and only if falsy, evaluates right.

        Args:
            context: Execution context

        Returns:
            Result of left or right, or NaN if special values
        """
        left_val = self.children[0].execute(context)

        # Handle special values for left
        sp = propagate_special(left_val)
        if sp is not None:
            return sp

        # Short-circuit: if left is truthy, return left
        if left_val:
            return left_val  # type: ignore[return-value]

        # Evaluate right
        right_val = self.children[1].execute(context)

        # Handle special values for right
        special = propagate_special(right_val)
        if special is not None:
            return special  # type: ignore[return-value]

        return left_val or right_val  # type: ignore[return-value]

    def _apply_op(self, left: object, right: object) -> T | SpecialValue:
        # Unreachable code, added for type checkers
        raise NotImplementedError
