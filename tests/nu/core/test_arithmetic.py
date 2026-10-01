"""Execution tests for the arithmetic atoms in nu.core.arithmetic.

Each atom is a pure ScalarQuery that computes from its operand values, so it
carries compile / acompile thunks and is exercised end to end: compile the
term, drive it, check the value. EMPTY propagation (an EMPTY operand
collapses the result to EMPTY) is checked alongside, and the async siblings are
asserted to mirror the sync hot path.
"""

from __future__ import annotations

import asyncio

from nu.core.arithmetic import (
    Abs,
    Add,
    Div,
    DivMod,
    FloorDiv,
    Mod,
    Mul,
    Neg,
    Pos,
    Pow,
    Round,
    Sub,
)
from nu.lang import EMPTY
from nu.lang.helpers import aeval, compile, eval
from nu.lang.literal import Literal


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- binary / variadic folds --------------------------------------------


def test_add_folds_its_operands():
    assert _eval(Add(Literal(1), Literal(2), Literal(3))) == 6


def test_mul_folds_its_operands():
    assert _eval(Mul(Literal(2), Literal(3), Literal(4))) == 24


def test_sub_subtracts():
    assert _eval(Sub(Literal(10), Literal(3))) == 7


def test_div_is_true_division():
    assert _eval(Div(Literal(7), Literal(2))) == 3.5


def test_floordiv_floors():
    assert _eval(FloorDiv(Literal(7), Literal(2))) == 3


def test_mod_takes_the_remainder():
    assert _eval(Mod(Literal(7), Literal(3))) == 1


def test_pow_raises():
    assert _eval(Pow(Literal(2), Literal(10))) == 1024


# --- unary ---------------------------------------------------------------


def test_neg_negates():
    assert _eval(Neg(Literal(5))) == -5


def test_pos_keeps_sign():
    assert _eval(Pos(Literal(-5))) == -5
    assert _eval(Pos(Literal(5))) == 5


def test_abs_takes_magnitude():
    assert _eval(Abs(Literal(-5))) == 5
    assert _eval(Abs(Literal(5))) == 5


# --- divmod / round ------------------------------------------------------


def test_divmod_yields_the_pair():
    assert _eval(DivMod(Literal(17), Literal(5))) == (3, 2)


def test_round_with_one_operand():
    assert _eval(Round(Literal(3.14159))) == 3


def test_round_with_ndigits():
    assert _eval(Round(Literal(3.14159), Literal(2))) == 3.14


# --- nesting -------------------------------------------------------------


def test_nested_arithmetic():
    program = Add(Mul(Literal(2), Literal(3)), Neg(Literal(1)))
    assert _eval(program) == 5


# --- sentinels -----------------------------------------------------------


def test_an_empty_operand_collapses_to_empty():
    assert _eval(Add(Literal(EMPTY), Literal(1))) is EMPTY
    assert _eval(Mul(Literal(2), Literal(EMPTY))) is EMPTY
    assert _eval(Sub(Literal(1), Literal(EMPTY))) is EMPTY
    assert _eval(Neg(Literal(EMPTY))) is EMPTY
    assert _eval(DivMod(Literal(EMPTY), Literal(2))) is EMPTY
    assert _eval(Round(Literal(1.5), Literal(EMPTY))) is EMPTY


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Add(Literal(2), Literal(3)))) == 5
    assert asyncio.run(_aeval(Pow(Literal(2), Literal(5)))) == 32
    assert asyncio.run(_aeval(Abs(Literal(-4)))) == 4
    assert asyncio.run(_aeval(DivMod(Literal(17), Literal(5)))) == (3, 2)
    assert asyncio.run(_aeval(Round(Literal(3.14159), Literal(2)))) == 3.14
    assert asyncio.run(_aeval(Mul(Literal(2), Literal(EMPTY)))) is EMPTY
