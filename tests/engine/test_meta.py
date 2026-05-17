"""Tests for the metaprogramming tools: gate and validate."""

from __future__ import annotations

import pytest

from nu.engine import Attribute, Schema, Symbol, Violation, compile, gate, validate


class Node(Symbol):
    sort = Attribute.declared("Node")


def make_program(*children):
    schema = Schema().finalize()
    return compile(Node(*children), schema)


def rule_leaves_only(program, path):
    if program.children(path):
        yield Violation(path, "LEAF", "node must be a leaf")


def rule_never(program, path):
    return ()


def test_violation_fields():
    v = Violation((1,), "R", "detail")
    assert v.path == (1,)
    assert v.rule == "R"
    assert v.detail == "detail"


def test_gate_clean_program():
    program = make_program()
    assert gate(program, rule_leaves_only) == []


def test_gate_collects_violations():
    program = make_program(Node(), Node())
    verdict = gate(program, rule_leaves_only)
    assert [v.path for v in verdict] == [()]
    assert verdict[0].rule == "LEAF"


def test_gate_runs_every_rule_over_every_node():
    program = make_program(Node())
    verdict = gate(program, rule_leaves_only, rule_never)
    assert len(verdict) == 1


def test_validate_passes_clean_program():
    program = make_program()
    assert validate(program, rule_leaves_only) is program


def test_validate_raises_on_violation():
    program = make_program(Node())
    with pytest.raises(ValueError, match="invalid program"):
        validate(program, rule_leaves_only)


def test_gate_does_not_mutate_the_program():
    program = make_program(Node())
    before = len(program.attr.rows())
    gate(program, rule_leaves_only)
    assert len(program.attr.rows()) == before
