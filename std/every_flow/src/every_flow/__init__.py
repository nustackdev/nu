"""EveryBase Flows - Common flow primitives for EveryFlow.

This module provides a rich set of flow primitives organized by category:

Control Flows (control.py):
    - Sequence, Seq: Execute children in order
    - If: Conditional execution
    - While: Loop while condition is true
    - DoWhile: Loop at least once, then check condition
    - Forever: Infinite loop (until cancelled)
    - Switch: Multi-way branching

Parallel Flows (parallel.py):
    - Parallel: Execute all children concurrently
    - Race: First to complete wins
    - All: All must succeed
    - Any: Any success is sufficient

Timing Flows (timing.py):
    - Delay: Pause execution
    - Timeout: Execute with time limit
    - Throttle: Rate-limit execution
    - Debounce: Wait for quiet period

Iteration Flows (iteration.py):
    - ForEach, ForEachSequence: Iterate over collections
    - ForRange: Iterate over numeric range

Reactive Flows (reactive.py):
    - Once: Wait for a single change, then execute child
    - OnChange: Execute child on every change (runs forever)
    - OnChangeWhile: Execute child on every change while condition is true

Error Handling (error.py):
    - TryCatch: Error recovery
    - Retry: Retry with backoff
    - Assert: Validate conditions

I/O Flows (io.py):
    - Print: Output to stdout
    - Log: Structured logging
    - Debug: Quick debug output

Profiling Flows (profiling.py):
    - Timed: Measure child execution time and store in a Ref
    - Accumulate: Accumulate total execution time across calls
    - Count: Count child executions, store in a Ref
    - Trace: Print entry/exit with timing for debugging
    - Tap: Execute a side-effect flow alongside the main child
    - Sample: Execute child only every N times

Flow Building Patterns:
    Flows are self-contained and cannot expose or pass state directly.
"""

from __future__ import annotations


__all__: list[str] = []
