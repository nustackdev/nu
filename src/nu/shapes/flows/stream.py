"""Stream flow — drain-then-follow over ordered collections.

The ``cat file; tail -f`` of Nu. One declaration that handles batch
catch-up, live follow, and the seamless transition between them.

Children: [advance, change, body, key, log_key]
"""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.nu import NuBase
from nu.terms.types import Mode

from ..queries.cursor import _UNSET, AdvanceCursor
from ..queries.reactive import OnChildrenChange


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "Stream",
]


class Stream(NuBase):
    """Drain-then-follow over an ordered collection.

    Iterates existing items (drain), then subscribes and follows new items
    (react). Transition is seamless — cursor tracks position.

    Children layout: [advance, change, body, key, log_key]
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(
        self,
        source: object,
        body: Nu,
        *,
        key: StrArg = "stream_key",
        log_key: StrArg = "stream_log_key",
        cursor: object | None = None,
    ) -> None:
        from nu.context import AttrRef

        cursor_ref = AttrRef(log_key)

        advance = AdvanceCursor(source, cursor_ref)
        change = OnChildrenChange(source)

        super().__init__(advance, change, body, key, log_key)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        from nu import runtime

        key = await runtime.afirst(self._children[3], ctx)
        log_key = await runtime.afirst(self._children[4], ctx)

        if log_key not in ctx.attrs:
            ctx.attrs[log_key] = _UNSET
        if key not in ctx.attrs:
            ctx.attrs[key] = _UNSET

        async for v in self._drain(ctx, key, log_key):
            yield v
        async for v in self._react(ctx, key, log_key):
            yield v

    async def _drain(self, ctx: Context, key: str, log_key: str) -> AsyncGenerator[Any, None]:
        """Drain existing items from source."""
        from nu import runtime

        while True:
            result = await runtime.afirst(self._children[0], ctx)
            if result is None:
                break
            log_k, actual_key = result
            ctx.attrs[key] = actual_key
            ctx.attrs[log_key] = log_k
            async with aclosing(self._children[2].aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    async def _react(self, ctx: Context, key: str, log_key: str) -> AsyncGenerator[Any, None]:
        """Follow new items via reactive subscription."""
        from nu import runtime

        loop = asyncio.get_running_loop()
        event = asyncio.Event()

        def on_change(_changed_key: object) -> None:
            loop.call_soon_threadsafe(event.set)

        sub = await runtime.afirst(self._children[1], ctx)
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
