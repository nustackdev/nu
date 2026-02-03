"""If -- conditional execution flow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everybase import Flow

from ._util import _ensure_term


if TYPE_CHECKING:
    from everybase import Context, Executable


__all__ = [
    "If",
]


class If(Flow):
    """Conditional execution.

    Children layout: [condition, then_branch, else_branch?]

    Condition is auto-wrapped via Const if a literal is passed.
    All computation parameters are children -- fully transparent
    to tree transforms.

    Example::

        If(x > 0, handle_positive, handle_non_positive)
        If(True, always_runs)
    """

    def __init__(
        self,
        condition: Any,
        then_branch: Executable,
        else_branch: Executable | None = None,
    ) -> None:
        """Initialize conditional flow.

        Args:
            condition: Term or literal evaluated as boolean.
            then_branch: Executed when condition is truthy.
            else_branch: Executed when condition is falsy (optional).
        """
        condition = _ensure_term(condition)
        if else_branch is not None:
            super().__init__(condition, then_branch, else_branch)
        else:
            super().__init__(condition, then_branch)

    async def execute(self, ctx: Context) -> None:
        """Evaluate condition and execute the appropriate branch."""
        if await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)
        elif self.child_count > 2:
            await self.children[2].execute(ctx)
