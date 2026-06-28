"""Execution tests for the comparison atoms.

Compile pure comparison programs over LiteralQuery operands and check the bool
they yield, sync and async, plus sentinel propagation. Mirrors the pure-leaf
slice of ``test_core.test_logic_comparisons``.
"""

from __future__ import annotations

import asyncio

from nu2.core.comparison import EqQuery, GeQuery, GtQuery, IsQuery, LeQuery, LtQuery, NeQuery
from nu2.core.literal import LiteralQuery
from nu2.lang import EMPTY, INVALID, Attr, compile
from nu2.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


def test_eq_and_ne():
    assert _eval(EqQuery(LiteralQuery(2), LiteralQuery(2))) is True
    assert _eval(EqQuery(LiteralQuery(2), LiteralQuery(3))) is False
    assert _eval(NeQuery(LiteralQuery(2), LiteralQuery(3))) is True
    assert _eval(NeQuery(LiteralQuery(2), LiteralQuery(2))) is False


def test_orderings():
    assert _eval(LtQuery(LiteralQuery(1), LiteralQuery(2))) is True
    assert _eval(LtQuery(LiteralQuery(2), LiteralQuery(1))) is False
    assert _eval(GtQuery(LiteralQuery(2), LiteralQuery(1))) is True
    assert _eval(GtQuery(LiteralQuery(1), LiteralQuery(2))) is False
    assert _eval(LeQuery(LiteralQuery(2), LiteralQuery(2))) is True
    assert _eval(LeQuery(LiteralQuery(3), LiteralQuery(2))) is False
    assert _eval(GeQuery(LiteralQuery(2), LiteralQuery(2))) is True
    assert _eval(GeQuery(LiteralQuery(1), LiteralQuery(2))) is False


def test_identity():
    obj = object()
    assert _eval(IsQuery(LiteralQuery(obj), LiteralQuery(obj))) is True
    assert _eval(IsQuery(LiteralQuery(object()), LiteralQuery(object()))) is False


def test_commutativity_is_declared():
    for kind in (EqQuery, NeQuery, IsQuery):
        program = compile(kind(LiteralQuery(1), LiteralQuery(2)))
        assert program.attr(program.root, Attr.COMMUTATIVE) is True
    for kind in (LtQuery, GtQuery, LeQuery, GeQuery):
        program = compile(kind(LiteralQuery(1), LiteralQuery(2)))
        assert program.attr(program.root, Attr.COMMUTATIVE) is not True


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(EqQuery(LiteralQuery(2), LiteralQuery(2)))) is True
    assert asyncio.run(_aeval(LtQuery(LiteralQuery(1), LiteralQuery(2)))) is True
    assert asyncio.run(_aeval(GeQuery(LiteralQuery(2), LiteralQuery(1)))) is True


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(EqQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(LtQuery(LiteralQuery(1), LiteralQuery(INVALID))) is INVALID
    assert asyncio.run(_aeval(GtQuery(LiteralQuery(EMPTY), LiteralQuery(1)))) is INVALID
