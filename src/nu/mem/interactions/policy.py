"""Rate policies that keep their state in a mem ref: ``Throttle`` and ``Debounce``.

Both only mean something under repeated invocation, so both carry state from
one call to the next: the time of the last run, the run still pending. A Term
is immutable and shared, so that state cannot live on the node. It lives in a
mem ref the caller passes, which makes it explicit and scoped: it lasts as long
as the frame (or bound dict) that holds the ref, and two policies never share
it unless they are handed the same ref.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from nu.core.spans.policy import _async_backstop
from nu.engine.structure import Declared
from nu.lang import Policy
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import FloatArg, Nu
    from nu.lang.runtime import Runtime


__all__ = ["Debounce", "Throttle"]


class Throttle(Policy):
    """Drops a body run that falls inside ``interval`` of the prior run.

    Async-only. A single call always runs; the policy shows under a loop or a
    reaction, where calls come one after another.

    Args:
        interval: the minimum gap between runs, in seconds.
        body: the throttled Term.
        last: the mem ref holding the time of the last run. Unset or ``None``
            means the body has never run.

    Notes:
        - The time is ``time.monotonic()``, written before the body runs.
        - The state lasts as long as what holds ``last``: put the frame
          around the loop, not inside it.

    Yields:
        The body's value, or ``None`` when the run is dropped.

    Example:
        >>> import asyncio
        >>> pings = lambda last: nu.ForRangeDo(0, 3, nu.Throttle(60.0, nu.print("ping"), last=last))
        >>> _ = asyncio.run(nu.arun(nu.let(None, pings)))
        ping
    """

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({2}), name="mutates")

    def __init__(self, interval: FloatArg, body: Nu, *, last: Nu) -> None:
        super().__init__(body, interval, last)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_backstop("Throttle")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, interval_q, last_q = children
        last = self._children[2]

        async def athunk(rt: Runtime) -> object:
            interval = float(await interval_q(rt))
            prior = await last_q(rt)
            now = time.monotonic()
            never = prior is None or prior is EMPTY
            if not never and now - prior < interval:
                return None
            await last._awrite(rt, now, rt.program.children[nid][2])
            return await body(rt)

        return athunk


class Debounce(Policy):
    """Delays the body; a re-entry cancels the pending run and starts over.

    Async-only. Each call cancels the run still waiting and schedules a fresh
    one, so only the last call in a burst fires.

    Args:
        delay: how long to wait before running the body, in seconds.
        body: the debounced Term.
        pending: the mem ref holding the scheduled run, an ``asyncio.Task``.
            Unset or ``None`` means nothing is scheduled.

    Notes:
        - The body runs later, detached from the call that scheduled it:
          nothing observes its result through this node.
        - The state lasts as long as what holds ``pending``: put the frame
          around the loop, not inside it.

    Yields:
        ``None``, immediately. The body's own value is never seen here.

    Example:
        >>> import asyncio
        >>> saves = lambda pending: nu.ForRangeDo(0, 3, nu.Debounce(0.01, nu.print("saved"), pending=pending))
        >>> _ = asyncio.run(nu.arun(nu.let(None, saves) >> nu.Delay(0.05)))
        saved
    """

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({2}), name="mutates")

    def __init__(self, delay: FloatArg, body: Nu, *, pending: Nu) -> None:
        super().__init__(body, delay, pending)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_backstop("Debounce")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, delay_q, pending_q = children
        pending = self._children[2]

        async def athunk(rt: Runtime) -> object:
            delay = float(await delay_q(rt))
            prior = await pending_q(rt)
            if isinstance(prior, asyncio.Task) and not prior.done():
                prior.cancel()

            async def later() -> object:
                await asyncio.sleep(delay)
                return await body(rt)

            await pending._awrite(rt, asyncio.create_task(later()), rt.program.children[nid][2])
            return None

        return athunk
