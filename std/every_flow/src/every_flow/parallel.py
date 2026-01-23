"""Parallel execution flows.

This module provides flows for concurrent execution patterns:
- Parallel: Execute all children concurrently, wait for all
- Race: Execute children concurrently, return on first completion
- All: Execute children concurrently, succeed only if all succeed
- Any: Execute children concurrently, succeed if any succeeds
"""

from __future__ import annotations

import asyncio
from enum import Enum

import attrs

from every import Flow, Runtime, Term


__all__ = [
    "All",
    "Any",
    "Parallel",
    "Race",
]


class CompletionMode(Enum):
    """How to handle parallel completion."""

    ALL = "all"  # Wait for all, fail if any fails
    ANY = "any"  # Return on first success
    RACE = "race"  # Return on first completion (success or failure)


@attrs.define
class _Parallel[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute children in parallel asynchronously.

    All children run concurrently using asyncio.gather.
    Waits for all children to complete.
    """

    children: list[Flow | Term] = attrs.field(factory=list)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute children concurrently."""
        await asyncio.gather(
            *[
                self.execute_child(child, index, runtime)
                for index, child in enumerate(self.children)
            ]
        )


@attrs.define
class _Race[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute children concurrently, complete on first finish.

    Returns as soon as any child completes (success or failure).
    Cancels remaining children.

    Useful for:
    - Failover patterns (try multiple sources)
    - Latency optimization (fastest wins)
    - Timeout alternatives (race against delay)
    """

    children: list[Flow | Term] = attrs.field(factory=list)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute children, return on first completion."""
        if not self.children:
            return

        tasks = [
            asyncio.create_task(self.execute_child(child, index, runtime))
            for index, child in enumerate(self.children)
        ]

        try:
            # Wait for first completion
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            # Wait for cancellations to complete
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

            # Propagate any exception from the completed task
            for task in done:
                task.result()  # Raises if task raised

        except asyncio.CancelledError:
            # Cancel all tasks on external cancellation
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


@attrs.define
class _All[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute children concurrently, succeed only if all succeed.

    All children run in parallel. If any child fails, the remaining
    children are cancelled and the error propagates.

    Useful for:
    - Parallel initialization (all must succeed)
    - Batch operations (all or nothing)
    - Coordinated multi-resource acquisition
    """

    children: list[Flow | Term] = attrs.field(factory=list)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute all children, fail if any fails."""
        if not self.children:
            return

        tasks = [
            asyncio.create_task(self.execute_child(child, index, runtime))
            for index, child in enumerate(self.children)
        ]

        try:
            # Wait for all, but fail fast on first exception
            await asyncio.gather(*tasks)
        except Exception:
            # Cancel remaining on failure
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


@attrs.define
class _Any[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute children concurrently, succeed if any succeeds.

    All children run in parallel. Returns on first successful completion.
    If all children fail, raises the last error.

    Useful for:
    - Fallback patterns (try multiple approaches)
    - Redundant operations (any success is sufficient)
    - Best-effort retrieval from multiple sources
    """

    children: list[Flow | Term] = attrs.field(factory=list)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute children, succeed on first success."""
        if not self.children:
            return

        tasks = [
            asyncio.create_task(self.execute_child(child, index, runtime))
            for index, child in enumerate(self.children)
        ]

        last_error: Exception | None = None
        pending = set(tasks)

        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

                for task in done:
                    try:
                        task.result()
                        # Success! Cancel remaining and return
                        for p in pending:
                            p.cancel()
                        if pending:
                            await asyncio.gather(*pending, return_exceptions=True)
                        return
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        last_error = e
                        # Continue waiting for others

            # All failed
            if last_error is not None:
                raise last_error

        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


# =============================================================================
# Wrapper Functions
# =============================================================================


def Parallel(*children: Flow | Term) -> _Parallel:  # noqa: N802
    """Execute children in parallel asynchronously.

    All children run concurrently using asyncio.gather.
    Waits for all children to complete.

    Args:
        *children: Child flows to execute in parallel

    Returns:
        Parallel flow

    Example:
        >>> Parallel(FetchUser(), FetchPosts(), FetchComments())
    """
    return _Parallel(children=list(children))


def Race(*children: Flow | Term) -> _Race:  # noqa: N802
    """Execute children concurrently, complete on first finish.

    Returns as soon as any child completes. Cancels remaining children.
    Useful for failover patterns and latency optimization.

    Args:
        *children: Child flows to race

    Returns:
        Race flow

    Example:
        >>> Race(
        ...     FetchFromPrimary(),
        ...     FetchFromFallback(),
        ... )
    """
    return _Race(children=list(children))


def All(*children: Flow | Term) -> _All:  # noqa: N802
    """Execute children concurrently, succeed only if all succeed.

    All children run in parallel. If any fails, remaining are cancelled.

    Args:
        *children: Child flows that must all succeed

    Returns:
        All flow

    Example:
        >>> All(
        ...     InitDatabase(),
        ...     InitCache(),
        ...     InitMessageQueue(),
        ... )
    """
    return _All(children=list(children))


def Any(*children: Flow | Term) -> _Any:  # noqa: N802
    """Execute children concurrently, succeed if any succeeds.

    Returns on first successful completion. If all fail, raises last error.

    Args:
        *children: Child flows where any success is sufficient

    Returns:
        Any flow

    Example:
        >>> Any(
        ...     FetchFromCache(),
        ...     FetchFromDatabase(),
        ...     FetchFromAPI(),
        ... )
    """
    return _Any(children=list(children))
