"""Tests for the cast atoms in nu2.core.cast.

The scalar casts (Int, Float, Complex, Str, Bytes, ByteArray) are pure
ScalarQueries with compile / acompile thunks, so they are driven end to end:
compile the term, evaluate, check the value, including the optional second
operand and sentinel propagation, with the async siblings mirroring the sync
path. The collection constructors (List, Tuple, Set, FrozenSet, Dict) apply the
Python constructor to an iterable operand value, so they are driven end to end
too; draining a stream into a container is a Reduction's job, not theirs.
"""

from __future__ import annotations

import asyncio

from nu2.core.cast import (
    ByteArray,
    Bytes,
    Complex,
    Dict,
    Float,
    FrozenSet,
    Int,
    List,
    Set,
    Str,
    Tuple,
)
from nu2.core.literal import Literal
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
    assert _eval(Int(Literal("42"))) == 42
    assert _eval(Int(Literal(3.9))) == 3


def test_float_casts():
    assert _eval(Float(Literal("3.5"))) == 3.5
    assert _eval(Float(Literal(2))) == 2.0


def test_complex_casts():
    assert _eval(Complex(Literal("1+2j"))) == complex(1, 2)
    assert _eval(Complex(Literal(3))) == complex(3, 0)


def test_str_casts():
    assert _eval(Str(Literal(42))) == "42"


def test_bytes_casts():
    assert _eval(Bytes(Literal(3))) == b"\x00\x00\x00"


def test_bytearray_casts():
    assert _eval(ByteArray(Literal(2))) == bytearray(b"\x00\x00")


# --- scalar casts: optional second operand -------------------------------


def test_int_with_base():
    assert _eval(Int(Literal("ff"), Literal(16))) == 255
    assert _eval(Int(Literal("101"), Literal(2))) == 5


def test_complex_with_imaginary():
    assert _eval(Complex(Literal(1), Literal(2))) == complex(1, 2)


def test_bytes_with_encoding():
    assert _eval(Bytes(Literal("hi"), Literal("utf-8"))) == b"hi"


def test_bytearray_with_encoding():
    assert _eval(ByteArray(Literal("hi"), Literal("utf-8"))) == bytearray(b"hi")


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(Int(Literal(EMPTY))) is INVALID
    assert _eval(Float(Literal(INVALID))) is INVALID
    assert _eval(Str(Literal(EMPTY))) is INVALID
    assert _eval(Int(Literal("ff"), Literal(EMPTY))) is INVALID
    assert _eval(Complex(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(Bytes(Literal("hi"), Literal(INVALID))) is INVALID


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Int(Literal("42")))) == 42
    assert asyncio.run(_aeval(Float(Literal("3.5")))) == 3.5
    assert asyncio.run(_aeval(Str(Literal(7)))) == "7"
    assert asyncio.run(_aeval(Int(Literal("ff"), Literal(16)))) == 255
    assert asyncio.run(_aeval(Complex(Literal(1), Literal(2)))) == complex(1, 2)
    assert asyncio.run(_aeval(Int(Literal(EMPTY)))) is INVALID


# --- collection constructors ---------------------------------------------


def test_collection_constructors_are_scalar_queries():
    for ctor in (List, Tuple, Set, FrozenSet, Dict):
        program = compile(ctor(Literal(1)))
        assert program.attr(program.root, Attr.SORT) is Sort.SCALAR_QUERY
        assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR


def test_collection_constructors_build_their_containers():
    assert _eval(List(Literal((1, 2, 3)))) == [1, 2, 3]
    assert _eval(Tuple(Literal([1, 2, 3]))) == (1, 2, 3)
    assert _eval(Set(Literal([1, 1, 2]))) == {1, 2}
    assert _eval(FrozenSet(Literal([1, 2]))) == frozenset({1, 2})
    assert _eval(Dict(Literal([("a", 1), ("b", 2)]))) == {"a": 1, "b": 2}


def test_collection_constructor_propagates_a_sentinel():
    assert _eval(List(Literal(EMPTY))) is INVALID
    assert _eval(Dict(Literal(INVALID))) is INVALID


def test_collection_aeval_mirrors_eval():
    assert asyncio.run(_aeval(List(Literal((1, 2))))) == [1, 2]
    assert asyncio.run(_aeval(Set(Literal([1, 1, 2])))) == {1, 2}
