"""Span - scoping Nu.

Wraps children with resource lifecycle (enter/exit).
Returns the last child's result (value-transparent).
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from .nu import Nu


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Span",
]


class Span(Nu[object], ABC):
    """Scoping Nu. Resource lifecycle for children.

    Spans group children under a shared context boundary
    via enter/exit. They are transparent - removing a Span
    doesn't change what is computed, only what is shared.
    """

    async def execute(self, ctx: Context) -> object:
        """Execute span: enter -> run children -> exit."""
        child_ctx = self.enter(ctx)
        result = None
        try:
            for child in self.children:
                result = await child.execute(child_ctx)
            self.exit_success(child_ctx)
        except BaseException as e:
            self.exit_failure(child_ctx, e)
            raise
        return result

    def enter(self, ctx: Context) -> Context:
        """Scope context for children. Override to add handles/factories."""
        return ctx

    def exit_success(self, ctx: Context) -> None:
        """Cleanup after successful execution. Override for commit/close."""

    def exit_failure(self, ctx: Context, error: BaseException) -> None:
        """Cleanup after failed execution. Override for abort/close."""

    @property
    def is_self_pure(self) -> bool:
        """Spans are pure - they scope resources but don't mutate."""
        return True
