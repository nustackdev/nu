from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast

from redwood.types import NaN, propagate_special

from ..term import Operation


if TYPE_CHECKING:
    from ..context import Context
    from ..term import RValue
    from .ergonomics import ErgonomicsMixin


type OpArgument = RValue | ErgonomicsMixin


class BinaryOp[T](Operation[T]):
    """Binary operation between two terms.

    Supports arithmetic, comparison, and logical operations.
    Handles special value propagation (Empty, NaN).

    Operators:
        Arithmetic: add, sub, mul, div, mod, pow
        Comparison: gt, lt, eq, ne, ge, le
        Logical: and, or

    Example:
        >>> BinaryOp("add", price.get(), LiteralValue(10))
        >>> BinaryOp("gt", balance.get(), LiteralValue(100))
    """

    # Operator implementations
    _OPERATORS: ClassVar[dict[str, Any]] = {
        # Arithmetic
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b if b != 0 else NaN,
        "mod": lambda a, b: a % b if b != 0 else NaN,
        "pow": lambda a, b: a**b,
        # Comparison
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "ge": lambda a, b: a >= b,
        "le": lambda a, b: a <= b,
        # Logical
        "and": lambda a, b: a and b,
        "or": lambda a, b: a or b,
    }

    def __init__(self, op: str, left: OpArgument, right: OpArgument) -> None:
        """Initialize binary operation.

        Args:
            op: Operator name (add, sub, gt, lt, etc.)
            left: Left operand
            right: Right operand

        Raises:
            ValueError: If operator is unknown
        """
        if op not in self._OPERATORS:
            raise ValueError(f"Unknown operator: {op}")

        self.op = op
        self.children = (cast("RValue", left), cast("RValue", right))

    def execute(self, context: Context) -> T:
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
            return special  # type: ignore[return-value]

        # Apply operator
        operator = self._OPERATORS[self.op]
        try:
            result = operator(left_val, right_val)
            return result if result is not None else NaN  # type: ignore[return-value]
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            return NaN  # type: ignore[return-value]

    def __repr__(self) -> str:
        """String representation."""
        return f"BinaryOp({self.op!r}, {self.children[0]!r}, {self.children[1]!r})"
