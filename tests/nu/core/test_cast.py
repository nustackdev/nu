"""Tests for the cast atoms in nu.core.cast.

The scalar casts (ToInt, ToFloat, ToComplex, ToStr, ToBytes, ToByteArray) are pure
ScalarQueries with compile / acompile thunks, so they are driven end to end:
compile the term, evaluate, check the value, including the optional second
operand and sentinel propagation, with the async siblings mirroring the sync
path. The collection constructors (ToList, ToTuple, ToSet, ToFrozenSet, ToDict) apply the
Python constructor to an iterable operand value, so they are driven end to end
too; draining a stream into a container is a Reduction's job, not theirs.
"""

from __future__ import annotations

import asyncio

from nu.core.cast import (
    ToByteArray,
    ToBytes,
    ToComplex,
    ToDict,
    ToFloat,
    ToFrozenSet,
    ToInt,
    ToList,
    ToSet,
    ToStr,
    ToTuple,
)
from nu.lang import EMPTY, INVALID, Attr, Cardinality, Sort
from nu.lang.helpers import aeval, compile, eval
from nu.lang.literal import Literal


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- scalar casts: single operand ----------------------------------------


def test_int_casts():
    assert _eval(ToInt(Literal("42"))) == 42
    assert _eval(ToInt(Literal(3.9))) == 3


def test_float_casts():
    assert _eval(ToFloat(Literal("3.5"))) == 3.5
    assert _eval(ToFloat(Literal(2))) == 2.0


def test_complex_casts():
    assert _eval(ToComplex(Literal("1+2j"))) == complex(1, 2)
    assert _eval(ToComplex(Literal(3))) == complex(3, 0)


def test_str_casts():
    assert _eval(ToStr(Literal(42))) == "42"


def test_bytes_casts():
    assert _eval(ToBytes(Literal(3))) == b"\x00\x00\x00"


def test_bytearray_casts():
    assert _eval(ToByteArray(Literal(2))) == bytearray(b"\x00\x00")


# --- scalar casts: optional second operand -------------------------------


def test_int_with_base():
    assert _eval(ToInt(Literal("ff"), Literal(16))) == 255
    assert _eval(ToInt(Literal("101"), Literal(2))) == 5


def test_complex_with_imaginary():
    assert _eval(ToComplex(Literal(1), Literal(2))) == complex(1, 2)


def test_bytes_with_encoding():
    assert _eval(ToBytes(Literal("hi"), Literal("utf-8"))) == b"hi"


def test_bytearray_with_encoding():
    assert _eval(ToByteArray(Literal("hi"), Literal("utf-8"))) == bytearray(b"hi")


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(ToInt(Literal(EMPTY))) is INVALID
    assert _eval(ToFloat(Literal(INVALID))) is INVALID
    assert _eval(ToStr(Literal(EMPTY))) is INVALID
    assert _eval(ToInt(Literal("ff"), Literal(EMPTY))) is INVALID
    assert _eval(ToComplex(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(ToBytes(Literal("hi"), Literal(INVALID))) is INVALID


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(ToInt(Literal("42")))) == 42
    assert asyncio.run(_aeval(ToFloat(Literal("3.5")))) == 3.5
    assert asyncio.run(_aeval(ToStr(Literal(7)))) == "7"
    assert asyncio.run(_aeval(ToInt(Literal("ff"), Literal(16)))) == 255
    assert asyncio.run(_aeval(ToComplex(Literal(1), Literal(2)))) == complex(1, 2)
    assert asyncio.run(_aeval(ToInt(Literal(EMPTY)))) is INVALID


# --- collection constructors ---------------------------------------------


def test_collection_constructors_are_scalar_queries():
    for ctor in (ToList, ToTuple, ToSet, ToFrozenSet, ToDict):
        program = compile(ctor(Literal(1)))
        assert program.attr(program.root, Attr.SORT) is Sort.SCALAR_QUERY
        assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR


def test_collection_constructors_build_their_containers():
    assert _eval(ToList(Literal((1, 2, 3)))) == [1, 2, 3]
    assert _eval(ToTuple(Literal([1, 2, 3]))) == (1, 2, 3)
    assert _eval(ToSet(Literal([1, 1, 2]))) == {1, 2}
    assert _eval(ToFrozenSet(Literal([1, 2]))) == frozenset({1, 2})
    assert _eval(ToDict(Literal([("a", 1), ("b", 2)]))) == {"a": 1, "b": 2}


def test_collection_constructor_propagates_a_sentinel():
    assert _eval(ToList(Literal(EMPTY))) is INVALID
    assert _eval(ToDict(Literal(INVALID))) is INVALID


def test_collection_aeval_mirrors_eval():
    assert asyncio.run(_aeval(ToList(Literal((1, 2))))) == [1, 2]
    assert asyncio.run(_aeval(ToSet(Literal([1, 1, 2])))) == {1, 2}
