"""Evaluation: how Nu programs run.

- ``sentinels`` - the EMPTY / INVALID propagation values.
- ``runtime``   - ``NuRuntime``: the concrete Runtime that drives compiled Programs.
- ``budget``    - ``Budget``: per-drive thread pool and async semaphore.
- ``loop``      - ``into_loop`` / ``safely_(a)closing`` lifecycle primitives.
- ``context``   - ``Context``: the tagged value store the runtime drives against.

Top-level entry points (``run``, ``eval``, ``aeval``, ...) live one level up
in ``nu2.lang.entry`` - they are the user's front door, not internals.
"""

from __future__ import annotations

from nu2.lang.evaluation.budget import Budget
from nu2.lang.evaluation.context import Attributes, Context
from nu2.lang.evaluation.loop import into_loop, safely_aclosing, safely_closing
from nu2.lang.evaluation.runtime import NuRuntime
from nu2.lang.evaluation.sentinels import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
)


__all__ = [
    "EMPTY",
    "INVALID",
    "Attributes",
    "Budget",
    "Context",
    "Empty",
    "Invalid",
    "NuRuntime",
    "Sentinel",
    "into_loop",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "safely_aclosing",
    "safely_closing",
]
