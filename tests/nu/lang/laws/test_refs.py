"""Ref invariant laws.

Mirrors ``src/nu/lang/laws/refs.py``. The single law ``ref_not_root``
fires (WARNING) when a Nu program's root atom is a Ref.
"""

from __future__ import annotations

from _support.law_terms import Act, Cmd, FlowS, Q, R
from _support.laws import assert_fails, assert_passes, violations


def test_ref_not_root_passes_when_root_is_a_query() -> None:
    assert_passes(Q())
    assert not [v for v in violations(Q()) if v.law == "ref_not_root"]


def test_ref_not_root_passes_when_root_is_a_command_holding_a_ref() -> None:
    """A Ref under a Command is the canonical placement; only the root counts."""
    assert_passes(Cmd(R()))
    assert not [v for v in violations(Cmd(R())) if v.law == "ref_not_root"]


def test_ref_not_root_passes_when_root_is_a_flow() -> None:
    assert_passes(FlowS(Cmd(R())))
    assert not [v for v in violations(FlowS(Cmd(R()))) if v.law == "ref_not_root"]


def test_ref_not_root_passes_when_root_is_an_action() -> None:
    assert_passes(Act(R()))
    assert not [v for v in violations(Act(R())) if v.law == "ref_not_root"]


def test_ref_not_root_fails_when_root_is_a_ref() -> None:
    assert_fails(R(), "ref_not_root")


def test_ref_not_root_fires_only_at_the_root() -> None:
    """A nested Ref does not retrigger the law at its own path."""
    fired = [v for v in violations(Cmd(R())) if v.law == "ref_not_root"]
    assert not fired


def test_ref_not_root_is_a_warning() -> None:
    """``ref_not_root`` is a WARNING; ``assert_passes`` (errors only) accepts it."""
    from nu.engine import Severity

    fired = [v for v in violations(R()) if v.law == "ref_not_root"]
    assert len(fired) == 1
    assert fired[0].severity is Severity.WARNING
