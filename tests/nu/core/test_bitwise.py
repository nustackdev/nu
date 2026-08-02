"""Functional tests for the bitwise core atoms.

Compile real bitwise programs and check both the algebra the language assigns
(commutative / associative on AND / OR / XOR) and the pure-scalar execution
slice (sync + async), including sentinel collapse.
"""

from __future__ import annotations

import asyncio

from nu.core.bitwise import (
    BitAnd,
    BitNot,
    BitOr,
    BitXor,
    LShift,
    RShift,
)
from nu.core.literal import Literal
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
    for atom in (BitAnd, BitOr, BitXor):
        program = compile(atom(Literal(1), Literal(2)))
        assert program.attr(program.root, Attr.COMMUTATIVE) is True
        assert program.attr(program.root, Attr.ASSOCIATIVE) is True


def test_shifts_declare_no_algebra():
    for atom in (LShift, RShift):
        program = compile(atom(Literal(1), Literal(2)))
        assert program.attr(program.root, Attr.COMMUTATIVE) is False
        assert program.attr(program.root, Attr.ASSOCIATIVE) is False


# --- effects -------------------------------------------------------------


def test_bitwise_is_pure():
    program = compile(BitAnd(Literal(6), Literal(3)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


# --- execution: pure scalars --------------------------------------------


def test_bitand_folds_operands():
    assert _eval(BitAnd(Literal(0b110), Literal(0b011))) == 0b010
    assert _eval(BitAnd(Literal(0b111), Literal(0b110), Literal(0b100))) == 0b100
    # identity is -1 (all bits), so a lone operand passes through.
    assert _eval(BitAnd(Literal(5))) == 5


def test_bitor_folds_operands():
    assert _eval(BitOr(Literal(0b100), Literal(0b001))) == 0b101
    assert _eval(BitOr(Literal(0b001), Literal(0b010), Literal(0b100))) == 0b111
    assert _eval(BitOr(Literal(5))) == 5


def test_bitxor_folds_operands():
    assert _eval(BitXor(Literal(0b110), Literal(0b011))) == 0b101
    assert _eval(BitXor(Literal(0b111), Literal(0b001), Literal(0b010))) == 0b100
    assert _eval(BitXor(Literal(5))) == 5


def test_bitnot_negates_bits():
    assert _eval(BitNot(Literal(0))) == -1
    assert _eval(BitNot(Literal(5))) == -6


def test_shifts_move_bits():
    assert _eval(LShift(Literal(1), Literal(4))) == 16
    assert _eval(RShift(Literal(16), Literal(2))) == 4


def test_nested_bitwise():
    program = BitOr(
        BitAnd(Literal(0b110), Literal(0b011)),
        LShift(Literal(1), Literal(2)),
    )
    assert _eval(program) == 0b110


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(BitAnd(Literal(0b110), Literal(0b011)))) == 0b010
    assert asyncio.run(_aeval(BitNot(Literal(0)))) == -1
    assert asyncio.run(_aeval(LShift(Literal(1), Literal(4)))) == 16


# --- sentinels -----------------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(BitAnd(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(BitOr(Literal(1), Literal(INVALID))) is INVALID
    assert _eval(BitXor(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(BitNot(Literal(EMPTY))) is INVALID
    assert _eval(LShift(Literal(EMPTY), Literal(1))) is INVALID
    assert _eval(RShift(Literal(1), Literal(INVALID))) is INVALID
    assert asyncio.run(_aeval(BitAnd(Literal(1), Literal(EMPTY)))) is INVALID
