"""Tests for the metaprogramming tools: Law, gate, and validate."""

from __future__ import annotations

import pytest

from nu2.engine import (
    Attribute,
    Law,
    Predicate,
    Schema,
    Severity,
    Symbol,
    Violation,
    compile,
    gate,
    validate,
)


class Node(Symbol):
    sort = Attribute.declared("Node")


def make_program(*children):
    schema = Schema().finalize()
    return compile(Node(*children), schema)


def _is_leaf(program, path):
    return not program.children(path)


leaves_only = Law(
    "leaves_only",
    scope=lambda program, path: True,
    holds=_is_leaf,
    message="node must be a leaf",
)

warn_branch = Law(
    "warn_branch",
    scope=lambda program, path: True,
    holds=_is_leaf,
    message="node has children",
    severity=Severity.WARNING,
)


def test_violation_fields():
    v = Violation((1,), "R", "detail", Severity.ERROR)
    assert v.path == (1,)
    assert v.law == "R"
    assert v.detail == "detail"
    assert v.severity is Severity.ERROR


def test_predicate_combines_with_and_or_not():
    always = Predicate(lambda program, path: True)
    never = Predicate(lambda program, path: False)
    program = make_program()
    assert (always & always)(program, ()) is True
    assert (always & never)(program, ()) is False
    assert (never | always)(program, ()) is True
    assert (~never)(program, ()) is True


def test_gate_clean_program():
    program = make_program()
    assert gate(program, leaves_only) == []


def test_gate_collects_violations():
    program = make_program(Node(), Node())
    verdict = gate(program, leaves_only)
    assert [v.path for v in verdict] == [()]
    assert verdict[0].law == "leaves_only"


def test_gate_runs_every_law_over_every_node():
    program = make_program(Node())
    verdict = gate(program, leaves_only, warn_branch)
    assert len(verdict) == 2


def test_validate_passes_clean_program():
    program = make_program()
    assert validate(program, leaves_only) is program


def test_validate_raises_on_an_error_violation():
    program = make_program(Node())
    with pytest.raises(ValueError, match="invalid program"):
        validate(program, leaves_only)


def test_validate_passes_a_warning_violation():
    program = make_program(Node())
    assert validate(program, warn_branch) is program
    assert gate(program, warn_branch)[0].severity is Severity.WARNING


def test_message_may_be_a_function_of_the_node():
    law = Law(
        "named",
        scope=lambda program, path: True,
        holds=_is_leaf,
        message=lambda program, path: f"branch at {path}",
    )
    verdict = gate(make_program(Node()), law)
    assert verdict[0].detail == "branch at ()"


def test_gate_does_not_mutate_the_program():
    program = make_program(Node())
    before = len(program.attr.rows())
    gate(program, leaves_only)
    assert len(program.attr.rows()) == before
