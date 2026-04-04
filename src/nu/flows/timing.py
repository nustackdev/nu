"""Timing flows -- Delay, Timeout, Throttle, Debounce."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from .base import Flow

from nu.utils import ensure_nu


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu, FloatArg, StrArg


__all__ = [
    "Debounce",
    "Delay",
    "Throttle",
    "Timed",
    "Timeout",
]


class Timed(Flow):
    """Time each child and print results.

    Runs children sequentially, measures wall time for each using perf_counter,
    then prints a summary with per-child timings.

    Children layout: ``[label, *children]``

    Example::

        Timed(
            store_data,
            read_back,
            label="write cycle",
        )
        # Output:
        # [Timed:write cycle]
        #   1. store_data            12.3ms
        #   2. read_back              4.1ms
        #   total                    16.4ms
    """

    def __init__(self, *children: Nu, label: StrArg = "Timed") -> None:
        """Initialize timed flow.

        Args:
            children: Nus to time sequentially.
            label: Display label for the timing summary.
        """
        super().__init__(ensure_nu(label), *children)

    async def execute(self, ctx: Context) -> None:
        """Run each child, measure time, print summary."""
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


class Delay(Flow):
    """Pause execution for a specified duration, then optionally run a child.

    Children layout: [delay, body?]

    The delay parameter is auto-wrapped via ``ensure_nu`` if a literal is passed,
    making it a child node visible to tree transforms.

    Example::

        Delay(1.5)
        Delay(1.0, some_action)
    """

    def __init__(
        self,
        delay: FloatArg,
        body: Nu | None = None,
    ) -> None:
        """Initialize delay flow.

        Args:
            delay: Duration to sleep in seconds. Nu or literal.
            body: Optional executable to run after the delay.
        """
        if body is not None:
            super().__init__(ensure_nu(delay), body)
        else:
            super().__init__(ensure_nu(delay))

    async def execute(self, ctx: Context) -> None:
        """Sleep for the resolved delay, then execute body if present."""
        delay = await self.children[0].execute(ctx)
        await asyncio.sleep(delay)
        if self.child_count > 1:
            await self.children[1].execute(ctx)


class Timeout(Flow):
    """Execute a child with a time limit.

    Children layout: [timeout, body, on_timeout?]

    If the body does not complete within the timeout period it is
    cancelled.  An optional on_timeout handler runs when the timeout
    fires instead of silently swallowing the error.

    Example::

        Timeout(30, fetch_large_data)
        Timeout(5, slow_operation, on_timeout=use_default)
    """

    def __init__(
        self,
        timeout: FloatArg,
        body: Nu,
        on_timeout: Nu | None = None,
    ) -> None:
        """Initialize timeout flow.

        Args:
            timeout: Maximum duration in seconds. Nu or literal.
            body: Nu to run under the time limit.
            on_timeout: Optional executable invoked when the timeout fires.
        """
        self._has_on_timeout = on_timeout is not None
        children: list[Nu] = [ensure_nu(timeout), body]
        if on_timeout is not None:
            children.append(on_timeout)
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Run body under the resolved timeout, invoking on_timeout if exceeded."""
        timeout = await self.children[0].execute(ctx)
        body = self.children[1]
        try:
            await asyncio.wait_for(body.execute(ctx), timeout=timeout)
        except TimeoutError:
            if self._has_on_timeout:
                await self.children[2].execute(ctx)


class Throttle(Flow):
    """Rate-limit execution to at most once per interval.

    Children layout: [interval, body?]

    When called more frequently than the interval allows, Throttle
    sleeps until the interval has elapsed since the last execution
    before proceeding.  Useful inside loops for API rate-limiting
    or UI update throttling.

    Example::

        Throttle(1.0, check_for_updates)
    """

    def __init__(
        self,
        interval: FloatArg,
        body: Nu | None = None,
    ) -> None:
        """Initialize throttle flow.

        Args:
            interval: Minimum interval between executions in seconds. Nu or literal.
            body: Optional executable to run after the throttle gate.
        """
        self._last_time: float = 0.0
        if body is not None:
            super().__init__(ensure_nu(interval), body)
        else:
            super().__init__(ensure_nu(interval))

    async def execute(self, ctx: Context) -> None:
        """Wait until the interval has passed, then execute body if present."""
        interval = await self.children[0].execute(ctx)
        now = time.monotonic()
        elapsed = now - self._last_time
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        self._last_time = time.monotonic()
        if self.child_count > 1:
            await self.children[1].execute(ctx)


class Debounce(Flow):
    """Wait for a quiet period before executing.

    Children layout: [delay, body?]

    Sleeps for the specified delay.  In a reactive context where
    re-triggering restarts the flow, this ensures the body only
    runs once activity has settled.

    Example::

        Debounce(0.5, process_search_query)
    """

    def __init__(
        self,
        delay: FloatArg,
        body: Nu | None = None,
    ) -> None:
        """Initialize debounce flow.

        Args:
            delay: Quiet period to wait in seconds. Nu or literal.
            body: Optional executable to run after the quiet period.
        """
        if body is not None:
            super().__init__(ensure_nu(delay), body)
        else:
            super().__init__(ensure_nu(delay))

    async def execute(self, ctx: Context) -> None:
        """Sleep for the resolved delay, then execute body if present."""
        delay = await self.children[0].execute(ctx)
        await asyncio.sleep(delay)
        if self.child_count > 1:
            await self.children[1].execute(ctx)
