"""every_flow -- Flow primitives for everyabc.

Control:
    Seq           -- sequential children
    If            -- conditional: condition, then/else branches
    While         -- loop while condition is truthy
    DoWhile       -- execute first, then loop while condition
    Forever       -- infinite loop
    Switch        -- multi-way branching on selector value

Parallel:
    Parallel      -- concurrent children via asyncio.gather
    Race          -- first completion wins
    All           -- all must succeed, fail fast
    Any           -- first success wins

Iteration:
    ForRange      -- counted loop with optional index Ref
    ForEach       -- sequential iteration over a sequence
    ForEachParallel -- concurrent iteration with semaphore

Error handling:
    TryCatch      -- try/catch/finally with optional error Ref
    Retry         -- retry with exponential backoff
    Assert        -- validate condition, raise on failure

Timing:
    Delay         -- pause execution for a duration
    Timeout       -- execute with a time limit
    Throttle      -- rate-limit execution
    Debounce      -- wait for quiet period before executing

Reactive:
    React         -- wait for a single change event
    ReactForever  -- react to every change indefinitely
    ReactWhile    -- react while condition holds

I/O:
    Print         -- print messages to stdout
    Log           -- structured logging with levels
    Debug         -- quick debug output for development

Assertions:
    AssertEmpty / AssertNotEmpty       -- collection size checks
    AssertExists / AssertMissing       -- existence checks
    AssertEquals / AssertNotEquals     -- equality checks
    AssertGreaterThan / AssertGreaterOrEqual -- ordering checks
    AssertLessThan / AssertLessOrEqual       -- ordering checks
    SkipIfEmpty / SkipIfNotEmpty       -- conditional execution on size
    SkipIfMissing / SkipIfExists       -- conditional execution on existence

"""

from __future__ import annotations

# Assertions
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

# Control
from .control import DoWhile, Forever, If, Seq, Switch, While

# Error handling
from .error import Assert, Retry, TryCatch

# I/O
from .io import Debug, Log, Print

# Iteration
from .iteration import ForEach, ForEachParallel, ForRange

# Parallel
from .parallel import All, Any, Parallel, Race

# Reactive
from .reactive import React, ReactForever, ReactWhile

# Timing
from .timing import Debounce, Delay, Throttle, Timeout


__all__ = [  # noqa: RUF022
    # Control
    "DoWhile",
    "Forever",
    "If",
    "Seq",
    "Switch",
    "While",
    # Parallel
    "All",
    "Any",
    "Parallel",
    "Race",
    # Iteration
    "ForEach",
    "ForEachParallel",
    "ForRange",
    # Error handling
    "Assert",
    "Retry",
    "TryCatch",
    # Timing
    "Debounce",
    "Delay",
    "Throttle",
    "Timeout",
    # Reactive
    "React",
    "ReactForever",
    "ReactWhile",
    # I/O
    "Debug",
    "Log",
    "Print",
    # Assertions
    "AssertEmpty",
    "AssertEquals",
    "AssertExists",
    "AssertGreaterOrEqual",
    "AssertGreaterThan",
    "AssertLessOrEqual",
    "AssertLessThan",
    "AssertMissing",
    "AssertNotEmpty",
    "AssertNotEquals",
    "SkipIfEmpty",
    "SkipIfExists",
    "SkipIfMissing",
    "SkipIfNotEmpty",
]
