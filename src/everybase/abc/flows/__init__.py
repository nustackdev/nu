"""Flow primitives -- control, parallel, iteration, error, timing, I/O, assertions."""

from __future__ import annotations

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
from .control import DoWhile, Forever, If, Seq, Switch, While
from .error import Assert, Retry, TryCatch
from .io import Debug, Log, Print
from .iteration import Fold, ForEach, ForRange
from .parallel import All, Any, Parallel, Race
from .timing import Debounce, Delay, Throttle, Timed, Timeout


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
    "Fold",
    "ForEach",
    "ForRange",
    # Error handling
    "Assert",
    "Retry",
    "TryCatch",
    # Timing
    "Debounce",
    "Delay",
    "Throttle",
    "Timed",
    "Timeout",
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
