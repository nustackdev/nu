"""Span — grouping (context boundary)."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..tree import Executable


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Span",
]


class Span(Executable[Executable], ABC):
    """Grouping node. Scopes context for children.

    Spans group children under a shared context boundary
    via an enter/exit lifecycle. They are transparent —
    removing a Span doesn't change what is computed, only
    what is shared during computation.

    Returns the last child's result (value-transparent).

    Children can be Terms, Flows, or Spans.
    Subclasses override enter/exit to shape context.
    """

    async def execute(self, ctx: Context) -> object:
        """Execute span: enter → run children → exit.

        Returns the last child's result for value transparency.
        """
        child_ctx = self.enter(ctx)
        result = None
        try:
            for child in self.children:
                result = await child.execute(child_ctx)
            self.exit_success(child_ctx)
        except Exception as e:
            self.exit_failure(child_ctx, e)
            raise
        return result

    def enter(self, ctx: Context) -> Context:
        """Scope context for children. Override to add handles/factories."""
        return ctx

    def exit_success(self, ctx: Context) -> None:
        """Cleanup after successful execution. Override for commit/close."""

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Cleanup after failed execution. Override for abort/close."""
