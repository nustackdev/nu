"""Functional tests for Nu rebuilt on the engine (nu.symbols).

Construct -> compile -> query / gate, exercising every Nu concern: effect
tracking, purity, realization, execution mode, and the gate set.
"""

from __future__ import annotations

import pytest

from nu.symbols import (
    RULES,
    Add,
    AsyncFetch,
    BlockingScan,
    Collect,
    Effect,
    Literal,
    Parallel,
    Range,
    Ref,
    Sequential,
    Snapshot,
    Store,
    compile,
    gate,
    validate,
)


# --- effects -------------------------------------------------------------


def test_pure_tree_tracks_no_effects():
    program = compile(Add(Literal(2), Literal(3)))
    assert program.attr(program.root, "tracked_effects") == frozenset()
    assert program.attr(program.root, "is_pure") is True


def test_command_tracks_a_write():
    program = compile(Store(Ref("x"), Literal(5)))
    assert program.attr(program.root, "tracked_effects") == frozenset({("x", Effect.WRITE)})
    assert program.attr(program.root, "is_pure") is False


def test_ref_in_query_slot_tracks_a_read():
    # The dual role: a Ref in a Query slot binds in read role.
    program = compile(Add(Ref("counter"), Literal(1)))
    assert program.attr(program.root, "tracked_effects") == frozenset({("counter", Effect.READ)})


def test_effects_fold_up_the_subtree():
    program = compile(Store(Ref("total"), Add(Ref("total"), Literal(1))))
    assert program.attr(program.root, "tracked_effects") == frozenset(
        {
            ("total", Effect.WRITE),
            ("total", Effect.READ),
        }
    )


# --- realization ---------------------------------------------------------


def test_realization_is_fixed_by_kind():
    program = compile(Add(Range(Literal(3)), Literal(1)))
    assert program.attr(program.root, "realization_eff") == "scalar"
    assert program.attr((0,), "realization_eff") == "stream"


def test_span_forwards_its_body_realization():
    program = compile(Snapshot(Range(Literal(3))))
    assert program.attr(program.root, "realization_eff") == "stream"


def test_reduction_is_scalar_over_a_stream():
    program = compile(Collect(Range(Literal(5))))
    assert program.attr(program.root, "realization_eff") == "scalar"


# --- execution mode ------------------------------------------------------


def test_needs_loop_when_an_async_atom_is_present():
    pure = compile(Add(Literal(1), Literal(2)))
    assert pure.attr(pure.root, "needs_loop") is False

    asy = compile(Add(AsyncFetch(Ref("u")), Literal(1)))
    assert asy.attr(asy.root, "needs_loop") is True


def test_exec_state_threads_from_the_root():
    pure = compile(Add(Literal(1), Literal(2)))
    assert pure.attr(pure.root, "exec_state") == "no_loop"

    asy = compile(AsyncFetch(Ref("u")))
    assert asy.attr(asy.root, "exec_state") == "loop"


def test_concurrent_parent_resolves_exec_state_per_child():
    # A concurrent Flow resolves each child on its own subtree (hybrid).
    program = compile(Parallel(AsyncFetch(Ref("u")), BlockingScan(Ref("d"))))
    assert program.attr(program.root, "exec_state") == "loop"
    assert program.attr((0,), "exec_state") == "loop"
    assert program.attr((1,), "exec_state") == "no_loop"


# --- gates ---------------------------------------------------------------


def test_composition_matrix_rejects_a_command_in_a_query():
    verdict = gate(compile(Add(Literal(1), Store(Ref("x"), Literal(2)))), *RULES)
    assert any(v.rule == "COMPOSE" for v in verdict)


def test_query_subtree_must_not_write():
    verdict = gate(compile(Add(Literal(1), Store(Ref("x"), Literal(2)))), *RULES)
    assert any(v.rule == "QUERY_WRITE" for v in verdict)


def test_refused_scalar_fed_a_stream():
    verdict = gate(compile(Add(Range(Literal(3)), Literal(1))), *RULES)
    assert any(v.rule == "REFUSED" for v in verdict)


def test_reduction_bridges_the_refused_edge():
    verdict = gate(compile(Collect(Range(Literal(3)))), *RULES)
    assert not any(v.rule == "REFUSED" for v in verdict)


def test_ref_only_slot_must_hold_a_ref():
    verdict = gate(compile(Store(Literal(0), Literal(1))), *RULES)
    assert any(v.rule == "SLOT" for v in verdict)


def test_flow_subtree_must_contain_a_command():
    verdict = gate(compile(Sequential()), *RULES)
    assert any(v.rule == "FLOW_EMPTY" for v in verdict)


def test_validate_passes_a_clean_program_and_raises_on_a_bad_one():
    clean = compile(Sequential(Store(Ref("a"), Literal(1)), Store(Ref("b"), Literal(2))))
    assert validate(clean, *RULES) is clean

    bad = compile(Store(Literal(0), Literal(1)))
    with pytest.raises(ValueError, match="SLOT"):
        validate(bad, *RULES)


# --- the store as a relation --------------------------------------------


def test_attr_is_queryable_as_a_relation():
    program = compile(Store(Ref("x"), Add(Ref("x"), Literal(1))))
    impure = program.attr.rows(name="is_pure").where(lambda r: r["value"] is False)
    assert program.root in impure.paths()
