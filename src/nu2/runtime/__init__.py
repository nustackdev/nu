"""Nu runtime - the per-execution driver, its Budget, and the toolkit.

Drives a compiled Program against a Context. Atoms implement ``eval`` /
``aeval`` methods that receive a ``Runtime`` and a path; they recurse and
inspect structure through the Runtime's toolkit.

- ``Runtime`` - driver class; the toolkit lives as methods on it.
- ``Budget`` - per-execution thread pool + concurrency gate; owned by Runtime.
- ``eval`` / ``aeval`` - top-level entries; construct a Runtime, dispatch
  to the root, return ``(value, ctx)``.
- ``eval_in_loop`` - sync caller bridging into an async-only Program.
- ``into_loop`` - stateless coroutine-runner for sync code.
"""

from nu2.runtime.budget import Budget
from nu2.runtime.driver import Runtime
from nu2.runtime.entry import aeval, eval, eval_in_loop
from nu2.runtime.loop import into_loop, safely_aclosing, safely_closing


__all__ = [
    "Budget",
    "Runtime",
    "aeval",
    "eval",
    "eval_in_loop",
    "into_loop",
    "safely_aclosing",
    "safely_closing",
]
