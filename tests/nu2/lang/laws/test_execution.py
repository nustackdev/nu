"""Execution-mode laws.

Mirrors ``src/nu2/lang/laws/execution.py``. Exercises
``async_atom_needs_loop`` and ``sync_atom_on_loop``. Sync vs async
behaviour is driven by ``requires_async`` and ``async_affinity``
declarations; tests use dimension-local shapes that flip those flags.
"""

from __future__ import annotations

from _support.law_terms import Q
from _support.laws import assert_passes


def test_execution_passes_on_a_plain_scalar_query() -> None:
    """A ``Q`` declares no async affinity and is not placed on the loop -
    ``sync_atom_on_loop`` does not fire."""
    assert_passes(Q())
