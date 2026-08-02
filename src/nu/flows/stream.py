"""Stream flow: drain-then-follow over ordered collections.

The ``cat file; tail -f`` of Nu. One declaration that handles batch
catch-up, live follow, and the transition between them.

Stream is ``StreamQuery``: it observes an ordered collection via a cursor and
a reactive subscription, yielding body results. The cursor writes to
``ctx.attrs[key]`` are untracked bookkeeping side-channels (same allowance as
Map/Filter's loop-var), not fabric writes.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any
from nu.core.reactive import OnChildrenChange
from nu.domains.shape.interactions import AdvanceCursor
from nu.lang import StreamQuery
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Stream"]


class Stream(StreamQuery):
    """Drain-then-follow over an ordered collection; cursor tracks position.

    Children: [advance, change, body, key, log_key].
    Iterates existing items (drain), then subscribes and follows new items
    (react).
    """

    def __init__(
        self,
        source: object,
        body: object,
        *,
        key: object = "stream_key",
        log_key: object = "stream_log_key",
    ) -> None:
        from nu.context import AttrRef

        cursor_ref = AttrRef(log_key)
        advance = AdvanceCursor(source, cursor_ref)
        change = OnChildrenChange(source)
        super().__init__(advance, change, body, key, log_key)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        msg = "Stream requires async runtime"
        raise NotImplementedError(msg)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            key = await children[3](rt)
            log_key = await children[4](rt)

            if log_key not in rt.ctx.attrs:
                rt.ctx.attrs[log_key] = EMPTY
            if key not in rt.ctx.attrs:
                rt.ctx.attrs[key] = EMPTY

            async def agen() -> object:
                async for v in _drain(rt, children, key, log_key):
                    yield v
                async for v in _react(rt, children, key, log_key):
                    yield v

            return agen()

        return athunk


async def _drain(
    rt: Runtime,
    children: tuple[Callable, ...],
    key: str,
    log_key: str,
) -> object:
    """Drain existing items from source via the advance cursor."""
    while True:
        result = await children[0](rt)
        if result is None:
            break
        log_k, actual_key = result
        rt.ctx.attrs[key] = actual_key
        rt.ctx.attrs[log_key] = log_k
        async for v in aiter_any(await children[2](rt)):
            yield v


async def _react(
    rt: Runtime,
    children: tuple[Callable, ...],
    key: str,
    log_key: str,
) -> object:
    """Follow new items via reactive subscription."""
    loop = asyncio.get_running_loop()
    event = asyncio.Event()

    def on_change(_k: object) -> None:
        loop.call_soon_threadsafe(event.set)

    sub = await children[1](rt)
    sub.bind(on_change)
    try:
        while True:
            await event.wait()
            event.clear()
            async for v in _drain(rt, children, key, log_key):
                yield v
    finally:
        sub.unbind(on_change)
        sub.close()
