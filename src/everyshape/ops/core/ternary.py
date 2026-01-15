"""Base class for ternary operations.

All ternary operations (three operands) inherit from TernaryOp.
Unlike UnaryOp and BinaryOp, ternary ops often need custom `execute()` logic
(e.g., conditional evaluation, lazy evaluation of branches).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from everyshape.term import Operation, literal


if TYPE_CHECKING:
    from everyshape.term import Context

__all__ = ["TernaryOp"]


class TernaryOp[ResultT](Operation[ResultT], ABC):
    """Base class for ternary operations (three operands).

    Defines execution pattern:
    1. Evaluate all three operands
    2. Apply operation via `_apply_op()`
    3. Return result

    Subclasses implement `_apply_op()` with operation-specific logic.
    Override `execute()` only when special handling is needed (e.g., lazy evaluation).

    Example:
        class ReplaceOp(TernaryOp[str]):
            def _apply_op(self, text: object, old: object, new: object) -> str:
                return str(text).replace(str(old), str(new))
    """

    def __init__(self, first: object, second: object, third: object) -> None:
        """Initialize ternary operation.

        Args:
            first: First operand (can be Term or literal value)
            second: Second operand (can be Term or literal value)
            third: Third operand (can be Term or literal value)
        """
        self.children = (literal(first), literal(second), literal(third))

    def execute(self, context: Context) -> ResultT:
        """Execute ternary operation.

        Evaluates all operands and applies operation logic.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        first_val = self.children[0].execute(context)
        second_val = self.children[1].execute(context)
        third_val = self.children[2].execute(context)
        return self._apply_op(first_val, second_val, third_val)

    @abstractmethod
    def _apply_op(self, first: Any, second: Any, third: Any, /) -> ResultT:  # noqa: ANN401
        """Apply the operator to operands.

        Subclasses override with operation-specific logic.

        Args:
            first: Evaluated first operand value
            second: Evaluated second operand value
            third: Evaluated third operand value

        Returns:
            Operation result
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r}, {self.children[1]!r}, {self.children[2]!r})"
