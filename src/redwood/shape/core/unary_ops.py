"""Unary operations with graceful special value handling.

This module provides type-safe unary operations, each as its own atomic class:

Arithmetic: NegOp, AbsOp
Logical: NotOp (internal only, not exposed via ergonomics)

Design principles:
1. Atomic classes: one operator = one class
2. Graceful degradation: return NaN/Empty instead of raising exceptions
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve generic T for type inference
5. Explicit handling: no generic try-catches, specific error cases handled
6. Backward compatibility: UnaryOp factory maintains string-based API

Usage:
    # Direct instantiation (specific operator class)
    NegOp(balance.get())
    AbsOp(temperature.get())

    # Factory (string-based, backward compatible)
    UnaryOp("neg", balance.get())

    # Via operator overloading (ergonomics.py)
    -price_var  # → NegOp(price_var)
    abs(price_var)  # → AbsOp(price_var)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from redwood.types import NAN, SpecialValue, propagate_special

from ..term import Operation


if TYPE_CHECKING:
    from ..context import Context
    from ..term import RValue
    from .ergonomics import ErgonomicsMixin

__all__ = [
    "AbsOp",
    "NegOp",
    "NotOp",
    "UnaryOp",
]

# =============================================================================
# ABSTRACT UNARY OPERATION
# =============================================================================

type OpArgument = RValue | ErgonomicsMixin


class UnaryOp[T](Operation[T]):
    """Base class for unary operations.

    Defines execution pattern: evaluate operand → handle special values →
    apply operator → return result.

    Subclasses implement specific operators (NegOp, AbsOp, etc.).
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize unary operation.

        Args:
            op: Operator name
            operand: Single operand
        """
        self.children = (cast("RValue", operand),)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute unary operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN if operand is special value
        """
        # Evaluate operand
        operand_val = self.children[0].execute(context)

        # Handle special values (Empty, NaN)
        special = propagate_special(operand_val)
        if special is not None:
            return special  # type: ignore[return-value]

        # Apply operator-specific logic
        return self._apply_op(operand_val)  # type: ignore[return-value]

    def _apply_op(self, operand: object) -> T | SpecialValue:
        """Apply the operator to operand.

        Subclasses override with operator-specific logic.

        Args:
            operand: Operand (not special)

        Returns:
            Operation result or NaN for errors
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"


# =============================================================================
# ARITHMETIC OPERATIONS
# =============================================================================


class NegOp[T](UnaryOp[T]):
    """Negation: -operand."""

    def _apply_op(self, operand: object) -> T | SpecialValue:
        try:
            return -operand  # type: ignore
        except TypeError:
            return NAN


class AbsOp[T](UnaryOp[T]):
    """Absolute value: abs(operand)."""

    def _apply_op(self, operand: object) -> T | SpecialValue:
        try:
            return abs(operand)  # type: ignore
        except TypeError:
            return NAN


# =============================================================================
# LOGICAL OPERATIONS (Internal only, not exposed via ergonomics)
# =============================================================================


class NotOp[T](UnaryOp[T]):
    """Logical NOT: not operand.

    Internal only - Python's 'not' keyword cannot be overloaded.
    Use explicit comparisons in ergonomics instead.
    """

    def _apply_op(self, operand: object) -> T | SpecialValue:
        return not operand  # type: ignore
