"""Stream flow - drain-then-follow over ordered collections.

The ``cat file; tail -f`` of Nu. One declaration that handles
batch catch-up, live follow, and the seamless transition between them.

Children: [advance_op, change_op, body, key, log_key]
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu import Sentinel
from nu.terms import Calculation
from nu.utils import ensure_nu

from ..cursor import AdvanceCursorOp
from ..reactive import OnChildrenChangeOp


if TYPE_CHECKING:
    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "Stream",
]


class Stream(Calculation):
    """Drain-then-follow over an ordered collection.

    Iterates existing items (drain), then subscribes and follows new
    items (react). Transition is seamless - cursor tracks position.

    Children layout: [advance_op, change_op, body, key, log_key]
    """

    def __init__(
        self,
        source: object,
        body: Nu,
        *,
        key: StrArg = "stream_key",
        log_key: StrArg = "stream_log_key",
        cursor: object | None = None,
    ) -> None:
        source_term = ensure_nu(source)

        from nu.context import AttrRef

        cursor_ref = AttrRef(log_key)

        advance = AdvanceCursorOp(source_term, cursor_ref)
        change = OnChildrenChangeOp(source_term)

        super().__init__(advance, change, body, ensure_nu(key), ensure_nu(log_key))

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        key = await self.children[3].execute(ctx)
        log_key = await self.children[4].execute(ctx)

        if log_key not in ctx.attrs:
            ctx.attrs[log_key] = Sentinel()
        if key not in ctx.attrs:
            ctx.attrs[key] = Sentinel()

        await self._drain(ctx, key, log_key)
        await self._react(ctx, key, log_key)

    async def _drain(self, ctx: Context, key: str, log_key: str) -> None:
        """Drain existing items from source."""
        while True:
            result = await self.children[0].execute(ctx)
            if result is None:
                break
            log_k, actual_key = result
            ctx.attrs[key] = actual_key
            ctx.attrs[log_key] = log_k
            await self.children[2].execute(ctx)

    async def _react(self, ctx: Context, key: str, log_key: str) -> None:
        """Follow new items via reactive subscription."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()

        def on_change(_changed_key: object) -> None:
            loop.call_soon_threadsafe(event.set)

        sub = await self.children[1].execute(ctx)
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()
                await self._drain(ctx, key, log_key)
        finally:
            sub.unbind(on_change)
            sub.close()
