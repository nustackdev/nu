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

from everyshape.typing import NAN, Sentinel, propagate_special

from ..term import Operation


if TYPE_CHECKING:
    from ..context import Context
    from ..term import Term
    from ..type import UnionBaseType


__all__ = [
    "AddOp",
    "AndOp",
    "BinaryOp",
    "BitwiseAndOp",
    "BitwiseOrOp",
    "DivOp",
    "EqOp",
    "FloorDivOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
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

type OpArgument = Term | UnionBaseType


class BinaryOp[ResultT](Operation[ResultT | Sentinel], ABC):
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
        self.children = (cast("Term", left), cast("Term", right))

    def execute(self, context: Context) -> ResultT | Sentinel:
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
    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
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


class AddOp[ResultT](BinaryOp[ResultT]):
    """Addition: left + right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left + right  # type: ignore
        except TypeError:
            return NAN


class SubOp[ResultT](BinaryOp[ResultT]):
    """Subtraction: left - right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left - right  # type: ignore
        except TypeError:
            return NAN


class MulOp[ResultT](BinaryOp[ResultT]):
    """Multiplication: left * right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left * right  # type: ignore
        except TypeError:
            return NAN


class DivOp[ResultT](BinaryOp[ResultT]):
    """Division: left / right. Returns NaN on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        # Explicit zero check before division
        try:
            return left / right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return NAN


class FloorDivOp[ResultT](BinaryOp[ResultT]):
    """Floor division: left // right. Returns NaN on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        # Explicit zero check before division
        try:
            return left // right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return NAN


class ModOp[ResultT](BinaryOp[ResultT]):
    """Modulo: left % right. Returns NaN on division by zero."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        # Explicit zero check before modulo
        try:
            return left % right  # type: ignore
        except (TypeError, ZeroDivisionError):
            return NAN


class PowOp[ResultT](BinaryOp[ResultT]):
    """Power: left ** right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left**right  # type: ignore
        except (TypeError, OverflowError):
            return NAN


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


class GtOp(BinaryOp[bool | Sentinel]):
    """Greater than: left > right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left > right  # type: ignore
        except TypeError:
            return NAN


class LtOp(BinaryOp[bool | Sentinel]):
    """Less than: left < right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left < right  # type: ignore
        except TypeError:
            return NAN


class EqOp(BinaryOp[bool | Sentinel]):
    """Equality: left == right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left == right  # type: ignore
        except TypeError:
            return NAN


class NeOp(BinaryOp[bool | Sentinel]):
    """Not equal: left != right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left != right  # type: ignore
        except TypeError:
            return NAN


class GeOp(BinaryOp[bool | Sentinel]):
    """Greater than or equal: left >= right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left >= right  # type: ignore
        except TypeError:
            return NAN


class LeOp(BinaryOp[bool | Sentinel]):
    """Less than or equal: left <= right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left <= right  # type: ignore
        except TypeError:
            return NAN


class IdCompOp(BinaryOp[bool | Sentinel]):
    """Identity comparison: left is right."""

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        try:
            return left is right  # type: ignore
        except TypeError:
            return NAN


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class AndOp[ResultT](BinaryOp[ResultT]):
    """Logical AND: left and right. Short-circuits at Python level."""

    def execute(self, context: Context) -> ResultT | Sentinel:
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

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        # Unreachable code, added for type checkers
        raise NotImplementedError


class OrOp[ResultT](BinaryOp[ResultT]):
    """Logical OR: left or right. Short-circuits at Python level."""

    def execute(self, context: Context) -> ResultT | Sentinel:
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

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        # Unreachable code, added for type checkers
        raise NotImplementedError


# =============================================================================
# BITWISE OPERATIONS
# =============================================================================


class XorOp[ResultT](BinaryOp[ResultT]):
    """Bitwise XOR: left ^ right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left ^ right  # type: ignore
        except TypeError:
            return NAN


class LShiftOp[ResultT](BinaryOp[ResultT]):
    """Left shift: left << right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left << right  # type: ignore
        except TypeError:
            return NAN


class RShiftOp[ResultT](BinaryOp[ResultT]):
    """Right shift: left >> right."""

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left >> right  # type: ignore
        except TypeError:
            return NAN


class BitwiseAndOp[ResultT](BinaryOp[ResultT]):
    """Bitwise AND: left & right.

    Note: This is distinct from AndOp (logical AND).
    Use .bitand() method to create this operation.
    """

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left & right  # type: ignore
        except TypeError:
            return NAN


class BitwiseOrOp[ResultT](BinaryOp[ResultT]):
    """Bitwise OR: left | right.

    Note: This is distinct from OrOp (logical OR).
    Use .bitor() method to create this operation.
    """

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        try:
            return left | right  # type: ignore
        except TypeError:
            return NAN
