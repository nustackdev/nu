"""Basic operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from redwood.abc import NaN, propagate_special
from redwood.shape.evaluation import Operation, RValue


if TYPE_CHECKING:
    from redwood.shape.types import Context


__all__ = [
    "BinaryOp",
    "LiteralValue",
]


class LiteralValue(Operation):
    """Constant literal value.

    Represents a compile-time constant (42, "hello", True, etc.)

    Example:
        LiteralValue(10).execute(ctx) → 10
    """

    def __init__(self, value: object) -> None:
        """Initialize literal.

        Args:
            value: The constant value
        """
        self.value = value

    def execute(self, context: Context) -> object:
        """Return the literal value.

        Args:
            context: Unused

        Returns:
            The constant value
        """
        return self.value


class BinaryOp(Operation):
    """Binary operation between two RValues.

    Supports comparison, arithmetic, and logical operations.
    Handles special value propagation.

    Example:
        BinaryOp("gt", price.get(), LiteralValue(100))
        → Evaluates to: price > 100
    """

    # Operator implementations
    _OPERATORS: ClassVar[dict[str, Any]] = {
        # Comparison
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "ge": lambda a, b: a >= b,
        "le": lambda a, b: a <= b,
        # Arithmetic
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b if b != 0 else None,
        # Logical
        "and": lambda a, b: a and b,
        "or": lambda a, b: a or b,
    }

    def __init__(self, op: str, left: RValue, right: RValue) -> None:
        """Initialize binary operation.

        Args:
            op: Operator name (gt, lt, add, sub, etc.)
            left: Left operand
            right: Right operand
        """
        self.op = op
        self.children = (left, right)

    def execute(self, context: Context) -> object:
        """Execute binary operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN if operands are special
        """
        # Evaluate operands
        left_val = self.children[0].execute(context)
        right_val = self.children[1].execute(context)

        # Handle special values
        special = propagate_special(left_val, right_val)
        if special is not None:
            return special

        # Apply operator
        operator = self._OPERATORS.get(self.op)
        if operator is None:
            raise ValueError(f"Unknown operator: {self.op}")

        try:
            result = operator(left_val, right_val)
            return result if result is not None else NaN
        except (TypeError, ValueError, ZeroDivisionError):
            return NaN
