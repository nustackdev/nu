"""Tests for the cast atoms in nu2.core.cast.

The scalar casts (IntQuery, FloatQuery, ComplexQuery, StrQuery, BytesQuery, ByteArrayQuery) are pure
ScalarQueries with compile / acompile thunks, so they are driven end to end:
compile the term, evaluate, check the value, including the optional second
operand and sentinel propagation, with the async siblings mirroring the sync
path. The collection constructors (ListQuery, TupleQuery, SetQuery, FrozenSetQuery, DictQuery) apply the
Python constructor to an iterable operand value, so they are driven end to end
too; draining a stream into a container is a Reduction's job, not theirs.
"""

from __future__ import annotations

import asyncio

from nu2.core.cast import (
    ByteArrayQuery,
    BytesQuery,
    ComplexQuery,
    DictQuery,
    FloatQuery,
    FrozenSetQuery,
    IntQuery,
    ListQuery,
    SetQuery,
    StrQuery,
    TupleQuery,
)
from nu2.core.literal import LiteralQuery
from nu2.lang import EMPTY, INVALID, Attr, Cardinality, Sort, compile
from nu2.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- scalar casts: single operand ----------------------------------------


def test_int_casts():
    assert _eval(IntQuery(LiteralQuery("42"))) == 42
    assert _eval(IntQuery(LiteralQuery(3.9))) == 3


def test_float_casts():
    assert _eval(FloatQuery(LiteralQuery("3.5"))) == 3.5
    assert _eval(FloatQuery(LiteralQuery(2))) == 2.0


def test_complex_casts():
    assert _eval(ComplexQuery(LiteralQuery("1+2j"))) == complex(1, 2)
    assert _eval(ComplexQuery(LiteralQuery(3))) == complex(3, 0)


def test_str_casts():
    assert _eval(StrQuery(LiteralQuery(42))) == "42"


def test_bytes_casts():
    assert _eval(BytesQuery(LiteralQuery(3))) == b"\x00\x00\x00"


def test_bytearray_casts():
    assert _eval(ByteArrayQuery(LiteralQuery(2))) == bytearray(b"\x00\x00")


# --- scalar casts: optional second operand -------------------------------


def test_int_with_base():
    assert _eval(IntQuery(LiteralQuery("ff"), LiteralQuery(16))) == 255
    assert _eval(IntQuery(LiteralQuery("101"), LiteralQuery(2))) == 5


def test_complex_with_imaginary():
    assert _eval(ComplexQuery(LiteralQuery(1), LiteralQuery(2))) == complex(1, 2)


def test_bytes_with_encoding():
    assert _eval(BytesQuery(LiteralQuery("hi"), LiteralQuery("utf-8"))) == b"hi"


def test_bytearray_with_encoding():
    assert _eval(ByteArrayQuery(LiteralQuery("hi"), LiteralQuery("utf-8"))) == bytearray(b"hi")


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(IntQuery(LiteralQuery(EMPTY))) is INVALID
    assert _eval(FloatQuery(LiteralQuery(INVALID))) is INVALID
    assert _eval(StrQuery(LiteralQuery(EMPTY))) is INVALID
    assert _eval(IntQuery(LiteralQuery("ff"), LiteralQuery(EMPTY))) is INVALID
    assert _eval(ComplexQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(BytesQuery(LiteralQuery("hi"), LiteralQuery(INVALID))) is INVALID


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(IntQuery(LiteralQuery("42")))) == 42
    assert asyncio.run(_aeval(FloatQuery(LiteralQuery("3.5")))) == 3.5
    assert asyncio.run(_aeval(StrQuery(LiteralQuery(7)))) == "7"
    assert asyncio.run(_aeval(IntQuery(LiteralQuery("ff"), LiteralQuery(16)))) == 255
    assert asyncio.run(_aeval(ComplexQuery(LiteralQuery(1), LiteralQuery(2)))) == complex(1, 2)
    assert asyncio.run(_aeval(IntQuery(LiteralQuery(EMPTY)))) is INVALID


# --- collection constructors ---------------------------------------------


def test_collection_constructors_are_scalar_queries():
    for ctor in (ListQuery, TupleQuery, SetQuery, FrozenSetQuery, DictQuery):
        program = compile(ctor(LiteralQuery(1)))
        assert program.attr(program.root, Attr.SORT) is Sort.SCALAR_QUERY
        assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR


def test_collection_constructors_build_their_containers():
    assert _eval(ListQuery(LiteralQuery((1, 2, 3)))) == [1, 2, 3]
    assert _eval(TupleQuery(LiteralQuery([1, 2, 3]))) == (1, 2, 3)
    assert _eval(SetQuery(LiteralQuery([1, 1, 2]))) == {1, 2}
    assert _eval(FrozenSetQuery(LiteralQuery([1, 2]))) == frozenset({1, 2})
    assert _eval(DictQuery(LiteralQuery([("a", 1), ("b", 2)]))) == {"a": 1, "b": 2}


def test_collection_constructor_propagates_a_sentinel():
    assert _eval(ListQuery(LiteralQuery(EMPTY))) is INVALID
    assert _eval(DictQuery(LiteralQuery(INVALID))) is INVALID


def test_collection_aeval_mirrors_eval():
    assert asyncio.run(_aeval(ListQuery(LiteralQuery((1, 2))))) == [1, 2]
    assert asyncio.run(_aeval(SetQuery(LiteralQuery([1, 1, 2])))) == {1, 2}
