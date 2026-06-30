"""Execution tests for the logical atoms in ``nu.core.logical``.

Compile small programs over LiteralQuery leaves and check the value each logical
atom yields, the bool-coercing (non-short-circuit) semantics of And / Or,
and sentinel propagation to INVALID.
"""

from __future__ import annotations

import asyncio

from nu.core.literal import LiteralQuery
from nu.core.logical import AndQuery as And
from nu.core.logical import BoolQuery as Bool
from nu.core.logical import NotQuery as Not
from nu.core.logical import OrQuery as Or
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
    assert _eval(And(LiteralQuery(True), LiteralQuery(True))) is True
    assert _eval(And(LiteralQuery(True), LiteralQuery(False))) is False
    assert _eval(And(LiteralQuery(False), LiteralQuery(False))) is False


def test_and_is_variadic():
    assert _eval(And(LiteralQuery(True), LiteralQuery(True), LiteralQuery(True))) is True
    assert _eval(And(LiteralQuery(True), LiteralQuery(True), LiteralQuery(False))) is False


def test_and_coerces_to_bool_not_an_operand():
    # Python `1 and 2` is 2; Nu And yields a plain bool.
    assert _eval(And(LiteralQuery(1), LiteralQuery(2))) is True
    assert _eval(And(LiteralQuery(0), LiteralQuery(2))) is False


# --- Or ------------------------------------------------------------------


def test_or_disjoins():
    assert _eval(Or(LiteralQuery(False), LiteralQuery(True))) is True
    assert _eval(Or(LiteralQuery(False), LiteralQuery(False))) is False
    assert _eval(Or(LiteralQuery(True), LiteralQuery(True))) is True


def test_or_is_variadic():
    assert _eval(Or(LiteralQuery(False), LiteralQuery(False), LiteralQuery(True))) is True
    assert _eval(Or(LiteralQuery(False), LiteralQuery(False), LiteralQuery(False))) is False


def test_or_coerces_to_bool_not_an_operand():
    # Python `0 or 3` is 3; Nu Or yields a plain bool.
    assert _eval(Or(LiteralQuery(0), LiteralQuery(3))) is True
    assert _eval(Or(LiteralQuery(0), LiteralQuery(0))) is False


# --- Not -----------------------------------------------------------------


def test_not_negates():
    assert _eval(Not(LiteralQuery(False))) is True
    assert _eval(Not(LiteralQuery(True))) is False
    assert _eval(Not(LiteralQuery(0))) is True
    assert _eval(Not(LiteralQuery(7))) is False


# --- Bool ----------------------------------------------------------------


def test_bool_casts_truthiness():
    assert _eval(Bool(LiteralQuery(7))) is True
    assert _eval(Bool(LiteralQuery(0))) is False
    assert _eval(Bool(LiteralQuery(""))) is False
    assert _eval(Bool(LiteralQuery("x"))) is True


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(And(LiteralQuery(True), LiteralQuery(True)))) is True
    assert asyncio.run(_aeval(Or(LiteralQuery(False), LiteralQuery(True)))) is True
    assert asyncio.run(_aeval(Not(LiteralQuery(False)))) is True
    assert asyncio.run(_aeval(Bool(LiteralQuery(7)))) is True


# --- sentinel propagation ------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(And(LiteralQuery(True), LiteralQuery(EMPTY))) is INVALID
    assert _eval(Or(LiteralQuery(False), LiteralQuery(INVALID))) is INVALID
    assert _eval(Not(LiteralQuery(EMPTY))) is INVALID
    assert _eval(Bool(LiteralQuery(INVALID))) is INVALID
    assert asyncio.run(_aeval(And(LiteralQuery(EMPTY), LiteralQuery(True)))) is INVALID
