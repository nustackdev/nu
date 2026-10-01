"""Stream flow: drain-then-follow over ordered collections.

The ``cat file; tail -f`` of Nu. One declaration that handles batch
catch-up, live follow, and the transition between them.
"""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any
from nu.core.reactive import OnChildrenChange
from nu.domains.shape.interactions import AdvanceCursor
from nu.lang import StreamQuery


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from nu.lang.runtime import Runtime

__all__ = ["Stream"]


class Stream(StreamQuery):
    """Drain-then-follow over an ordered collection; cursor tracks position.

    Args:
        source: the ordered collection to stream over.
        body: the Nu run per item: a lambda over the item's cursor key, or a
            tree reading it with ``Attr(key)``.
        key: the ``ctx.attrs`` name the current item's cursor key is bound
            under, for a tree ``body`` to read. Defaults to
            ``"stream_key"``; a lambda mints its own.
        log_key: the ``ctx.attrs`` name the underlying log cursor is bound
            under.

    Notes:
        - Children are ``[advance, change, body, key, log_key]``: ``advance``
          is an ``AdvanceCursor`` over ``source``, ``change`` an
          ``OnChildrenChange`` subscription on ``source``.
        - Drains existing items first (walks ``advance`` to exhaustion,
          running ``body`` per item), then subscribes and follows new items
          as they arrive, draining again on each change notification.
        - ``key`` is bound per item for as long as that item's ``body`` is
          drained, the same scoped binding ``Map`` / ``Filter`` give their
          loop variable. ``log_key`` is the cursor's own position, bound for
          the stream's whole drain (starting from an outer binding when there
          is one) and advanced item by item.
        - Async-only: ``_compile`` raises ``NotImplementedError``, since
          following requires an event loop.

    Yields:
        The body's results, drained then followed, as an async stream.

    Example:
        A stream needs a real ordered-collection substrate to drive
        ``advance`` / ``change``, so it can't run standalone here::

            Stream(SequenceRef("items"), lambda key: nu.print(key))
    """

    def __init__(
        self,
        source: object,
        body: object,
        *,
        key: object = None,
        log_key: object = "stream_log_key",
    ) -> None:
        from nu.context import Attr

        body, (key,) = bind("Stream", body, key=key)
        if key is None:
            key = "stream_key"

        cursor_ref = Attr(log_key)
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
            attrs = rt.ctx.attrs

            async def agen() -> object:
                with attrs.let(log_key, attrs.get(log_key)):
                    async with aclosing(_drain(rt, children, key, log_key)) as drained:
                        async for v in drained:
                            yield v
                    async with aclosing(_react(rt, children, key, log_key)) as followed:
                        async for v in followed:
                            yield v

            return agen()

        return athunk


async def _drain(
    rt: Runtime,
    children: tuple[Callable, ...],
    key: str,
    log_key: str,
) -> AsyncGenerator:
    """Walk ``advance`` to exhaustion, running ``body`` per item.

    Yields:
        Each item ``body`` produces, in cursor order.
    """
    while True:
        result = await children[0](rt)
        if result is None:
            break
        log_k, actual_key = result
        rt.ctx.attrs.set(log_key, log_k)
        with rt.ctx.attrs.let(key, actual_key):
            async with aclosing(aiter_any(await children[2](rt))) as items:
                async for v in items:
                    yield v


async def _react(
    rt: Runtime,
    children: tuple[Callable, ...],
    key: str,
    log_key: str,
) -> AsyncGenerator:
    """Subscribe to ``change`` and re-drain on every notification.

    Notes:
        - Unbinds and closes the subscription on exit, including on
          cancellation, via ``finally``.

    Yields:
        Each item a subsequent drain produces, forever.
    """
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
            async with aclosing(_drain(rt, children, key, log_key)) as drained:
                async for v in drained:
                    yield v
    finally:
        sub.unbind(on_change)
        sub.close()
