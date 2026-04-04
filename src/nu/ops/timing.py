"""Timing ops -- Timed, Delay, Timeout, Throttle, Debounce."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from nu.terms.op import Calculation, Command


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


class Timed(Command):
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


class Delay(Command):
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


class Timeout(Calculation):
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


class Throttle(Command):
    """Rate-limit execution to at most once per interval.

    Children: ``[interval, body?]``
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
        elapsed = now - self._last_time
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        self._last_time = time.monotonic()
        if self.child_count > 1:
            await self.children[1].execute(ctx)


class Debounce(Command):
    """Wait for a quiet period before executing.

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
