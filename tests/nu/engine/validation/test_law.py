"""Unit tests for ``nu.engine.validation.law``.

Covers :class:`Law` (construction, ``check``), the verdict primitives
(:class:`Severity`, :class:`Violation`), the runners (:func:`gate`,
:func:`validate`), and :class:`ValidationError`.
"""

from __future__ import annotations

import pytest
from _support.terms import Leaf, Node

from nu.engine.compilation import compile
from nu.engine.validation import (
    Law,
    Severity,
    ValidationError,
    Violation,
    gate,
    validate,
)


# --- construction ---------------------------------------------------------


def test_law_defaults_to_error_severity():
    law = Law(
        "x",
        scope=lambda program, path: True,
        holds=lambda program, path: True,
        message="x",
    )
    assert law.severity is Severity.ERROR


def test_law_repr_shows_the_name():
    law = Law(
        "no-empty-nodes",
        scope=lambda program, path: True,
        holds=lambda program, path: True,
        message="x",
    )
    assert repr(law) == "Law('no-empty-nodes')"


# --- check ----------------------------------------------------------------


def test_check_returns_none_when_path_is_out_of_scope(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "x",
        scope=lambda program, path: False,
        holds=lambda program, path: False,  # would fail, but scope rejects
        message="should never fire",
    )
    assert law.check(p, ()) is None


def test_check_returns_none_when_the_predicate_holds(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "x",
        scope=lambda program, path: True,
        holds=lambda program, path: True,
        message="should never fire",
    )
    assert law.check(p, ()) is None


def test_check_returns_a_violation_when_in_scope_and_holds_is_false(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "always-fails",
        scope=lambda program, path: True,
        holds=lambda program, path: False,
        message="boom",
    )
    v = law.check(p, ())
    assert v == Violation(path=(), law="always-fails", detail="boom", severity=Severity.ERROR)


def test_check_resolves_a_callable_message_at_failure_time(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "named",
        scope=lambda program, path: True,
        holds=lambda program, path: False,
        message=lambda program, path: f"at {path} on {type(program.terms[0]).__name__}",
    )
    v = law.check(p, ())
    assert v is not None
    assert v.detail == "at () on Leaf"


# --- gate -----------------------------------------------------------------


def test_gate_returns_empty_when_every_law_holds(schema):
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    law = Law(
        "ok",
        scope=lambda program, path: True,
        holds=lambda program, path: True,
        message="x",
    )
    assert gate(p, law) == []


def test_gate_collects_violations_across_every_node_and_law(schema):
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    # Two laws: one fails only at the root, one fails only at leaves.
    root_only = Law(
        "no-root",
        scope=lambda program, path: path == (),
        holds=lambda program, path: False,
        message="root fails",
    )
    leaves_only = Law(
        "no-leaves",
        scope=lambda program, path: program.children[program.id_of[path]] == (),
        holds=lambda program, path: False,
        message="leaf fails",
    )
    violations = gate(p, root_only, leaves_only)
    paths_and_laws = [(v.path, v.law) for v in violations]
    assert ((), "no-root") in paths_and_laws
    assert ((0,), "no-leaves") in paths_and_laws
    assert ((1,), "no-leaves") in paths_and_laws
    assert len(violations) == 3


def test_gate_keeps_warning_level_violations(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "soft",
        scope=lambda program, path: True,
        holds=lambda program, path: False,
        message="warned",
        severity=Severity.WARNING,
    )
    [v] = gate(p, law)
    assert v.severity is Severity.WARNING


# --- validate -------------------------------------------------------------


def test_validate_returns_the_program_when_every_law_passes(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "ok",
        scope=lambda program, path: True,
        holds=lambda program, path: True,
        message="x",
    )
    assert validate(p, law) is p


def test_validate_does_not_raise_on_warning_only_violations(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "soft",
        scope=lambda program, path: True,
        holds=lambda program, path: False,
        message="warned",
        severity=Severity.WARNING,
    )
    assert validate(p, law) is p


def test_validate_raises_validation_error_on_an_error_level_violation(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "hard",
        scope=lambda program, path: True,
        holds=lambda program, path: False,
        message="no good",
    )
    with pytest.raises(ValidationError) as exc:
        validate(p, law)
    assert exc.value.violations == [
        Violation(path=(), law="hard", detail="no good", severity=Severity.ERROR),
    ]
    assert "no good" in str(exc.value)
    assert "[hard]" in str(exc.value)


def test_validation_error_subclasses_value_error(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    law = Law(
        "hard",
        scope=lambda program, path: True,
        holds=lambda program, path: False,
        message="x",
    )
    with pytest.raises(ValueError):
        validate(p, law)
