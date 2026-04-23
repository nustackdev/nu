"""Timing ops -- Timed, Timeout, Throttle, Debounce.

For sleep primitives, see ``nu.stdlib.asyncio.AsyncSleep`` (ASYNC) and
``nu.stdlib.time.TimeSleep`` (SYNC). Core ships no ``Delay``: asyncio.sleep
and time.sleep are different primitives under different modes, and the
wrapper belongs in stdlib.
"""

from __future__ import annotations

import asyncio
import time
from contextlib import aclosing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Flow, Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu.context import Context
    from nu.terms import FloatArg, Nu, StrArg


__all__ = [
    "Debounce",
    "Throttle",
    "Timed",
    "Timeout",
]


class Timed(Flow):
    """Time each child and print results.

    Children: ``[label, *children]``
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, *children: Nu, label: StrArg = "Timed") -> None:
        super().__init__(label, *children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        label = await self.children[0].afirst(ctx)
        timings: list[tuple[str, float]] = []
        for child in self.children[1:]:
            name = child.__class__.__name__
            if hasattr(child, "_label"):
                name = child._label
            elif hasattr(child, "__repr__"):
                r = repr(child)
                if len(r) < 60:
                    name = r
            t0 = time.perf_counter()
            await child.aexecute(ctx)
            elapsed = time.perf_counter() - t0
            timings.append((name, elapsed))

        total = sum(t for _, t in timings)
        print(f"[Timed:{label}]")  # noqa: T201
        for i, (name, elapsed) in enumerate(timings, 1):
            print(f"  {i}. {name:<40} {elapsed * 1000:>8.1f}ms")  # noqa: T201
        print(f"  {'total':<42} {total * 1000:>8.1f}ms")  # noqa: T201


class Timeout(Flow):
    """Execute a child with a time limit.

    Children: ``[timeout, body, on_timeout?]``
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(
        self,
        timeout: FloatArg,
        body: Nu,
        on_timeout: Nu | None = None,
    ) -> None:
        self._has_on_timeout = on_timeout is not None
        children: list = [timeout, body]
        if on_timeout is not None:
            children.append(on_timeout)
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        timeout = await self.children[0].afirst(ctx)
        body = self.children[1]
        try:
            await asyncio.wait_for(body.aexecute(ctx), timeout=timeout)
        except TimeoutError:
            if self._has_on_timeout:
                await self.children[2].aexecute(ctx)


class Throttle(Flow):
    """Drop executions within interval. Execute at most once per interval.

    Children: ``[interval, body?]``

    First call always executes. Subsequent calls within the interval are skipped.
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, interval: FloatArg, body: Nu | None = None) -> None:
        self._last_time: float = 0.0
        if body is not None:
            super().__init__(interval, body)
        else:
            super().__init__(interval)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        interval = await self.children[0].afirst(ctx)
        now = time.monotonic()
        if now - self._last_time < interval:
            return  # drop
        self._last_time = now
        if self._child_count > 1:
            async with aclosing(self.children[1].aopen(ctx)) as gen:
                async for v in gen:
                    yield v


class Debounce(Flow):
    """Cancel pending, restart timer. Execute only after quiet period.

    Children: ``[delay, body?]``

    Each call cancels any pending execution and starts a new timer.
    Body executes only when the timer expires without being reset.
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, delay: FloatArg, body: Nu | None = None) -> None:
        self._pending: asyncio.Task | None = None
        if body is not None:
            super().__init__(delay, body)
        else:
            super().__init__(delay)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        delay = await self.children[0].afirst(ctx)
        if self._pending is not None and not self._pending.done():
            self._pending.cancel()
        if self._child_count > 1:
            self._pending = asyncio.create_task(self._run_after(delay, ctx))

    async def _run_after(self, delay: float, ctx: Context) -> None:
        await asyncio.sleep(delay)
        await self.children[1].aexecute(ctx)
