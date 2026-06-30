"""Functional tests for the bitwise core atoms.

Compile real bitwise programs and check both the algebra the language assigns
(commutative / associative on AND / OR / XOR) and the pure-scalar execution
slice (sync + async), including sentinel collapse.
"""

from __future__ import annotations

import asyncio

from nu.core.bitwise import (
    BitAndQuery,
    BitNotQuery,
    BitOrQuery,
    BitXorQuery,
    LShiftQuery,
    RShiftQuery,
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


# --- algebra -------------------------------------------------------------


def test_logical_bitops_declare_their_algebra():
    for atom in (BitAndQuery, BitOrQuery, BitXorQuery):
        program = compile(atom(LiteralQuery(1), LiteralQuery(2)))
        assert program.attr(program.root, Attr.COMMUTATIVE) is True
        assert program.attr(program.root, Attr.ASSOCIATIVE) is True


def test_shifts_declare_no_algebra():
    for atom in (LShiftQuery, RShiftQuery):
        program = compile(atom(LiteralQuery(1), LiteralQuery(2)))
        assert program.attr(program.root, Attr.COMMUTATIVE) is False
        assert program.attr(program.root, Attr.ASSOCIATIVE) is False


# --- effects -------------------------------------------------------------


def test_bitwise_is_pure():
    program = compile(BitAndQuery(LiteralQuery(6), LiteralQuery(3)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


# --- execution: pure scalars --------------------------------------------


def test_bitand_folds_operands():
    assert _eval(BitAndQuery(LiteralQuery(0b110), LiteralQuery(0b011))) == 0b010
    assert (
        _eval(BitAndQuery(LiteralQuery(0b111), LiteralQuery(0b110), LiteralQuery(0b100))) == 0b100
    )
    # identity is -1 (all bits), so a lone operand passes through.
    assert _eval(BitAndQuery(LiteralQuery(5))) == 5


def test_bitor_folds_operands():
    assert _eval(BitOrQuery(LiteralQuery(0b100), LiteralQuery(0b001))) == 0b101
    assert _eval(BitOrQuery(LiteralQuery(0b001), LiteralQuery(0b010), LiteralQuery(0b100))) == 0b111
    assert _eval(BitOrQuery(LiteralQuery(5))) == 5


def test_bitxor_folds_operands():
    assert _eval(BitXorQuery(LiteralQuery(0b110), LiteralQuery(0b011))) == 0b101
    assert (
        _eval(BitXorQuery(LiteralQuery(0b111), LiteralQuery(0b001), LiteralQuery(0b010))) == 0b100
    )
    assert _eval(BitXorQuery(LiteralQuery(5))) == 5


def test_bitnot_negates_bits():
    assert _eval(BitNotQuery(LiteralQuery(0))) == -1
    assert _eval(BitNotQuery(LiteralQuery(5))) == -6


def test_shifts_move_bits():
    assert _eval(LShiftQuery(LiteralQuery(1), LiteralQuery(4))) == 16
    assert _eval(RShiftQuery(LiteralQuery(16), LiteralQuery(2))) == 4


def test_nested_bitwise():
    program = BitOrQuery(
        BitAndQuery(LiteralQuery(0b110), LiteralQuery(0b011)),
        LShiftQuery(LiteralQuery(1), LiteralQuery(2)),
    )
    assert _eval(program) == 0b110


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(BitAndQuery(LiteralQuery(0b110), LiteralQuery(0b011)))) == 0b010
    assert asyncio.run(_aeval(BitNotQuery(LiteralQuery(0)))) == -1
    assert asyncio.run(_aeval(LShiftQuery(LiteralQuery(1), LiteralQuery(4)))) == 16


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(BitAndQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(BitOrQuery(LiteralQuery(1), LiteralQuery(INVALID))) is INVALID
    assert _eval(BitXorQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(BitNotQuery(LiteralQuery(EMPTY))) is INVALID
    assert _eval(LShiftQuery(LiteralQuery(EMPTY), LiteralQuery(1))) is INVALID
    assert _eval(RShiftQuery(LiteralQuery(1), LiteralQuery(INVALID))) is INVALID
    assert asyncio.run(_aeval(BitAndQuery(LiteralQuery(1), LiteralQuery(EMPTY)))) is INVALID
