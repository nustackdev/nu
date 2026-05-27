"""Sort and composition laws.

Mirrors ``src/nu2/lang/laws/composition.py``. Exercises ``composition``,
``query_no_write``, ``command_has_write``, ``flow_has_command`` (and any
laws the dimension agent adds: ``action_has_write``,
``flow_body_is_mutator``, the rename to ``query_no_own_write``).
"""

from __future__ import annotations

from _support.law_terms import Cmd, FlowS, Q, R
from _support.laws import assert_fails, assert_passes


def test_composition_passes_when_strategy_holds_command() -> None:
    """A Strategy holding a Command fits the matrix row for ``_WORK``."""
    assert_passes(FlowS(Cmd(R())))


def test_composition_fails_when_query_holds_command() -> None:
    """A Query's matrix row is ``_VALUE``; a Command yields nothing."""
    assert_fails(Q(Cmd(R())), "composition")
