"""Profiling and observability flows.

This module provides flows for profiling, debugging, and observability:
- Timed: Measure child execution time and store in a Ref
- Accumulate: Accumulate total execution time across multiple calls
- Count: Count child executions, store in a Ref
- Trace: Print entry/exit with timing for debugging
- Tap: Execute a side-effect flow alongside the main child
- Sample: Execute child only every N times (for profiling workloads)
"""

from __future__ import annotations

import time

import attrs

from everyabc import Flow, Ref, Runtime, Term, is_sentinel


__all__ = [
    "Accumulate",
    "Count",
    "Sample",
    "Tap",
    "Timed",
    "Trace",
]


@attrs.define
class _Timed[RuntimeT: Runtime](Flow[RuntimeT]):
    """Measure child execution time and store in a Ref.

    Executes the child flow and records how long it took.
    The elapsed time (in seconds as float) is stored in the provided ref.

    Flow Building Pattern:
        Use Timed to profile specific flows and store timing data
        for later analysis or display.

    Use cases:
        - Profile slow operations
        - Track performance metrics
        - Debug timing issues
    """

    child: Flow | Term = attrs.field()
    elapsed_ref: Ref = attrs.field()

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child and measure time."""
        start = time.perf_counter()
        try:
            await self.execute_child(self.child, 0, runtime)
        finally:
            elapsed = time.perf_counter() - start
            runtime.terms.execute_term(self.elapsed_ref.set(elapsed))


@attrs.define
class _Accumulate[RuntimeT: Runtime](Flow[RuntimeT]):
    """Accumulate total execution time across multiple calls.

    Unlike Timed which stores each measurement, Accumulate adds to
    an existing value. Useful for tracking total time spent in a flow
    across loop iterations.

    Flow Building Pattern:
        Use inside loops to track cumulative time. Initialize the
        ref to 0.0 before the loop.

    Use cases:
        - Total time in a hot path across iterations
        - Cumulative profiling data
        - Performance budgeting
    """

    child: Flow | Term = attrs.field()
    total_ref: Ref = attrs.field()

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child and accumulate time."""
        # Get current accumulated value
        current = 0.0
        result = runtime.terms.execute_term(self.total_ref.get())
        if not is_sentinel(result) and isinstance(result, (int, float)):
            current = float(result)

        start = time.perf_counter()
        try:
            await self.execute_child(self.child, 0, runtime)
        finally:
            elapsed = time.perf_counter() - start
            runtime.terms.execute_term(self.total_ref.set(current + elapsed))


@attrs.define
class _Count[RuntimeT: Runtime](Flow[RuntimeT]):
    """Count child executions and store in a Ref.

    Increments a counter each time the child executes.
    Useful for tracking how many times a flow runs.

    Flow Building Pattern:
        Use to track execution frequency. Initialize the ref to 0
        before starting. Works well with loops and reactive flows.

    Use cases:
        - Count loop iterations
        - Track event occurrences
        - Debug execution paths
    """

    child: Flow | Term = attrs.field()
    count_ref: Ref = attrs.field()

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child and increment count."""
        # Get current count
        current = 0
        result = runtime.terms.execute_term(self.count_ref.get())
        if not is_sentinel(result) and isinstance(result, int):
            current = result

        # Increment count before execution
        runtime.terms.execute_term(self.count_ref.set(current + 1))

        await self.execute_child(self.child, 0, runtime)


@attrs.define
class _Trace[RuntimeT: Runtime](Flow[RuntimeT]):
    """Print entry/exit with timing for debugging.

    Prints a message on entry and exit, along with execution time.
    Useful for quick debugging of flow execution order and timing.

    Flow Building Pattern:
        Wrap any flow with Trace to see when it starts/ends.
        Uses print() for immediate output (bypasses logging).

    Use cases:
        - Debug flow execution order
        - Quick timing checks
        - Understand control flow
    """

    child: Flow | Term = attrs.field()
    label: str = attrs.field(default="")
    prefix: str = attrs.field(default="[TRACE]")

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child with trace output."""
        name = self.label or str(runtime.path)
        print(f"{self.prefix} ENTER {name}")  # noqa: T201

        start = time.perf_counter()
        try:
            await self.execute_child(self.child, 0, runtime)
            elapsed = time.perf_counter() - start
            print(f"{self.prefix} EXIT  {name} ({elapsed:.4f}s)")  # noqa: T201
        except Exception as e:
            elapsed = time.perf_counter() - start
            print(f"{self.prefix} ERROR {name} ({elapsed:.4f}s): {type(e).__name__}: {e}")  # noqa: T201
            raise


@attrs.define
class _Tap[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute a side-effect flow alongside the main child.

    Runs the tap flow after the main child completes.
    The tap flow is for side effects (logging, metrics) and doesn't
    affect the main flow's behavior.

    Flow Building Pattern:
        Use Tap to inject observability without modifying the child.
        The tap flow receives the same runtime context.

    Use cases:
        - Add logging without modifying flows
        - Inject metrics collection
        - Debug at specific points
    """

    child: Flow | Term = attrs.field()
    tap: Flow | Term = attrs.field()

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child, then tap."""
        await self.execute_child(self.child, 0, runtime)
        await self.execute_child(self.tap, "tap", runtime)


@attrs.define
class _Sample[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child only every N times.

    Useful for profiling high-frequency operations without
    the overhead of measuring every single execution.

    Flow Building Pattern:
        Sample tracks its own counter via runtime.attributes.
        Every Nth call, it executes the child.

    Use cases:
        - Profile hot loops without full overhead
        - Periodic logging in tight loops
        - Rate-limited debugging
    """

    every_n: Term | int = attrs.field()
    child: Flow | Term = attrs.field()
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child every N times."""
        if isinstance(self.every_n, Term):
            every_n = runtime.terms.execute_term(self.every_n)
            if not isinstance(every_n, int) or every_n <= 0:
                raise ValueError("every_n must be a positive integer")
        else:
            every_n = self.every_n

        # Get current sample counter
        sample_count = runtime.attributes.get(runtime.path, "_sample_count")
        if sample_count is None or not isinstance(sample_count, int):
            sample_count = 0

        sample_count += 1
        runtime.attributes.set(runtime.path, "_sample_count", sample_count, step_name=self.name)

        if sample_count >= every_n:
            # Reset counter and execute
            runtime.attributes.set(runtime.path, "_sample_count", 0, step_name=self.name)
            await self.execute_child(self.child, 0, runtime)


# =============================================================================
# Wrapper Functions
# =============================================================================


def Timed(child: Flow | Term, elapsed_ref: Ref) -> _Timed:  # noqa: N802
    """Measure child execution time and store in a Ref.

    Executes the child and stores elapsed time (seconds as float)
    in the provided ref.

    Args:
        child: Child flow to time
        elapsed_ref: FloatRef to store elapsed time (e.g., Metrics.duration)

    Returns:
        Timed flow

    Example:
        >>> Timed(SlowOperation(), Metrics.last_duration)
        >>> Timed(ProcessBatch(), Stats.processing_time)
    """
    return _Timed(child=child, elapsed_ref=elapsed_ref)


def Accumulate(child: Flow | Term, total_ref: Ref) -> _Accumulate:  # noqa: N802
    """Accumulate total execution time across multiple calls.

    Adds each execution's time to the current value in the ref.
    Useful for tracking total time in loops.

    Args:
        child: Child flow to time
        total_ref: FloatRef for storing accumulated time

    Returns:
        Accumulate flow

    Example:
        >>> # In a loop - tracks total time across iterations
        >>> Seq(
        ...     Metrics.total_time.set(0.0),
        ...     ForRange(0, 100, Accumulate(ProcessItem(), Metrics.total_time)),
        ... )
    """
    return _Accumulate(child=child, total_ref=total_ref)


def Count(child: Flow | Term, count_ref: Ref) -> _Count:  # noqa: N802
    """Count child executions and store in a Ref.

    Increments the counter each time child executes.

    Args:
        child: Child flow to count
        count_ref: IntRef for storing count

    Returns:
        Count flow

    Example:
        >>> Seq(
        ...     Metrics.iterations.set(0),
        ...     While(has_more.get(), Count(ProcessNext(), Metrics.iterations)),
        ... )
    """
    return _Count(child=child, count_ref=count_ref)


def Trace(  # noqa: N802
    child: Flow | Term,
    label: str = "",
    prefix: str = "[TRACE]",
) -> _Trace:
    """Print entry/exit with timing for debugging.

    Prints when child starts, completes, and how long it took.

    Args:
        child: Child flow to trace
        label: Label for trace output (defaults to flow path)
        prefix: Prefix for trace lines (default: "[TRACE]")

    Returns:
        Trace flow

    Example:
        >>> Trace(SlowOperation(), label="slow-op")
        # Output:
        # [TRACE] ENTER slow-op
        # [TRACE] EXIT  slow-op (1.2345s)
    """
    return _Trace(child=child, label=label, prefix=prefix)


def Tap(child: Flow | Term, tap: Flow | Term) -> _Tap:  # noqa: N802
    """Execute a side-effect flow alongside the main child.

    Runs the tap flow after child completes. Use for injecting
    logging or metrics without modifying the child flow.

    Args:
        child: Main child flow to execute
        tap: Side-effect flow to run after child

    Returns:
        Tap flow

    Example:
        >>> Tap(
        ...     ProcessData(),
        ...     Debug(current_count.get(), labels=["count"]),
        ... )
        >>> Tap(
        ...     FetchBatch(),
        ...     Log("Batch fetched", level="debug"),
        ... )
    """
    return _Tap(child=child, tap=tap)


def Sample(every_n: Term | int, child: Flow | Term) -> _Sample:  # noqa: N802
    """Execute child only every N times.

    Useful for profiling without full overhead.

    Args:
        every_n: Execute child every N calls
        child: Child flow to sample

    Returns:
        Sample flow

    Example:
        >>> # Log every 100th iteration
        >>> Forever(
        ...     Seq(
        ...         ProcessItem(),
        ...         Sample(100, Print("Still running...")),
        ...     )
        ... )
    """
    return _Sample(every_n=every_n, child=child)
