"""Base class for unary operations.

All unary operations (single operand) inherit from UnaryOp and implement `_apply_op()`.
The base handles operand evaluation; subclasses focus on the operation logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.term import Operation, literal


if TYPE_CHECKING:
    from everyshape.term import Context, Term
    from everyshape.types import UnionBaseType

__all__ = ["UnaryOp"]


type OpArgument = Term | UnionBaseType


class UnaryOp[ResultT](Operation[ResultT]):
    """Base class for unary operations (single operand).

    Defines execution pattern:
    1. Evaluate operand
    2. Apply operation via `_apply_op()`
    3. Return result

    Subclasses implement `_apply_op()` with operation-specific logic.
    Override `execute()` only when special handling is needed.

    Example:
        class NegOp(UnaryOp[ResultT]):
            def _apply_op(self, operand: object) -> ResultT:
                return -operand
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize unary operation.

        Args:
            operand: Single operand (can be Term or literal value)
        """
        self.children = (literal(operand),)

    def execute(self, context: Context) -> ResultT:
        """Execute unary operation.

        Evaluates operand and applies operation logic.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        operand_val = self.children[0].execute(context)
        return self._apply_op(operand_val)

    def _apply_op(self, operand: object) -> ResultT:
        """Apply the operator to operand.

        Subclasses override with operation-specific logic.

        Args:
            operand: Evaluated operand value

        Returns:
            Operation result
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"
