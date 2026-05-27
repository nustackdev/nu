"""Observability laws.

Mirrors ``src/nu2/lang/laws/observability.py``. ``program_mutates`` fires
on the root when the subtree contains no WRITE.
"""

from __future__ import annotations

from _support.law_terms import Act, Brk, Cmd, FlowS, Q, R, Stream
from _support.laws import assert_fails, assert_passes, violations

from nu2.engine import Severity


def test_program_mutates_passes_when_root_is_a_strategy_with_a_command() -> None:
    """A Strategy that runs a Command writes the Context."""
    assert_passes(FlowS(Cmd(R())))


def test_program_mutates_passes_when_root_is_a_bare_command() -> None:
    """A bare Command at the root is itself a WRITE."""
    assert_passes(Cmd(R()))


def test_program_mutates_passes_when_root_is_a_query_with_an_action_descendant() -> None:
    """An Action in a Query's value slot still carries a WRITE up the tree."""
    assert_passes(Q(Act(R())))


def test_program_mutates_fails_when_root_is_a_pure_query() -> None:
    """A bare Query has no WRITE anywhere; the law warns."""
    assert_fails(Q(), "program_mutates")


def test_program_mutates_fails_when_root_is_a_pure_stream() -> None:
    """A pure StreamQuery yields values but never mutates."""
    assert_fails(Stream(), "program_mutates")


def test_program_mutates_fails_when_a_span_wraps_a_pure_query() -> None:
    """A Bracket wrapping a non-mutating body still doesn't mutate."""
    assert_fails(Brk(Q()), "program_mutates")


def test_program_mutates_is_a_warning() -> None:
    """The law is a developer-convenience warning, not an error."""
    fired = [v for v in violations(Q()) if v.law == "program_mutates"]
    assert fired
    assert all(v.severity is Severity.WARNING for v in fired)


def test_program_mutates_does_not_fire_on_non_root_pure_nodes() -> None:
    """The scope is root-only; a pure subtree under a mutator is fine."""
    fired = [v for v in violations(FlowS(Cmd(R()))) if v.law == "program_mutates"]
    assert not fired
