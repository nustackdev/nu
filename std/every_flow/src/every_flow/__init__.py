"""Flows - Common flow primitives.

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
    State is communicated via runtime.attributes:

    1. Parent flows set attributes for child access:
       >>> with runtime.storage.transaction() as tx:
       ...     runtime.attributes.set(runtime.path, "index", i, storage_context=tx)

    2. Child flows read attributes:
       >>> with runtime.storage.snapshot() as snap:
       ...     index = runtime.attributes.get(runtime.path, "index", storage_context=snap)

    Common attributes by flow:
    - ForEach/ForRange: "index" - current iteration index
    - Once/OnChange/OnChangeWhile: "changed_key" - the key that changed
    - Switch: "case" - matched case value
    - TryCatch: "error", "error_type" - caught exception info
    - Retry: "attempt" - current attempt number
"""

from __future__ import annotations

# Assertion
from .asserts import (
    AssertEmpty,
    AssertEquals,
    AssertExists,
    AssertGreaterOrEqual,
    AssertGreaterThan,
    AssertLessOrEqual,
    AssertLessThan,
    AssertMissing,
    AssertNotEmpty,
    AssertNotEquals,
    SkipIfEmpty,
    SkipIfExists,
    SkipIfMissing,
    SkipIfNotEmpty,
)

# Attributes
from .attributes import (
    SetAttr,
)

# Control flows
from .control import (
    DoWhile,
    Forever,
    If,
    Seq,
    Sequence,
    Switch,
    While,
)

# Error handling flows
from .error import (
    Assert,
    Retry,
    TryCatch,
)

# I/O flows
from .io import (
    Debug,
    Log,
    Print,
)

# Iteration flows
from .iteration import (
    ForEach,
    ForEachParallel,
    ForRange,
)

# Parallel flows
from .parallel import (
    All,
    Any,
    Parallel,
    Race,
)

# Profiling flows
from .profiling import (
    Accumulate,
    Count,
    Sample,
    Tap,
    Timed,
    Trace,
)

# Reactive flows
from .reactive import (
    React,
    ReactForever,
    ReactWhile,
)

# Timing flows
from .timing import (
    Debounce,
    Delay,
    Throttle,
    Timeout,
)


__all__ = [  # noqa: RUF022
    # Control flows
    "Sequence",
    "Seq",
    "If",
    "While",
    "DoWhile",
    "Forever",
    "Switch",
    # Parallel flows
    "Parallel",
    "Race",
    "All",
    "Any",
    # Timing flows
    "Delay",
    "Timeout",
    "Throttle",
    "Debounce",
    # Iteration flows
    "ForEach",
    "ForRange",
    "ForEachParallel",
    # Reactive flows
    "React",
    "ReactForever",
    "ReactWhile",
    # Error handling
    "TryCatch",
    "Retry",
    "Assert",
    # Assertion
    "AssertEmpty",
    "AssertNotEmpty",
    "AssertExists",
    "AssertMissing",
    "AssertEquals",
    "AssertNotEquals",
    "AssertGreaterThan",
    "AssertLessThan",
    "AssertGreaterOrEqual",
    "AssertLessOrEqual",
    "SkipIfEmpty",
    "SkipIfNotEmpty",
    "SkipIfMissing",
    "SkipIfExists",
    # I/O
    "Print",
    "Log",
    "Debug",
    # Profiling
    "Timed",
    "Accumulate",
    "Count",
    "Trace",
    "Tap",
    "Sample",
    # Attributes
    "SetAttr",
]
