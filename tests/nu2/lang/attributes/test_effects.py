"""Unit tests for ``nu2.lang.attributes.effects``.

Covers the ``Effect`` enum, the declared ``OWN_EFFECTS`` per kind, and the
synthesized ``COMPOSITION_EFFECTS`` fold.
"""

from __future__ import annotations

import pytest
from _support.law_terms import Act, Cmd, FlowS, Q, R

from nu2.engine.structure import Declared
from nu2.lang import Command
from nu2.lang import compile as nu_compile
from nu2.lang.attributes import Attr, Effect


# --- Effect enum --------------------------------------------------------


def test_effect_enum_members() -> None:
    assert Effect.RESOLVE.value == "resolve"
    assert Effect.READ.value == "read"
    assert Effect.WRITE.value == "write"


def test_effect_is_str_enum() -> None:
    assert isinstance(Effect.WRITE, str)


# --- own_effects declared default ---------------------------------------


def _own_at_root(term: object) -> dict[int, Effect]:
    program = nu_compile(term)
    return program.attr(program.root, Attr.OWN_EFFECTS)


def test_own_effects_empty_for_bare_query() -> None:
    assert _own_at_root(Q()) == {}


def test_own_effects_for_command_annotates_write_slot() -> None:
    assert _own_at_root(Cmd(R())) == {0: Effect.WRITE}


def test_own_effects_for_action_annotates_write_slot() -> None:
    assert _own_at_root(Act(R())) == {0: Effect.WRITE}


def test_own_effects_empty_for_strategy() -> None:
    assert _own_at_root(FlowS(Cmd(R()))) == {}


# --- composition_effects synthesized fold -------------------------------


def _composition_at_root(term: object) -> frozenset[tuple[str, Effect]]:
    program = nu_compile(term)
    root_id = program.id_of[program.root]
    return program.attrs[Attr.COMPOSITION_EFFECTS][root_id]


def test_composition_effects_empty_for_bare_query() -> None:
    assert _composition_at_root(Q()) == frozenset()


def test_composition_effects_command_writes_named_ref() -> None:
    assert _composition_at_root(Cmd(R("x"))) == frozenset({("x", Effect.WRITE)})


def test_composition_effects_action_writes_named_ref() -> None:
    assert _composition_at_root(Act(R("z"))) == frozenset({("z", Effect.WRITE)})


def test_composition_effects_action_in_query_propagates_up() -> None:
    assert _composition_at_root(Q(Act(R("z")))) == frozenset({("z", Effect.WRITE)})


def test_composition_effects_strategy_unions_children() -> None:
    result = _composition_at_root(FlowS(Cmd(R("a")), Cmd(R("b"))))
    assert result == frozenset({("a", Effect.WRITE), ("b", Effect.WRITE)})


def test_composition_effects_unannotated_ref_slot_defaults_to_read() -> None:
    class TwoSlotCmd(Command):
        own_effects = Declared(value={0: Effect.WRITE})

    result = _composition_at_root(TwoSlotCmd(R("a"), R("b")))
    assert result == frozenset({("a", Effect.WRITE), ("b", Effect.READ)})


def test_composition_effects_skips_non_ref_child_in_annotated_slot() -> None:
    result = _composition_at_root(Cmd(Q()))
    assert result == frozenset()


def test_composition_effects_query_in_write_slot_does_not_contribute() -> None:
    program = nu_compile(Cmd(Q()))
    root_id = program.id_of[program.root]
    assert program.attr(program.root, Attr.OWN_EFFECTS) == {0: Effect.WRITE}
    assert program.attrs[Attr.COMPOSITION_EFFECTS][root_id] == frozenset()


# --- column shape -------------------------------------------------------


def test_composition_effects_column_values_are_frozensets() -> None:
    program = nu_compile(FlowS(Cmd(R("a")), Cmd(R("b"))))
    column = program.attrs[Attr.COMPOSITION_EFFECTS]
    assert all(isinstance(v, frozenset) for v in column)


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Q(), frozenset()),
        (Cmd(R("x")), frozenset({("x", Effect.WRITE)})),
        (Act(R("y")), frozenset({("y", Effect.WRITE)})),
        (
            FlowS(Cmd(R("a")), Cmd(R("b"))),
            frozenset({("a", Effect.WRITE), ("b", Effect.WRITE)}),
        ),
        (Q(Act(R("z"))), frozenset({("z", Effect.WRITE)})),
    ],
)
def test_composition_effects_at_root(term: object, expected: frozenset[tuple[str, Effect]]) -> None:
    assert _composition_at_root(term) == expected
