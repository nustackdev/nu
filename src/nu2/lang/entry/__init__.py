"""Top-level entry points: construct a Runtime, dispatch to the root, return.

Each entry owns a fresh ``Budget`` for the call, sized by ``max_parallel``,
and closes it on exit. The Runtime sees the Budget through construction; no
global state.

The sync entries (``eval``, ``first``, ``collect``) refuse a Program whose
subtree carries an async-only atom (e.g. Watch); the caller must use the
async sibling. ``eval_in_loop`` is the deliberate bridge.

Modules:

- ``value``  - ``eval``, ``aeval``, ``eval_in_loop``: drive a Program whose
  root yields a single value.
- ``stream`` - ``first``, ``collect``, ``afirst``, ``alast``, ``acollect``:
  drive a Program whose root yields a stream.
- ``term``   - ``run``, ``arun``, ``run_in_loop``: all-in-one Term -> value,
  three phases (compile, validate, evaluate) in one call.
"""

from __future__ import annotations

from nu2.lang.entry.stream import acollect, afirst, alast, collect, first
from nu2.lang.entry.term import arun, run, run_in_loop
from nu2.lang.entry.value import aeval, eval, eval_in_loop


__all__ = [
    "acollect",
    "aeval",
    "afirst",
    "alast",
    "arun",
    "collect",
    "eval",
    "eval_in_loop",
    "first",
    "run",
    "run_in_loop",
]
