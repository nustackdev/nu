"""Base class for ternary operations.

All ternary operations (three operands) inherit from TernaryOp.
Unlike UnaryOp and BinaryOp, ternary ops often need custom `execute()` logic
(e.g., conditional evaluation, lazy evaluation of branches).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, cast

from everyshape.term import Operation


if TYPE_CHECKING:
    from everyshape.term import Context, Term
    from everyshape.types import UnionBaseType

__all__ = ["TernaryOp"]


type OpArgument = Term | UnionBaseType


class TernaryOp[ResultT](Operation[ResultT]):
    """Base class for ternary operations (three operands).

    Ternary operations often require custom execution logic:
    - ConditionalOp: evaluates condition first, then only one branch
    - SliceOp: may have optional operands

    Subclasses typically override `execute()` directly rather than `_apply_op()`.

    Example:
        class ConditionalOp(TernaryOp[ResultT]):
            def execute(self, context: Context) -> ResultT:
                condition = self.children[1].execute(context)
                if condition:
                    return self.children[0].execute(context)
                return self.children[2].execute(context)
    """

    def __init__(self, first: OpArgument, second: OpArgument, third: OpArgument) -> None:
        """Initialize ternary operation.

        Args:
            first: First operand (can be Term or literal value)
            second: Second operand (can be Term or literal value)
            third: Third operand (can be Term or literal value)
        """
        self.children = (cast("Term", first), cast("Term", second), cast("Term", third))

    @abstractmethod
    def execute(self, context: Context) -> ResultT:
        """Execute ternary operation.

        Subclasses implement operation-specific execution logic.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        ...

    def _apply_op(self, first: object, second: object, third: object) -> ResultT:
        """Apply the operator to operands.

        Optional hook for subclasses that want simple apply semantics.
        Most ternary ops override `execute()` directly instead.

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
