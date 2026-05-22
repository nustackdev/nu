"""Functional tests for the Nu core terms built on nu2.lang.

Attribute real core programs and check the attributes the language assigns:
effects, cardinality, sync/async, the law set. Execution coverage is the
pure-leaf slice for now (Literal, arithmetic, logic); the rest lands as the
fabric pieces (Ref, streams) come online.
"""

from __future__ import annotations

import asyncio

from nu2.core import (
    Add,
    And,
    Delete,
    Div,
    Emit,
    Eq,
    If,
    Literal,
    Lt,
    Mul,
    Neg,
    Not,
    Or,
    Par,
    Range,
    Seq,
    Set,
    Sub,
    Sum,
    Watch,
    While,
)
from nu2.lang import EMPTY, INVALID, LAWS, Attr, Cardinality, Effect, Ref, attribute, gate, validate
from nu2.lang.entry import aeval, arun, eval, run


# --- effects -------------------------------------------------------------


def test_arithmetic_is_pure():
    program = attribute(Add(Literal(1), Literal(2)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


def test_set_tracks_a_write_and_a_read():
    program = attribute(Set(Ref("total"), Add(Ref("total"), Literal(1))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("total", Effect.WRITE), ("total", Effect.READ)}
    )


def test_a_flow_folds_every_command_effect():
    program = attribute(Seq(Set(Ref("a"), Literal(1)), Set(Ref("b"), Literal(2))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("a", Effect.WRITE), ("b", Effect.WRITE)}
    )


# --- cardinality ---------------------------------------------------------


def test_reduction_is_scalar_over_a_stream():
    program = attribute(Sum(Range(Literal(0), Literal(10))))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


# --- sync / async --------------------------------------------------------


def test_a_watch_puts_the_program_on_a_loop():
    assert attribute(Seq(Set(Ref("x"), Literal(1)))).attr((), Attr.ON_LOOP) is False
    assert attribute(Emit(Ref("out"), Watch())).attr((), Attr.ON_LOOP) is True


# --- algebra -------------------------------------------------------------


def test_declared_algebra_reaches_the_program():
    program = attribute(Add(Literal(1), Literal(2)))
    assert program.attr(program.root, Attr.COMMUTATIVE) is True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is True


# --- laws ----------------------------------------------------------------


def test_a_clean_program_validates():
    program = attribute(Seq(Set(Ref("a"), Literal(1)), Set(Ref("b"), Add(Ref("a"), Literal(1)))))
    assert validate(program, *LAWS) is program


def test_a_command_in_a_query_slot_is_refused():
    verdict = gate(attribute(Add(Set(Ref("x"), Literal(1)), Literal(2))), *LAWS)
    assert any(v.law == "composition" for v in verdict)


def test_a_parallel_flow_runs_its_commands():
    program = attribute(Par(Set(Ref("a"), Literal(1)), Set(Ref("b"), Literal(2))))
    assert program.attr(program.root, Attr.EXEC_ORDER) is not None
    assert validate(program, *LAWS) is program


def test_a_control_holds_commands_under_a_condition():
    program = attribute(If(Eq(Ref("flag"), Literal(1)), Set(Ref("done"), Literal(1))))
    assert validate(program, *LAWS) is program


# --- execution: pure scalars --------------------------------------------
#
# This is the pure leaf-of-leaves slice: Literal + arithmetic + logic.
# Atoms that need a fabric (Ref, streams, reductions, commands) land later.


def _eval(term: object) -> object:
    value, _ = eval(attribute(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(attribute(term))
    return value


def test_literal_yields_its_payload():
    assert _eval(Literal(42)) == 42


def test_arithmetic_folds_operands():
    assert _eval(Add(Literal(1), Literal(2), Literal(3))) == 6
    assert _eval(Mul(Literal(2), Literal(3), Literal(4))) == 24
    assert _eval(Sub(Literal(10), Literal(3))) == 7
    assert _eval(Div(Literal(8), Literal(2))) == 4
    assert _eval(Neg(Literal(5))) == -5


def test_nested_arithmetic():
    program = Add(Mul(Literal(2), Literal(3)), Neg(Literal(1)))
    assert _eval(program) == 5


def test_logic_comparisons():
    assert _eval(Eq(Literal(2), Literal(2))) is True
    assert _eval(Lt(Literal(1), Literal(2))) is True
    assert _eval(Lt(Literal(2), Literal(1))) is False


def test_boolean_ops():
    assert _eval(And(Literal(True), Literal(True))) is True
    assert _eval(And(Literal(True), Literal(False))) is False
    assert _eval(Or(Literal(False), Literal(True))) is True
    assert _eval(Not(Literal(False))) is True


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Add(Literal(2), Literal(3)))) == 5
    assert asyncio.run(_aeval(And(Literal(True), Literal(True)))) is True


def test_a_sentinel_operand_collapses_a_query_to_invalid():
    # Literal yields its payload value as-is, so a Literal carrying EMPTY
    # serves as a sentinel-producing leaf. Add's sentinel-aware fold
    # collapses on it.
    assert _eval(Add(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(Mul(Literal(2), Literal(INVALID))) is INVALID
    assert asyncio.run(_aeval(And(Literal(True), Literal(EMPTY)))) is INVALID


def test_run_attributes_validates_and_evaluates_a_description():
    # One-call: description -> AttributedTerm -> validated -> driven.
    value, _ = run(Add(Literal(2), Mul(Literal(3), Literal(4))))
    assert value == 14
    value, _ = asyncio.run(arun(And(Literal(True), Literal(True))))
    assert value is True


def test_run_raises_on_an_invalid_description():
    import pytest

    # A Command in a Query slot fails the composition law.
    with pytest.raises(ValueError, match="invalid program"):
        run(Add(Set(Ref("x"), Literal(1)), Literal(2)))


def test_eval_refuses_async_only_programs():
    import pytest

    program = attribute(Emit(Ref("out"), Watch()))
    with pytest.raises(RuntimeError, match="async-only"):
        eval(program)


# --- placeholders: command / flow / span execution requires a fabric -----
#
# Set, Seq, Par, If, While, Delete, Emit, Scope, Retry: pending. Once Refs
# and Commands have eval / aeval methods, the old execution tests come back.
_ = (Set, Delete, Emit, Seq, Par, If, While, Sum, Range)
