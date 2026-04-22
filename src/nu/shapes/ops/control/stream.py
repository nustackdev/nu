"""Stream flow - drain-then-follow over ordered collections.

The ``cat file; tail -f`` of Nu. One declaration that handles
batch catch-up, live follow, and the seamless transition between them.

Children: [advance_op, change_op, body, key, log_key]
"""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Interaction, Mode, Sentinel
from nu.utils import ensure_nu

from ..cursor import AdvanceCursorOp
from ..reactive import OnChildrenChangeOp


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "Stream",
]


class Stream(Interaction):
    """Drain-then-follow over an ordered collection.

    Iterates existing items (drain), then subscribes and follows new
    items (react). Transition is seamless - cursor tracks position.

    Children layout: [advance_op, change_op, body, key, log_key]
    """

    mode: ClassVar[Mode] = Mode.ASYNC

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

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        key = await self.children[3].afirst(ctx)
        log_key = await self.children[4].afirst(ctx)

        if log_key not in ctx.attrs:
            ctx.attrs[log_key] = Sentinel()
        if key not in ctx.attrs:
            ctx.attrs[key] = Sentinel()

        async for v in self._drain(ctx, key, log_key):
            yield v
        async for v in self._react(ctx, key, log_key):
            yield v

    async def _drain(self, ctx: Context, key: str, log_key: str) -> AsyncGenerator[Any, None]:
        """Drain existing items from source."""
        while True:
            result = await self.children[0].afirst(ctx)
            if result is None:
                break
            log_k, actual_key = result
            ctx.attrs[key] = actual_key
            ctx.attrs[log_key] = log_k
            async with aclosing(self.children[2].aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    async def _react(self, ctx: Context, key: str, log_key: str) -> AsyncGenerator[Any, None]:
        """Follow new items via reactive subscription."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()

        def on_change(_changed_key: object) -> None:
            loop.call_soon_threadsafe(event.set)

        sub = await self.children[1].afirst(ctx)
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()
                async for v in self._drain(ctx, key, log_key):
                    yield v
        finally:
            sub.unbind(on_change)
            sub.close()
