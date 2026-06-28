"""Functional tests for the Nu core terms built on nu2.lang.

Compile real core programs and check the attributes the language assigns:
effects, cardinality, sync/async, the law set. Execution coverage is the
pure-leaf slice for now (LiteralQuery, arithmetic, logic); the rest lands as the
fabric pieces (Ref, streams) come online.
"""

from __future__ import annotations

import asyncio

from nu2.context import SetCommand
from nu2.core import (
    AddQuery,
    AndQuery,
    DivQuery,
    EqQuery,
    IterQuery,
    LiteralQuery,
    LtQuery,
    MulQuery,
    NegQuery,
    NotQuery,
    OrQuery,
    SubQuery,
    SumQuery,
)
from nu2.lang import EMPTY, INVALID, LAWS, Attr, Cardinality, Effect, Ref, compile, gate, validate
from nu2.lang.helpers import aeval, arun, eval, run


# --- effects -------------------------------------------------------------


def test_arithmetic_is_pure():
    program = compile(AddQuery(LiteralQuery(1), LiteralQuery(2)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


def test_set_tracks_a_write_and_a_read():
    # Both Refs are the same class, so the same fabric: a WRITE and a READ on it.
    program = compile(SetCommand(Ref(), AddQuery(Ref(), LiteralQuery(1))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {(Ref, Effect.WRITE), (Ref, Effect.READ)}
    )


# --- cardinality ---------------------------------------------------------


def test_reduction_is_scalar_over_a_stream():
    program = compile(SumQuery(IterQuery(LiteralQuery(range(10)))))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


# --- algebra -------------------------------------------------------------


def test_declared_algebra_reaches_the_program():
    program = compile(AddQuery(LiteralQuery(1), LiteralQuery(2)))
    assert program.attr(program.root, Attr.COMMUTATIVE) is True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is True


# --- laws ----------------------------------------------------------------


def test_a_clean_program_validates():
    program = compile(SetCommand(Ref("total"), AddQuery(Ref("total"), LiteralQuery(1))))
    assert validate(program, *LAWS) is program


def test_a_command_in_a_query_slot_is_refused():
    verdict = gate(compile(AddQuery(SetCommand(Ref("x"), LiteralQuery(1)), LiteralQuery(2))), *LAWS)
    assert any(v.law == "composition" for v in verdict)


# --- execution: pure scalars --------------------------------------------
#
# This is the pure leaf-of-leaves slice: LiteralQuery + arithmetic + logic.
# Atoms that need a fabric (Ref, streams, reductions, commands) land later.


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


def test_literal_yields_its_payload():
    assert _eval(LiteralQuery(42)) == 42


def test_arithmetic_folds_operands():
    assert _eval(AddQuery(LiteralQuery(1), LiteralQuery(2), LiteralQuery(3))) == 6
    assert _eval(MulQuery(LiteralQuery(2), LiteralQuery(3), LiteralQuery(4))) == 24
    assert _eval(SubQuery(LiteralQuery(10), LiteralQuery(3))) == 7
    assert _eval(DivQuery(LiteralQuery(8), LiteralQuery(2))) == 4
    assert _eval(NegQuery(LiteralQuery(5))) == -5


def test_nested_arithmetic():
    program = AddQuery(MulQuery(LiteralQuery(2), LiteralQuery(3)), NegQuery(LiteralQuery(1)))
    assert _eval(program) == 5


def test_logic_comparisons():
    assert _eval(EqQuery(LiteralQuery(2), LiteralQuery(2))) is True
    assert _eval(LtQuery(LiteralQuery(1), LiteralQuery(2))) is True
    assert _eval(LtQuery(LiteralQuery(2), LiteralQuery(1))) is False


def test_boolean_ops():
    assert _eval(AndQuery(LiteralQuery(True), LiteralQuery(True))) is True
    assert _eval(AndQuery(LiteralQuery(True), LiteralQuery(False))) is False
    assert _eval(OrQuery(LiteralQuery(False), LiteralQuery(True))) is True
    assert _eval(NotQuery(LiteralQuery(False))) is True


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(AddQuery(LiteralQuery(2), LiteralQuery(3)))) == 5
    assert asyncio.run(_aeval(AndQuery(LiteralQuery(True), LiteralQuery(True)))) is True


def test_a_sentinel_operand_collapses_a_query_to_invalid():
    # LiteralQuery yields its payload value as-is, so a LiteralQuery carrying EMPTY
    # serves as a sentinel-producing leaf. AddQuery's sentinel-aware fold
    # collapses on it.
    assert _eval(AddQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(MulQuery(LiteralQuery(2), LiteralQuery(INVALID))) is INVALID
    assert asyncio.run(_aeval(AndQuery(LiteralQuery(True), LiteralQuery(EMPTY)))) is INVALID


def test_run_compiles_validates_and_evaluates_a_description():
    # One-call: Term -> Program -> validated -> driven.
    value, _ = run(AddQuery(LiteralQuery(2), MulQuery(LiteralQuery(3), LiteralQuery(4))))
    assert value == 14
    value, _ = asyncio.run(arun(AndQuery(LiteralQuery(True), LiteralQuery(True))))
    assert value is True


def test_run_raises_on_an_invalid_description():
    import pytest

    # A Command in a Query slot fails the composition law.
    with pytest.raises(ValueError, match="invalid program"):
        run(AddQuery(SetCommand(Ref("x"), LiteralQuery(1)), LiteralQuery(2)))
