"""Execution tests for the arithmetic atoms in nu.core.arithmetic.

Each atom is a pure ScalarQuery that computes from its operand values, so it
carries compile / acompile thunks and is exercised end to end: compile the
term, drive it, check the value. Sentinel propagation (EMPTY / INVALID on any
operand collapses to INVALID) is checked alongside, and the async siblings are
asserted to mirror the sync hot path.
"""

from __future__ import annotations

import asyncio

from nu.core.arithmetic import (
    AbsQuery,
    AddQuery,
    DivModQuery,
    DivQuery,
    FloorDivQuery,
    ModQuery,
    MulQuery,
    NegQuery,
    PosQuery,
    PowQuery,
    RoundQuery,
    SubQuery,
)
from nu.core.literal import LiteralQuery
from nu.lang import EMPTY, INVALID, Attr, compile
from nu.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- binary / variadic folds --------------------------------------------


def test_add_folds_its_operands():
    assert _eval(AddQuery(LiteralQuery(1), LiteralQuery(2), LiteralQuery(3))) == 6


def test_mul_folds_its_operands():
    assert _eval(MulQuery(LiteralQuery(2), LiteralQuery(3), LiteralQuery(4))) == 24


def test_sub_subtracts():
    assert _eval(SubQuery(LiteralQuery(10), LiteralQuery(3))) == 7


def test_div_is_true_division():
    assert _eval(DivQuery(LiteralQuery(7), LiteralQuery(2))) == 3.5


def test_floordiv_floors():
    assert _eval(FloorDivQuery(LiteralQuery(7), LiteralQuery(2))) == 3


def test_mod_takes_the_remainder():
    assert _eval(ModQuery(LiteralQuery(7), LiteralQuery(3))) == 1


def test_pow_raises():
    assert _eval(PowQuery(LiteralQuery(2), LiteralQuery(10))) == 1024


# --- unary ---------------------------------------------------------------


def test_neg_negates():
    assert _eval(NegQuery(LiteralQuery(5))) == -5


def test_pos_keeps_sign():
    assert _eval(PosQuery(LiteralQuery(-5))) == -5
    assert _eval(PosQuery(LiteralQuery(5))) == 5


def test_abs_takes_magnitude():
    assert _eval(AbsQuery(LiteralQuery(-5))) == 5
    assert _eval(AbsQuery(LiteralQuery(5))) == 5


# --- divmod / round ------------------------------------------------------


def test_divmod_yields_the_pair():
    assert _eval(DivModQuery(LiteralQuery(17), LiteralQuery(5))) == (3, 2)


def test_round_with_one_operand():
    assert _eval(RoundQuery(LiteralQuery(3.14159))) == 3


def test_round_with_ndigits():
    assert _eval(RoundQuery(LiteralQuery(3.14159), LiteralQuery(2))) == 3.14


# --- nesting -------------------------------------------------------------


def test_nested_arithmetic():
    program = AddQuery(MulQuery(LiteralQuery(2), LiteralQuery(3)), NegQuery(LiteralQuery(1)))
    assert _eval(program) == 5


# --- algebra -------------------------------------------------------------


def test_add_and_mul_declare_their_algebra():
    program = compile(AddQuery(LiteralQuery(1), LiteralQuery(2)))
    assert program.attr(program.root, Attr.COMMUTATIVE) is True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is True
    program = compile(MulQuery(LiteralQuery(2), LiteralQuery(3)))
    assert program.attr(program.root, Attr.COMMUTATIVE) is True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is True


def test_sub_is_neither_commutative_nor_associative():
    program = compile(SubQuery(LiteralQuery(1), LiteralQuery(2)))
    assert program.attr(program.root, Attr.COMMUTATIVE) is not True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is not True


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(AddQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(MulQuery(LiteralQuery(2), LiteralQuery(INVALID))) is INVALID
    assert _eval(SubQuery(LiteralQuery(1), LiteralQuery(EMPTY))) is INVALID
    assert _eval(NegQuery(LiteralQuery(INVALID))) is INVALID
    assert _eval(DivModQuery(LiteralQuery(EMPTY), LiteralQuery(2))) is INVALID
    assert _eval(RoundQuery(LiteralQuery(1.5), LiteralQuery(EMPTY))) is INVALID


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(AddQuery(LiteralQuery(2), LiteralQuery(3)))) == 5
    assert asyncio.run(_aeval(PowQuery(LiteralQuery(2), LiteralQuery(5)))) == 32
    assert asyncio.run(_aeval(AbsQuery(LiteralQuery(-4)))) == 4
    assert asyncio.run(_aeval(DivModQuery(LiteralQuery(17), LiteralQuery(5)))) == (3, 2)
    assert asyncio.run(_aeval(RoundQuery(LiteralQuery(3.14159), LiteralQuery(2)))) == 3.14
    assert asyncio.run(_aeval(MulQuery(LiteralQuery(2), LiteralQuery(EMPTY)))) is INVALID
