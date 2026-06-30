"""Unit tests for ``nu.lang.attributes.effects``.

Covers the ``Effect`` enum, the declared ``MUTATES`` per kind, and the
synthesized ``COMPOSITION_EFFECTS`` fold.
"""

from __future__ import annotations

import pytest
from _support.law_terms import R2, Act, Cmd, FlowS, Q, R

from nu.engine.structure import Declared
from nu.lang import Command
from nu.lang import compile as nu_compile
from nu.lang.attributes import Attr, Effect


# --- Effect enum --------------------------------------------------------


def test_effect_enum_members() -> None:
    assert Effect.READ.value == "read"
    assert Effect.WRITE.value == "write"


def test_effect_is_str_enum() -> None:
    assert isinstance(Effect.WRITE, str)


# --- mutates declared default -------------------------------------------


def _mutates_at_root(term: object) -> frozenset[int]:
    program = nu_compile(term)
    return program.attr(program.root, Attr.MUTATES)


def test_mutates_empty_for_bare_query() -> None:
    assert _mutates_at_root(Q()) == frozenset()


def test_mutates_for_command_annotates_write_slot() -> None:
    assert _mutates_at_root(Cmd(R())) == frozenset({0})


def test_mutates_for_action_annotates_write_slot() -> None:
    assert _mutates_at_root(Act(R())) == frozenset({0})


def test_mutates_empty_for_strategy() -> None:
    assert _mutates_at_root(FlowS(Cmd(R()))) == frozenset()


# --- composition_effects synthesized fold -------------------------------


def _composition_at_root(term: object) -> frozenset[tuple[type, Effect]]:
    program = nu_compile(term)
    root_id = program.id_of[program.root]
    return program.attrs[Attr.COMPOSITION_EFFECTS][root_id]


def test_composition_effects_empty_for_bare_query() -> None:
    assert _composition_at_root(Q()) == frozenset()


def test_composition_effects_command_writes_ref_class() -> None:
    assert _composition_at_root(Cmd(R())) == frozenset({(R, Effect.WRITE)})


def test_composition_effects_action_writes_ref_class() -> None:
    assert _composition_at_root(Act(R())) == frozenset({(R, Effect.WRITE)})


def test_composition_effects_action_in_query_propagates_up() -> None:
    assert _composition_at_root(Q(Act(R()))) == frozenset({(R, Effect.WRITE)})


def test_composition_effects_strategy_unions_children() -> None:
    result = _composition_at_root(FlowS(Cmd(R()), Cmd(R2())))
    assert result == frozenset({(R, Effect.WRITE), (R2, Effect.WRITE)})


def test_composition_effects_same_class_collapses_to_one_fabric() -> None:
    # Two Refs of the same class are one fabric: their WRITE tuples are equal.
    result = _composition_at_root(FlowS(Cmd(R("a")), Cmd(R("b"))))
    assert result == frozenset({(R, Effect.WRITE)})


def test_composition_effects_unannotated_ref_slot_defaults_to_read() -> None:
    class TwoSlotCmd(Command):
        mutates = Declared(value=frozenset({0}))

    result = _composition_at_root(TwoSlotCmd(R(), R2()))
    assert result == frozenset({(R, Effect.WRITE), (R2, Effect.READ)})


def test_composition_effects_skips_non_ref_child_in_annotated_slot() -> None:
    result = _composition_at_root(Cmd(Q()))
    assert result == frozenset()


def test_composition_effects_query_in_write_slot_does_not_contribute() -> None:
    program = nu_compile(Cmd(Q()))
    root_id = program.id_of[program.root]
    assert program.attr(program.root, Attr.MUTATES) == frozenset({0})
    assert program.attrs[Attr.COMPOSITION_EFFECTS][root_id] == frozenset()


# --- column shape -------------------------------------------------------


def test_composition_effects_column_values_are_frozensets() -> None:
    program = nu_compile(FlowS(Cmd(R()), Cmd(R2())))
    column = program.attrs[Attr.COMPOSITION_EFFECTS]
    assert all(isinstance(v, frozenset) for v in column)


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Q(), frozenset()),
        (Cmd(R()), frozenset({(R, Effect.WRITE)})),
        (Act(R()), frozenset({(R, Effect.WRITE)})),
        (
            FlowS(Cmd(R()), Cmd(R2())),
            frozenset({(R, Effect.WRITE), (R2, Effect.WRITE)}),
        ),
        (Q(Act(R())), frozenset({(R, Effect.WRITE)})),
    ],
)
def test_composition_effects_at_root(
    term: object, expected: frozenset[tuple[type, Effect]]
) -> None:
    assert _composition_at_root(term) == expected
