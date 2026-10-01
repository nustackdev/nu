"""Functional tests for the bitwise core atoms.

Compile real bitwise programs and check the pure-scalar execution slice (sync
+ async), including sentinel collapse.
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
from nu.lang import EMPTY, Attr
from nu.lang.helpers import aeval, compile, eval
from nu.lang.literal import Literal


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


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


# --- the fold keeps the operands' own meaning ----------------------------


def test_a_single_child_passes_through_unchanged():
    # The fold starts from the first child, not an int identity, so a lone
    # operand of any type comes back as itself.
    assert _eval(BitAnd(Literal({1, 2}))) == {1, 2}
    assert _eval(BitOr(Literal({"a": 1}))) == {"a": 1}
    assert _eval(BitXor(Literal(True))) is True


def test_no_children_yield_the_int_identity():
    assert _eval(BitAnd()) == -1
    assert _eval(BitOr()) == 0
    assert _eval(BitXor()) == 0


def test_bitxor_over_sets_is_symmetric_difference():
    assert _eval(BitXor(Literal({1, 2}), Literal({2, 3}))) == {1, 3}
    assert _eval(BitXor(Literal({1}), Literal({2}), Literal({1, 3}))) == {2, 3}


def test_bitor_over_dicts_merges():
    assert _eval(BitOr(Literal({"a": 1}), Literal({"a": 2, "b": 3}))) == {"a": 2, "b": 3}


def test_bitand_over_bools_stays_bool():
    assert _eval(BitAnd(Literal(True), Literal(False))) is False


def test_async_fold_keeps_non_int_operands():
    assert asyncio.run(_aeval(BitAnd(Literal({1, 2}), Literal({2, 3})))) == {2}
    assert asyncio.run(_aeval(BitOr(Literal({"a": 1}), Literal({"b": 2})))) == {"a": 1, "b": 2}
    assert asyncio.run(_aeval(BitXor(Literal({1, 2}), Literal({2, 3})))) == {1, 3}
    assert asyncio.run(_aeval(BitOr(Literal({1})))) == {1}
    assert asyncio.run(_aeval(BitXor())) == 0


# --- sentinels -----------------------------------------------------------


def test_an_empty_operand_collapses_to_empty():
    assert _eval(BitAnd(Literal(EMPTY), Literal(1))) is EMPTY
    assert _eval(BitOr(Literal(1), Literal(EMPTY))) is EMPTY
    assert _eval(BitXor(Literal(EMPTY), Literal(1))) is EMPTY
    assert _eval(BitNot(Literal(EMPTY))) is EMPTY
    assert _eval(LShift(Literal(EMPTY), Literal(1))) is EMPTY
    assert _eval(RShift(Literal(1), Literal(EMPTY))) is EMPTY
    assert asyncio.run(_aeval(BitAnd(Literal(1), Literal(EMPTY)))) is EMPTY
