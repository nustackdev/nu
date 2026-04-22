"""Assert — Atomic Command that validates a condition during execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.terms import Atomic


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import StrArg


__all__ = ["Assert"]


class Assert(Atomic):
    """Validate a condition during execution.

    Children: ``[condition, message]``

    Raises ``AssertionError`` when condition is falsy.
    """

    def __init__(self, condition: Any, message: StrArg = "Assertion failed") -> None:
        super().__init__(condition, message)

    async def run(self, ctx: Context) -> None:
        result = await self.children[0].first(ctx)
        if not result:
            message = await self.children[1].first(ctx)
            raise AssertionError(message)

    def run_sync(self, ctx: Context) -> None:
        result = self.children[0].first_sync(ctx)
        if not result:
            message = self.children[1].first_sync(ctx)
            raise AssertionError(message)
