"""Conditional operations.

ConditionalOp: Ternary conditional (a if b else c)

Overrides execute() to evaluate condition first, then only the selected branch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .core import TernaryOp


if TYPE_CHECKING:
    from everyshape.term import Context


__all__ = [
    "ConditionalOp",
]


class ConditionalOp[ResultT](TernaryOp[ResultT]):
    """Conditional ternary: value_if_true if condition else value_if_false.

    Arguments order: (value_if_true, condition, value_if_false)
    Only evaluates the selected branch for efficiency.
    """

    def execute(self, context: Context) -> ResultT:
        """Execute conditional with lazy branch evaluation.

        Evaluates condition first, then only the selected branch.

        Args:
            context: Execution context

        Returns:
            Result from the selected branch
        """
        condition = self.children[1].execute(context)

        if condition:
            return self.children[0].execute(context)
        return self.children[2].execute(context)

    def _apply_op(self, first: object, second: object, third: object) -> ResultT:
        """Simple apply for completeness."""
        return first if second else third  # type: ignore
