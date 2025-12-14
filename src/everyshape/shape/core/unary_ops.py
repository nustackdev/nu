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

from everyshape.types import NAN, SpecialValue, is_empty, is_nan

from ..term import Operation


if TYPE_CHECKING:
    from ..context import ContextProtocol
    from ..term import RValue
    from .ergonomics import ErgonomicsMixin

__all__ = [
    "AbsOp",
    "BitwiseNotOp",
    "BoolOp",
    "IsEmptyOp",
    "IsNaNOp",
    "NegOp",
    "NotEmptyOp",
    "NotNaNOp",
    "NotOp",
    "PosOp",
    "UnaryOp",
]

# =============================================================================
# ABSTRACT UNARY OPERATION
# =============================================================================

type OpArgument = RValue | ErgonomicsMixin


class UnaryOp[ResultT, ContextT: ContextProtocol](Operation[ResultT, ContextT]):
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

    def execute(self, context: ContextT) -> ResultT:
        """Execute unary operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN if operand is special value
        """
        # Evaluate operand
        operand_val = self.children[0].execute(context)

        # Apply operator-specific logic
        return self._apply_op(operand_val)

    def _apply_op(self, operand: object) -> ResultT:
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


class NegOp[ResultT, ContextT: ContextProtocol](UnaryOp[ResultT | SpecialValue, ContextT]):
    """Negation: -operand."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        try:
            return -operand  # type: ignore
        except TypeError:
            return NAN


class AbsOp[ResultT, ContextT: ContextProtocol](UnaryOp[ResultT | SpecialValue, ContextT]):
    """Absolute value: abs(operand)."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        try:
            return abs(operand)  # type: ignore
        except TypeError:
            return NAN


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class NotOp[ResultT, ContextT: ContextProtocol](UnaryOp[ResultT | SpecialValue, ContextT]):
    """Logical NOT: not operand.

    Python's 'not' keyword cannot be overloaded.
    Use .not_() method in ergonomics instead.
    """

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        return not operand  # type: ignore


class BitwiseNotOp[ResultT, ContextT: ContextProtocol](UnaryOp[ResultT | SpecialValue, ContextT]):
    """Bitwise NOT: ~operand (two's complement).

    Note: Python's ~ operator is blocked in ergonomics.
    Use .bitnot() method instead.
    """

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        try:
            return ~operand  # type: ignore
        except TypeError:
            return NAN


class PosOp[ResultT, ContextT: ContextProtocol](UnaryOp[ResultT | SpecialValue, ContextT]):
    """Unary plus: +operand."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        try:
            return +operand  # type: ignore
        except TypeError:
            return NAN


class BoolOp[ContextT: ContextProtocol](UnaryOp[bool, ContextT]):
    """Operand is not of NaN type."""

    def _apply_op(self, operand: object) -> bool:
        return bool(operand)


# =============================================================================
# CONVENIENCE SPECIAL OPERATIONS (methods for working with special values)
# =============================================================================


class IsEmptyOp[ContextT: ContextProtocol](UnaryOp[bool, ContextT]):
    """Operand is of Empty type."""

    def _apply_op(self, operand: object) -> bool:
        return is_empty(operand)


class NotEmptyOp[ContextT: ContextProtocol](UnaryOp[bool, ContextT]):
    """Operand is not of Empty type."""

    def _apply_op(self, operand: object) -> bool:
        return not is_empty(operand)


class IsNaNOp[ContextT: ContextProtocol](UnaryOp[bool, ContextT]):
    """Operand is of NaN type."""

    def _apply_op(self, operand: object) -> bool:
        return is_nan(operand)


class NotNaNOp[ContextT: ContextProtocol](UnaryOp[bool, ContextT]):
    """Operand is not of NaN type."""

    def _apply_op(self, operand: object) -> bool:
        return not is_nan(operand)
