"""Base class for binary operations.

All binary operations (two operands) inherit from BinaryOp and implement `_apply_op()`.
The base handles operand evaluation and special value propagation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from everyshape.typing import Sentinel, propagate_special

from ..conversion import literal
from .comp import Operation


if TYPE_CHECKING:
    from ..context import Context

__all__ = ["BinaryOp"]


class BinaryOp[ResultT](Operation[ResultT | Sentinel], ABC):
    """Base class for binary operations (two operands).

    Defines execution pattern:
    1. Evaluate both operands
    2. Propagate special values (Empty, Invalid)
    3. Apply operation via `_apply_op()`
    4. Return result

    Subclasses implement `_apply_op()` with operation-specific logic.
    Override `execute()` only when special handling is needed (e.g., short-circuit).

    Example:
        class AddOp(BinaryOp[ResultT]):
            def _apply_op(self, left: object, right: object) -> ResultT:
                return left + right
    """

    def __init__(self, left: object, right: object) -> None:
        """Initialize binary operation.

        Args:
            left: Left operand (can be Term or literal value)
            right: Right operand (can be Term or literal value)
        """
        self.children = (literal(left), literal(right))

    def execute(self, context: Context) -> ResultT | Sentinel:
        """Execute binary operation.

        Evaluates both operands, handles special values, and applies operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or Sentinel if operands are special values
        """
        left_val = self.children[0].execute(context)
        right_val = self.children[1].execute(context)

        # Propagate special values (Empty, Invalid)
        special = propagate_special(left_val, right_val)
        if special is not None:
            return special

        return self._apply_op(left_val, right_val)

    @abstractmethod
    def _apply_op(self, left: Any, right: Any, /) -> ResultT | Sentinel:  # noqa: ANN401
        """Apply the operator to operands.

        Subclasses override with operation-specific logic.

        Args:
            left: Evaluated left operand value
            right: Evaluated right operand value

        Returns:
            Operation result or Sentinel for errors
        """
        raise NotADirectoryError()

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r}, {self.children[1]!r})"
