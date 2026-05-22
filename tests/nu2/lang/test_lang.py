"""Functional tests for Nu rebuilt on the attribute layer (nu2.lang).

The lang package is the abstract framework; a Nu program needs concrete
atoms. These tests bring their own minimal atoms, then exercise every concern:
effect tracking, cardinality, sync/async, exec order, and the law set.
"""

from __future__ import annotations

import pytest

from nu2.engine import Attribute
from nu2.lang import (
    LAWS,
    Attr,
    Bracket,
    Cardinality,
    Command,
    Effect,
    ExecOrder,
    Reduction,
    Ref,
    ScalarQuery,
    Severity,
    Strategy,
    StreamQuery,
    attribute,
    gate,
    validate,
)


# --- test atoms: concrete kinds the framework deliberately leaves open ---


class Write(Command):
    """A Command that writes its first slot."""

    own_effects = Attribute.declared({0: Effect.WRITE})


class AsyncWrite(Command):
    """A write Command that runs only on an event loop."""

    requires_async = Attribute.declared(True)
    own_effects = Attribute.declared({0: Effect.WRITE})


class SyncWrite(Command):
    """A write Command that runs only off an event loop."""

    async_affinity = Attribute.declared(False)
    own_effects = Attribute.declared({0: Effect.WRITE})


class Fork(Strategy):
    """A Strategy that runs its child Commands in parallel."""

    exec_order = Attribute.declared(ExecOrder.PARALLEL)


# --- effects -------------------------------------------------------------


def test_pure_tree_tracks_no_effects():
    program = attribute(ScalarQuery(ScalarQuery(), ScalarQuery()))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


def test_command_tracks_a_write():
    program = attribute(Write(Ref("x"), ScalarQuery()))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset({("x", Effect.WRITE)})


def test_ref_in_a_query_slot_tracks_a_read():
    program = attribute(ScalarQuery(Ref("counter")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("counter", Effect.READ)}
    )


def test_effects_fold_up_the_subtree():
    program = attribute(Write(Ref("total"), ScalarQuery(Ref("total"))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("total", Effect.WRITE), ("total", Effect.READ)}
    )


# --- cardinality ---------------------------------------------------------


def test_cardinality_is_fixed_by_kind():
    program = attribute(ScalarQuery(StreamQuery()))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


def test_span_forwards_its_body_cardinality():
    program = attribute(Bracket(StreamQuery()))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.STREAM


def test_reduction_is_scalar_over_a_stream():
    program = attribute(Reduction(StreamQuery()))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR


# --- sync / async --------------------------------------------------------


def test_has_async_only_atom_only_when_an_async_atom_is_present():
    assert attribute(ScalarQuery()).attr((), Attr.HAS_ASYNC_ONLY_ATOM) is False
    assert attribute(AsyncWrite(Ref("u"))).attr((), Attr.HAS_ASYNC_ONLY_ATOM) is True


def test_on_loop_threads_from_the_root():
    assert attribute(ScalarQuery()).attr((), Attr.ON_LOOP) is False
    assert attribute(AsyncWrite(Ref("u"))).attr((), Attr.ON_LOOP) is True


def test_parallel_parent_resolves_on_loop_per_child():
    program = attribute(Fork(AsyncWrite(Ref("u")), SyncWrite(Ref("d"))))
    assert program.attr(program.root, Attr.ON_LOOP) is True
    assert program.attr((0,), Attr.ON_LOOP) is True
    assert program.attr((1,), Attr.ON_LOOP) is False


# --- laws ----------------------------------------------------------------


def test_composition_matrix_rejects_a_command_in_a_query():
    verdict = gate(attribute(ScalarQuery(Write(Ref("x")))), *LAWS)
    assert any(v.law == "composition" for v in verdict)


def test_query_subtree_must_not_write():
    verdict = gate(attribute(ScalarQuery(Write(Ref("x")))), *LAWS)
    assert any(v.law == "query_no_write" for v in verdict)


def test_scalar_consumer_fed_a_stream_is_refused():
    verdict = gate(attribute(ScalarQuery(StreamQuery())), *LAWS)
    assert any(v.law == "scalar_stream_refused" for v in verdict)


def test_a_reduction_bridges_the_refused_edge():
    verdict = gate(attribute(Reduction(StreamQuery())), *LAWS)
    assert not any(v.law == "scalar_stream_refused" for v in verdict)


def test_an_effect_slot_must_hold_a_ref():
    verdict = gate(attribute(Write(ScalarQuery())), *LAWS)
    assert any(v.law == "ref_slots" for v in verdict)


def test_a_flow_subtree_must_contain_a_command():
    verdict = gate(attribute(Strategy()), *LAWS)
    assert any(v.law == "flow_has_command" for v in verdict)


def test_sync_atom_on_the_loop_is_a_warning_not_a_rejection():
    # A sequential parent threads "on loop" down: the sync-only child is
    # forced onto the loop. The law warns; validate still passes.
    program = attribute(Strategy(AsyncWrite(Ref("u")), SyncWrite(Ref("d"))))
    warnings = [v for v in gate(program, *LAWS) if v.law == "sync_atom_on_loop"]
    assert [v.severity for v in warnings] == [Severity.WARNING]
    assert validate(program, *LAWS) is program


def test_validate_passes_a_clean_program_and_raises_on_a_bad_one():
    clean = attribute(Strategy(Write(Ref("a")), Write(Ref("b"))))
    assert validate(clean, *LAWS) is clean

    with pytest.raises(ValueError, match="ref_slots"):
        validate(attribute(Write(ScalarQuery())), *LAWS)


def test_attr_is_queryable_as_a_relation():
    program = attribute(Write(Ref("x"), ScalarQuery(Ref("x"))))
    impure = program.attr.rows(name=Attr.COMPOSITION_EFFECTS).where(lambda row: bool(row["value"]))
    assert program.root in impure.paths()
