"""Top-level entry points: construct a Runtime, dispatch, return.

Engine stages, each in its own module:

- ``compilation`` - ``compile`` a Term against Nu's SCHEMA -> Program.
- ``validation``  - ``validate`` a Program against Nu's LAWS.
- ``evaluation``  - drive an already-compiled Program. Two families by
  root cardinality: value-root (``eval`` / ``aeval`` / ``eval_in_loop``)
  and stream-root (``first`` / ``collect`` / ``afirst`` / ``alast`` /
  ``acollect``).
- ``run``         - all-in-one Term -> result: chains compile, validate,
  eval in one call (``run`` / ``arun`` / ``run_in_loop``).

Each drive/run entry owns a fresh ``Budget`` for the call, sized by
``max_parallel``, and closes it on exit. The Runtime sees the Budget
through construction; no global state. The sync entries refuse a Program
whose subtree carries an async-only atom (e.g. Watch); the caller must
use the async sibling. ``eval_in_loop`` / ``run_in_loop`` are deliberate
bridges.
"""

from __future__ import annotations

from .compilation import compile
from .evaluation import acollect, aeval, afirst, alast, collect, eval, eval_in_loop, first
from .run import arun, run, run_in_loop
from .validation import validate


__all__ = [
    "acollect",
    "aeval",
    "afirst",
    "alast",
    "arun",
    "collect",
    "compile",
    "eval",
    "eval_in_loop",
    "first",
    "run",
    "run_in_loop",
    "validate",
]
