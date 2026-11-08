"""Stream flow: drain-then-follow over ordered collections.

The ``cat file; tail -f`` of Nu. One declaration that handles batch
catch-up, live follow, and the transition between them.
"""

from __future__ import annotations

from contextlib import aclosing
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any
from nu.domains.shape.interactions import AdvanceCursor
from nu.lang import StreamQuery

from .._body import async_only
from ..level._wakes import Wakes, read_schedule, schedule_terms
from ..sources.on import OnChildrenChange


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Iterable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime

__all__ = ["Stream"]


def _reads(source: object, cursor: object) -> tuple[Nu, Nu]:
    """The two reads of ``source``: the item past ``cursor``, and the watch.

    A ref whose fabric needs each read bracketed supplies both itself through
    ``_stream_reads(cursor)``, so every drain step sees the source as it
    stands then (kv refs give each read a snapshot of its own).
    """
    own = getattr(type(source), "_stream_reads", None)
    if own is not None:
        return own(source, cursor)
    return AdvanceCursor(source, cursor), OnChildrenChange(source)


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
        after: re-drain offsets in seconds after subscribing, for the window
            a fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one. Empty by default: re-drains
            are opt in (``after=nu.RECHECK_AFTER``).
        every: seconds between standing re-drains once ``after`` is spent.
            ``None`` (the default) turns them off; opt in with
            ``every=nu.RECHECK_EVERY``. A term yielding a float or None, or a
            literal one.

    Notes:
        - Children are ``[advance, change, body, key, log_key, after,
          every]``: ``advance`` is an ``AdvanceCursor`` over ``source``,
          ``change`` an ``OnChildrenChange`` subscription on ``source``. A
          source ref may supply both itself (``_stream_reads``): a kv ref
          wraps each in a snapshot of its own, so the stream needs no
          bracket around it and an outer one does not freeze it.
        - Subscribes first, then drains: walks ``advance`` to exhaustion,
          running ``body`` per item. An item appended at any point after the
          subscribe is either in that first drain or wakes a later one, so
          none falls between catching up and following.
        - Drains are driven like a level flow's passes: once right after
          subscribing, again on each change notification, and on the
          ``after`` / ``every`` re-checks, so a lost notification is caught
          late rather than never. Wakes landing while a drain runs merge
          into one more drain. Re-draining from the cursor is idempotent:
          a drain that finds nothing new runs no body.
        - ``key`` is bound per item for as long as that item's ``body`` is
          drained, the same scoped binding ``Map`` / ``Filter`` give their
          loop variable. ``log_key`` is the cursor's own position, bound for
          the stream's whole drain (starting from an outer binding when there
          is one) and advanced item by item.
        - Never ends on its own; closing the stream unbinds and closes the
          subscription.
        - Async only: the sync path raises ``RuntimeError``, since following
          requires an event loop.

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
        after: Iterable[float] | object = (),
        every: float | object | None = None,
    ) -> None:
        from nu.context import Attr

        body, (key,) = bind("Stream", body, key=key)
        if key is None:
            key = "stream_key"

        advance, change = _reads(source, Attr(log_key))
        super().__init__(
            advance, change, body, key, log_key, *schedule_terms("Stream", after, every)
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("Stream")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, after, every = children[1], children[5], children[6]

        async def athunk(rt: Runtime) -> object:
            key = await children[3](rt)
            log_key = await children[4](rt)
            attrs = rt.ctx.attrs

            async def agen() -> object:
                with attrs.let(log_key, attrs.get(log_key)):
                    schedule = await read_schedule("Stream", rt, after, every)
                    async with Wakes(await change(rt), *schedule) as wakes:
                        while True:
                            await wakes.wait()
                            async with aclosing(_drain(rt, children, key, log_key)) as drained:
                                async for v in drained:
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
