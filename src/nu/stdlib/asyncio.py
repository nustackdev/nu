"""Asyncio-backed Ops. ASYNC-mode wrappers over asyncio primitives."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Command, Mode


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import FloatArg


__all__ = ["AsyncSleep"]


class AsyncSleep(Command):
    """Yield to the event loop for ``delay`` seconds. Wraps `asyncio.sleep`.

    Children: ``[delay]``
    """

    mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    async def run(self, ctx: Context) -> None:
        delay = await self.children[0].first(ctx)
        await asyncio.sleep(delay)
