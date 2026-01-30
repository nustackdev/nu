"""Conditional morphisms.

ConditionalOp: Ternary conditional (a if b else c)

Overrides execute() to evaluate condition first, then only the selected branch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import TernaryOperation


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "ConditionalOp",
]


class ConditionalOp[ResultT](TernaryOperation[ResultT]):
    """Conditional ternary: value_if_true if condition else value_if_false.

    Arguments order: (value_if_true, condition, value_if_false)
    Only evaluates the selected branch for efficiency.
    """

    def execute(self, ctx: Context) -> ResultT:
        """Execute conditional with lazy branch evaluation.

        Evaluates condition first, then only the selected branch.
        """
        condition = self._children[1].execute(ctx)

        if condition:
            return self._children[0].execute(ctx)
        return self._children[2].execute(ctx)

    def apply(self, first: object, second: object, third: object) -> ResultT:
        """Simple apply for completeness."""
        return first if second else third  # type: ignore
