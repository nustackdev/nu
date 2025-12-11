"""Binary operations with graceful special value handling.

This module provides type-safe binary operations, each as its own atomic class:

Arithmetic: AddOp, SubOp, MulOp, DivOp, ModOp, PowOp
Comparison: GtOp, LtOp, EqOp, NeOp, GeOp, LeOp
Logical: AndOp, OrOp
Bitwise: XorOp, LShiftOp, RShiftOp
  (Note: & and | are blocked in ergonomics for safety - use .and_() and .or_() instead)

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

from everyshape.types import NAN, SpecialValue, propagate_special

from ..term import Operation


if TYPE_CHECKING:
    from ..context import ContextProtocol
    from ..term import RValue
    from .ergonomics import ErgonomicsMixin


__all__ = [
    "AddOp",
    "AndOp",
    "BinaryOp",
    "DivOp",
    "EqOp",
    "FloorDivOp",
    "GeOp",
    "GtOp",
    "LShiftOp",
    "LeOp",
    "LtOp",
    "ModOp",
    "MulOp",
    "NeOp",
    "OrOp",
    "PowOp",
    "RShiftOp",
    "SubOp",
    "XorOp",
]


# =============================================================================
# ABSTRACT BINARY OPERATION
# =============================================================================

type OpArgument = RValue | ErgonomicsMixin


class BinaryOp[ResultT, ContextT: ContextProtocol](
    Operation[ResultT | SpecialValue, ContextT], ABC
):
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

    def execute(self, context: ContextT) -> ResultT | SpecialValue:
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
        return self._apply_op(left_val, right_val)

    @abstractmethod
    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
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


class AddOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Addition: left + right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left + right  # type: ignore
        except TypeError:
            return NAN


class SubOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Subtraction: left - right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left - right  # type: ignore
        except TypeError:
            return NAN


class MulOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Multiplication: left * right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left * right  # type: ignore
        except TypeError:
            return NAN


class DivOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Division: left / right. Returns NaN on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        # Explicit zero check before division
        if right == 0:
            return NAN
        try:
            return left / right  # type: ignore
        except TypeError:
            return NAN


class FloorDivOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Floor division: left // right. Returns NaN on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        # Explicit zero check before division
        if right == 0:
            return NAN
        try:
            return left // right  # type: ignore
        except TypeError:
            return NAN


class ModOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Modulo: left % right. Returns NaN on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        # Explicit zero check before modulo
        if right == 0:
            return NAN
        try:
            return left % right  # type: ignore
        except TypeError:
            return NAN


class PowOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Power: left ** right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left**right  # type: ignore
        except (TypeError, OverflowError):
            return NAN


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


class GtOp[ContextT: ContextProtocol](BinaryOp[bool | SpecialValue, ContextT]):
    """Greater than: left > right."""

    def _apply_op(self, left: object, right: object) -> bool | SpecialValue:
        try:
            return left > right  # type: ignore
        except TypeError:
            return NAN


class LtOp[ContextT: ContextProtocol](BinaryOp[bool | SpecialValue, ContextT]):
    """Less than: left < right."""

    def _apply_op(self, left: object, right: object) -> bool | SpecialValue:
        try:
            return left < right  # type: ignore
        except TypeError:
            return NAN


class EqOp[ContextT: ContextProtocol](BinaryOp[bool | SpecialValue, ContextT]):
    """Equality: left == right."""

    def _apply_op(self, left: object, right: object) -> bool | SpecialValue:
        try:
            return left == right  # type: ignore
        except TypeError:
            return NAN


class NeOp[ContextT: ContextProtocol](BinaryOp[bool | SpecialValue, ContextT]):
    """Not equal: left != right."""

    def _apply_op(self, left: object, right: object) -> bool | SpecialValue:
        try:
            return left != right  # type: ignore
        except TypeError:
            return NAN


class GeOp[ContextT: ContextProtocol](BinaryOp[bool | SpecialValue, ContextT]):
    """Greater than or equal: left >= right."""

    def _apply_op(self, left: object, right: object) -> bool | SpecialValue:
        try:
            return left >= right  # type: ignore
        except TypeError:
            return NAN


class LeOp[ContextT: ContextProtocol](BinaryOp[bool | SpecialValue, ContextT]):
    """Less than or equal: left <= right."""

    def _apply_op(self, left: object, right: object) -> bool | SpecialValue:
        try:
            return left <= right  # type: ignore
        except TypeError:
            return NAN


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class AndOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Logical AND: left and right. Short-circuits at Python level."""

    def execute(self, context: ContextT) -> ResultT | SpecialValue:
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

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        # Unreachable code, added for type checkers
        raise NotImplementedError


class OrOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Logical OR: left or right. Short-circuits at Python level."""

    def execute(self, context: ContextT) -> ResultT | SpecialValue:
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

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        # Unreachable code, added for type checkers
        raise NotImplementedError


# =============================================================================
# BITWISE OPERATIONS
# =============================================================================


class XorOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Bitwise XOR: left ^ right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left ^ right  # type: ignore
        except TypeError:
            return NAN


class LShiftOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Left shift: left << right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left << right  # type: ignore
        except TypeError:
            return NAN


class RShiftOp[ResultT, ContextT: ContextProtocol](BinaryOp[ResultT, ContextT]):
    """Right shift: left >> right."""

    def _apply_op(self, left: object, right: object) -> ResultT | SpecialValue:
        try:
            return left >> right  # type: ignore
        except TypeError:
            return NAN
