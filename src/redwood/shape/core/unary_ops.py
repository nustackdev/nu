from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from redwood.types import NaN, propagate_special

from ..term import Operation


if TYPE_CHECKING:
    from ..context import Context
    from ..term import RValue


class UnaryOp[T](Operation[T]):
    """Unary operation on a single term.

    Supports negation, logical not, and other single-operand operations.
    Handles special value propagation.

    Operators:
        neg: arithmetic negation (-x)
        not: logical negation (not x)
        abs: absolute value (abs(x))

    Example:
        >>> UnaryOp("neg", balance.get())
        >>> UnaryOp("not", is_active.get())
    """

    # Operator implementations
    _OPERATORS: ClassVar[dict[str, Any]] = {
        "neg": lambda x: -x,
        "not": lambda x: not x,
        "abs": lambda x: abs(x),
    }

    def __init__(self, op: str, operand: RValue) -> None:
        """Initialize unary operation.

        Args:
            op: Operator name (neg, not, abs)
            operand: Single operand

        Raises:
            ValueError: If operator is unknown
        """
        if op not in self._OPERATORS:
            raise ValueError(f"Unknown operator: {op}")

        self.op = op
        self.children = (operand,)

    def execute(self, context: Context) -> T:
        """Execute unary operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN if operand is special value
        """
        # Evaluate operand
        operand_val = self.children[0].execute(context)

        # Handle special values
        special = propagate_special(operand_val)
        if special is not None:
            return special  # type: ignore[return-value]

        # Apply operator
        operator = self._OPERATORS[self.op]
        try:
            result = operator(operand_val)
            return result if result is not None else NaN  # type: ignore[return-value]
        except (TypeError, ValueError, OverflowError):
            return NaN  # type: ignore[return-value]

    def __repr__(self) -> str:
        """String representation."""
        return f"UnaryOp({self.op!r}, {self.children[0]!r})"
