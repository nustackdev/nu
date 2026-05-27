"""Observability laws.

Mirrors ``src/nu2/lang/laws/observability.py``. Currently the module is
empty; the dimension agent adds ``program_mutates``. The placeholder test
records the intended green-path shape (a mutating program).
"""

from __future__ import annotations

from _support.law_terms import Cmd, FlowS, R
from _support.laws import assert_passes


def test_observability_passes_on_a_mutating_program() -> None:
    """A Strategy that runs a Command writes the Context - observable."""
    assert_passes(FlowS(Cmd(R())))
