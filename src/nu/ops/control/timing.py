"""Timing ops -- Timed, Delay, Timeout, Throttle, Debounce."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from nu.terms import Op


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import FloatArg, Nu, StrArg


__all__ = [
    "Debounce",
    "Delay",
    "Throttle",
    "Timed",
    "Timeout",
]


class Timed(Op):
    """Time each child and print results.

    Children: ``[label, *children]``
    """

    def __init__(self, *children: Nu, label: StrArg = "Timed") -> None:
        super().__init__(label, *children)

    async def execute(self, ctx: Context) -> None:
        label = await self.children[0].execute(ctx)
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
            await child.execute(ctx)
            elapsed = time.perf_counter() - t0
            timings.append((name, elapsed))

        total = sum(t for _, t in timings)
        print(f"[Timed:{label}]")  # noqa: T201
        for i, (name, elapsed) in enumerate(timings, 1):
            print(f"  {i}. {name:<40} {elapsed * 1000:>8.1f}ms")  # noqa: T201
        print(f"  {'total':<42} {total * 1000:>8.1f}ms")  # noqa: T201


class Delay(Op):
    """Pause execution, then optionally run a child.

    Children: ``[delay, body?]``
    """

    def __init__(self, delay: FloatArg, body: Nu | None = None) -> None:
        if body is not None:
            super().__init__(delay, body)
        else:
            super().__init__(delay)

    async def execute(self, ctx: Context) -> None:
        delay = await self.children[0].execute(ctx)
        await asyncio.sleep(delay)
        if self.child_count > 1:
            await self.children[1].execute(ctx)


class Timeout(Op):
    """Execute a child with a time limit.

    Children: ``[timeout, body, on_timeout?]``
    """

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

    async def execute(self, ctx: Context) -> None:
        timeout = await self.children[0].execute(ctx)
        body = self.children[1]
        try:
            await asyncio.wait_for(body.execute(ctx), timeout=timeout)
        except TimeoutError:
            if self._has_on_timeout:
                await self.children[2].execute(ctx)


class Throttle(Op):
    """Drop executions within interval. Execute at most once per interval.

    Children: ``[interval, body?]``

    First call always executes. Subsequent calls within the interval are skipped.
    """

    def __init__(self, interval: FloatArg, body: Nu | None = None) -> None:
        self._last_time: float = 0.0
        if body is not None:
            super().__init__(interval, body)
        else:
            super().__init__(interval)

    async def execute(self, ctx: Context) -> None:
        interval = await self.children[0].execute(ctx)
        now = time.monotonic()
        if now - self._last_time < interval:
            return  # drop
        self._last_time = now
        if self.child_count > 1:
            await self.children[1].execute(ctx)


class Debounce(Op):
    """Cancel pending, restart timer. Execute only after quiet period.

    Children: ``[delay, body?]``

    Each call cancels any pending execution and starts a new timer.
    Body executes only when the timer expires without being reset.
    """

    def __init__(self, delay: FloatArg, body: Nu | None = None) -> None:
        self._pending: asyncio.Task | None = None
        if body is not None:
            super().__init__(delay, body)
        else:
            super().__init__(delay)

    async def execute(self, ctx: Context) -> None:
        delay = await self.children[0].execute(ctx)
        if self._pending is not None and not self._pending.done():
            self._pending.cancel()
        if self.child_count > 1:
            self._pending = asyncio.create_task(self._run_after(delay, ctx))

    async def _run_after(self, delay: float, ctx: Context) -> None:
        await asyncio.sleep(delay)
        await self.children[1].execute(ctx)
