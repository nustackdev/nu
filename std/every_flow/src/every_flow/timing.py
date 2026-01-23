"""Timing and rate-limiting flows.

This module provides flows for timing control:
- Delay: Pause execution for a duration
- Timeout: Execute with time limit
- Throttle: Rate-limit execution (max once per interval)
- Debounce: Wait for quiet period before executing
"""

from __future__ import annotations

import asyncio
import time

import attrs

from every import Flow, Runtime, Term, is_sentinel


__all__ = [
    "Debounce",
    "Delay",
    "Throttle",
    "Timeout",
]


# TODO: update once reactive morphisms are there
class FlowTimeoutError(Exception):
    pass


@attrs.define
class _Delay[RuntimeT: Runtime](Flow[RuntimeT]):
    """Pause execution for specified duration."""

    delay: Term | float = attrs.field(default=0.0)
    child: Term | Flow | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute delay."""
        if isinstance(self.delay, Term):
            delay = runtime.terms.execute_term(self.delay)
            if is_sentinel(delay):
                delay = 0.0
            elif not isinstance(delay, (int, float)):
                raise ValueError("Delay should be a number")
        else:
            delay = self.delay

        await asyncio.sleep(delay)

        if self.child is not None:
            await self.execute_child(self.child, 0, runtime)


@attrs.define
class _Timeout[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child with timeout.

    If the child doesn't complete within the timeout period,
    it is cancelled and an optional on_timeout handler is executed.
    """

    timeout: Term | float = attrs.field(default=0.0)
    child: Term | Flow | None = attrs.field(default=None)
    on_timeout: Term | Flow | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child with timeout."""
        if self.child is None:
            raise ValueError("Child flow should not be None")

        if isinstance(self.timeout, Term):
            timeout = runtime.terms.execute_term(self.timeout)
            if is_sentinel(timeout):
                raise TypeError(f"timeout should be either int or float, {timeout} given")
            elif not isinstance(timeout, (int, float)):
                raise ValueError("Timeout should be a number")
        else:
            timeout = self.timeout

        try:
            await asyncio.wait_for(self.execute_child(self.child, 0, runtime), timeout=timeout)
        except TimeoutError:
            runtime.cancellation.cancel(runtime.path)

            if self.on_timeout is not None:
                await self.execute_child(self.on_timeout, "on_timeout", runtime)
            _ = FlowTimeoutError
            # TODO: tbd if should raise error or no
            # else:
            #     raise FlowTimeoutError(
            #         f"Flow timed out after {timeout}s",
            #         path=runtime.path,
            #         timeout_seconds=timeout,
            #     ) from None


@attrs.define
class _Throttle[RuntimeT: Runtime](Flow[RuntimeT]):
    """Rate-limit child execution to at most once per interval.

    In a loop, ensures child executes at most once per interval.
    Tracks last execution time via runtime.attributes.

    Flow Building Pattern:
        Throttle is designed for use inside loops (While, Forever).
        It ensures rate-limiting by tracking last execution time.
        The actual execution is NOT skipped - instead, Throttle waits
        until the interval has passed before executing.

    Use cases:
        - API rate limiting
        - UI update throttling
        - Resource-intensive operation limiting
    """

    interval: Term | float = attrs.field(default=1.0)
    child: Term | Flow | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child with rate limiting."""
        if self.child is None:
            raise ValueError("Child flow should not be None")

        if isinstance(self.interval, Term):
            interval = runtime.terms.execute_term(self.interval)
            if not isinstance(interval, (int, float)):
                raise ValueError("Interval should be a number")
        else:
            interval = self.interval

        # Get last execution time from attributes
        last_exec = runtime.attributes.get(runtime.path, "_throttle_last")

        current_time = time.monotonic()

        if last_exec is not None and isinstance(last_exec, (int, float)):
            elapsed = current_time - last_exec
            if elapsed < interval:
                # Wait for remaining interval
                await asyncio.sleep(interval - elapsed)
                current_time = time.monotonic()

        # Update last execution time
        runtime.attributes.set(runtime.path, "_throttle_last", current_time, step_name=self.name)

        # Execute child
        await self.execute_child(self.child, 0, runtime)


@attrs.define
class _Debounce[RuntimeT: Runtime](Flow[RuntimeT]):
    """Wait for quiet period before executing child.

    Waits until no new triggers occur for the specified delay,
    then executes the child. Useful for handling bursts of events.

    Flow Building Pattern:
        Debounce is designed for reactive patterns where you want
        to wait for activity to settle before responding.
        Unlike Throttle (which executes periodically), Debounce
        waits for a quiet period.

    Use cases:
        - Search-as-you-type (wait for user to stop typing)
        - Window resize handling (wait for resize to complete)
        - Batch processing (collect events, then process)
    """

    delay: Term | float = attrs.field(default=0.5)
    child: Term | Flow | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child after quiet period."""
        if self.child is None:
            raise ValueError("Child flow should not be None")

        if isinstance(self.delay, Term):
            delay = runtime.terms.execute_term(self.delay)
            if not isinstance(delay, (int, float)):
                raise ValueError("Delay should be a number")
        else:
            delay = self.delay

        # Simply wait for the debounce period
        # In a reactive context, re-triggering would restart this flow
        await asyncio.sleep(delay)

        # Execute child after quiet period
        await self.execute_child(self.child, 0, runtime)


# =============================================================================
# Wrapper Functions
# =============================================================================


def Delay(delay: Term | float, child: Flow | Term | None = None) -> _Delay:  # noqa: N802
    """Pause execution for specified duration.

    Args:
        delay: Delay duration in seconds (Term or float)
        child: Optional child flow to execute after delay

    Returns:
        Delay flow

    Example:
        >>> Delay(1.5)
        >>> Delay(1, Print("Done"))
    """
    return _Delay(delay=delay, child=child)


def Timeout(  # noqa: N802
    timeout: Term | float,
    child: Flow | Term,
    on_timeout: Flow | Term | None = None,
) -> _Timeout:
    """Execute child with timeout.

    If child doesn't complete within timeout, it is cancelled.
    Optionally executes on_timeout handler instead of raising.

    Args:
        timeout: Timeout duration in seconds (Term or float)
        child: Child flow to execute with timeout
        on_timeout: Optional handler to execute on timeout (instead of raising)

    Returns:
        Timeout flow

    Example:
        >>> Timeout(30, FetchLargeData())
        >>> Timeout(5, SlowOperation(), on_timeout=UseDefault())
    """
    return _Timeout(timeout=timeout, child=child, on_timeout=on_timeout)


def Throttle(interval: Term | float, child: Flow | Term) -> _Throttle:  # noqa: N802
    """Rate-limit child execution to at most once per interval.

    In a loop, waits until interval has passed since last execution.

    Args:
        interval: Minimum interval between executions in seconds
        child: Child flow to rate-limit

    Returns:
        Throttle flow

    Example:
        >>> Forever(Throttle(1.0, CheckForUpdates()))  # Max once per second
    """
    return _Throttle(interval=interval, child=child)


def Debounce(delay: Term | float, child: Flow | Term) -> _Debounce:  # noqa: N802
    """Wait for quiet period before executing child.

    Waits for the specified delay, then executes child.
    Useful for waiting until activity settles.

    Args:
        delay: Quiet period to wait in seconds
        child: Child flow to execute after quiet period

    Returns:
        Debounce flow

    Example:
        >>> Debounce(0.5, ProcessSearchQuery())  # Wait for typing to stop
    """
    return _Debounce(delay=delay, child=child)
