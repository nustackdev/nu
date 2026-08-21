"""Execution tests for the comparison atoms.

Compile pure comparison programs over Literal operands and check the bool
they yield, sync and async, plus sentinel propagation. Mirrors the pure-leaf
slice of ``test_core.test_logic_comparisons``.
"""

from __future__ import annotations

import asyncio

from nu.core.comparison import Eq, Ge, Gt, Is, Le, Lt, Ne
from nu.core.literal import Literal
from nu.lang import EMPTY, INVALID, compile
from nu.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


def test_eq_and_ne():
    assert _eval(Eq(Literal(2), Literal(2))) is True
    assert _eval(Eq(Literal(2), Literal(3))) is False
    assert _eval(Ne(Literal(2), Literal(3))) is True
    assert _eval(Ne(Literal(2), Literal(2))) is False


def test_orderings():
    assert _eval(Lt(Literal(1), Literal(2))) is True
    assert _eval(Lt(Literal(2), Literal(1))) is False
    assert _eval(Gt(Literal(2), Literal(1))) is True
    assert _eval(Gt(Literal(1), Literal(2))) is False
    assert _eval(Le(Literal(2), Literal(2))) is True
    assert _eval(Le(Literal(3), Literal(2))) is False
    assert _eval(Ge(Literal(2), Literal(2))) is True
    assert _eval(Ge(Literal(1), Literal(2))) is False


def test_identity():
    obj = object()
    assert _eval(Is(Literal(obj), Literal(obj))) is True
    assert _eval(Is(Literal(object()), Literal(object()))) is False


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Eq(Literal(2), Literal(2)))) is True
    assert asyncio.run(_aeval(Lt(Literal(1), Literal(2)))) is True
    assert asyncio.run(_aeval(Ge(Literal(2), Literal(1)))) is True


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(Eq(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(Lt(Literal(1), Literal(INVALID))) is INVALID
    assert asyncio.run(_aeval(Gt(Literal(EMPTY), Literal(1)))) is INVALID
