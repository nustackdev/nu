"""Time-backed Ops. SYNC-mode wrappers over the ``time`` module."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Command, Mode


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import FloatArg


__all__ = ["TimeSleep"]


class TimeSleep(Command):
    """Block the thread for ``delay`` seconds. Wraps `time.sleep`.

    Children: ``[delay]``
    """

    mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    async def run(self, ctx: Context) -> None:
        delay = await self.children[0].first(ctx)
        time.sleep(delay)

    def run_sync(self, ctx: Context) -> None:
        delay = self.children[0].first_sync(ctx)
        time.sleep(delay)
