"""Execution tests for the logical atoms in ``nu.core.logical``.

Compile small programs over Literal leaves and check the value each logical
atom yields, the bool-coercing (non-short-circuit) semantics of And / Or,
and sentinel propagation to INVALID.
"""

from __future__ import annotations

import asyncio

from nu.core.literal import Literal
from nu.core.logical import And as And
from nu.core.logical import Not as Not
from nu.core.logical import Or as Or
from nu.core.logical import ToBool as Bool
from nu.lang import EMPTY, INVALID, compile
from nu.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- And -----------------------------------------------------------------


def test_and_conjoins():
    assert _eval(And(Literal(True), Literal(True))) is True
    assert _eval(And(Literal(True), Literal(False))) is False
    assert _eval(And(Literal(False), Literal(False))) is False


def test_and_is_variadic():
    assert _eval(And(Literal(True), Literal(True), Literal(True))) is True
    assert _eval(And(Literal(True), Literal(True), Literal(False))) is False


def test_and_coerces_to_bool_not_an_operand():
    # Python `1 and 2` is 2; Nu And yields a plain bool.
    assert _eval(And(Literal(1), Literal(2))) is True
    assert _eval(And(Literal(0), Literal(2))) is False


# --- Or ------------------------------------------------------------------


def test_or_disjoins():
    assert _eval(Or(Literal(False), Literal(True))) is True
    assert _eval(Or(Literal(False), Literal(False))) is False
    assert _eval(Or(Literal(True), Literal(True))) is True


def test_or_is_variadic():
    assert _eval(Or(Literal(False), Literal(False), Literal(True))) is True
    assert _eval(Or(Literal(False), Literal(False), Literal(False))) is False


def test_or_coerces_to_bool_not_an_operand():
    # Python `0 or 3` is 3; Nu Or yields a plain bool.
    assert _eval(Or(Literal(0), Literal(3))) is True
    assert _eval(Or(Literal(0), Literal(0))) is False


# --- Not -----------------------------------------------------------------


def test_not_negates():
    assert _eval(Not(Literal(False))) is True
    assert _eval(Not(Literal(True))) is False
    assert _eval(Not(Literal(0))) is True
    assert _eval(Not(Literal(7))) is False


# --- Bool ----------------------------------------------------------------


def test_bool_casts_truthiness():
    assert _eval(Bool(Literal(7))) is True
    assert _eval(Bool(Literal(0))) is False
    assert _eval(Bool(Literal(""))) is False
    assert _eval(Bool(Literal("x"))) is True


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(And(Literal(True), Literal(True)))) is True
    assert asyncio.run(_aeval(Or(Literal(False), Literal(True)))) is True
    assert asyncio.run(_aeval(Not(Literal(False)))) is True
    assert asyncio.run(_aeval(Bool(Literal(7)))) is True


# --- sentinel propagation ------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(And(Literal(True), Literal(EMPTY))) is INVALID
    assert _eval(Or(Literal(False), Literal(INVALID))) is INVALID
    assert _eval(Not(Literal(EMPTY))) is INVALID
    assert _eval(Bool(Literal(INVALID))) is INVALID
    assert asyncio.run(_aeval(And(Literal(EMPTY), Literal(True)))) is INVALID
