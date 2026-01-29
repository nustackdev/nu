"""Span -- cohesion boundary (2-cell / region)."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everyabc.tree import Executable


if TYPE_CHECKING:
    from everyabc.context import Context


__all__ = [
    "Span",
]


class Span(Executable[Executable], ABC):
    """Cohesion boundary (2-cell). Context shaper.

    Spans scope context for their children via enter/exit lifecycle.
    On execution:
        1. enter(ctx) → child_ctx (add handles, factories)
        2. Execute children with child_ctx
        3. exit_success(child_ctx) or exit_failure(child_ctx, error)

    Subclasses override enter/exit to shape context.
    Default implementations are transparent (pass-through).

    Concrete spans (PVAtomic, PVSnapshot, Traced, etc.)
    are defined downstream.

    Design rules:
        S2: Span transparency -- removing spans doesn't change computation.
        S4: Spans own exactly one concern -- cohesion (what's shared).
    """

    async def execute(self, ctx: Context) -> None:
        """Execute span: enter → run children → exit.

        Calls enter() to scope context, executes children sequentially,
        then calls exit_success/exit_failure for cleanup.
        """
        child_ctx = self.enter(ctx)
        try:
            for child in self.children:
                await child.execute(child_ctx)
            self.exit_success(child_ctx)
        except Exception as e:
            self.exit_failure(child_ctx, e)
            raise

    def enter(self, ctx: Context) -> Context:
        """Scope context for children. Override to add handles/factories."""
        return ctx

    def exit_success(self, ctx: Context) -> None:
        """Cleanup after successful execution. Override for commit/close."""

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Cleanup after failed execution. Override for abort/close."""
