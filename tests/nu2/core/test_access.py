"""Tests for the access atoms (item / attribute member access).

Reads (GetItem, Len, Contains, Slice, GetAttr, HasAttr) are evaluable
ScalarQueries: evaluate them and check the value, plus sentinel propagation.
Writes (SetItem, DelItem, SetAttr, DelAttr) are structural Commands: check the
effect attribution and law verdicts, not evaluation (their runtime is pending
the fabric write path).
"""

from __future__ import annotations

import asyncio

from nu2.core.access import (
    Contains,
    DelAttr,
    DelItem,
    GetAttr,
    GetItem,
    HasAttr,
    Len,
    SetAttr,
    SetItem,
    Slice,
)
from nu2.core.literal import Literal
from nu2.lang import EMPTY, INVALID, LAWS, Attr, Effect, Ref, compile, gate, validate
from nu2.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- reads: evaluation ---------------------------------------------------


def test_get_item_indexes_its_target():
    assert _eval(GetItem(Literal([10, 20, 30]), Literal(1))) == 20
    assert _eval(GetItem(Literal({"a": 1, "b": 2}), Literal("b"))) == 2


def test_len_counts_its_child():
    assert _eval(Len(Literal([1, 2, 3]))) == 3
    assert _eval(Len(Literal("abcd"))) == 4


def test_contains_checks_membership():
    assert _eval(Contains(Literal([1, 2, 3]), Literal(2))) is True
    assert _eval(Contains(Literal([1, 2, 3]), Literal(9))) is False


def test_slice_builds_a_slice_object():
    s = _eval(Slice(Literal(1), Literal(3), Literal(None)))
    assert s == slice(1, 3, None)
    assert _eval(
        GetItem(Literal([0, 1, 2, 3, 4]), Slice(Literal(1), Literal(3), Literal(None)))
    ) == [1, 2]


def test_get_attr_reads_an_attribute():
    assert _eval(GetAttr(Literal(1j), Literal("imag"))) == 1.0


def test_get_attr_falls_back_to_default():
    assert _eval(GetAttr(Literal(object()), Literal("nope"), Literal("fallback"))) == "fallback"


def test_has_attr_checks_presence():
    assert _eval(HasAttr(Literal(1j), Literal("imag"))) is True
    assert _eval(HasAttr(Literal(object()), Literal("nope"))) is False


def test_async_reads_mirror_sync():
    assert asyncio.run(_aeval(GetItem(Literal([10, 20]), Literal(0)))) == 10
    assert asyncio.run(_aeval(Len(Literal([1, 2])))) == 2
    assert asyncio.run(_aeval(Contains(Literal([1, 2]), Literal(1)))) is True


# --- reads: sentinel propagation -----------------------------------------


def test_a_sentinel_operand_collapses_a_read_to_invalid():
    assert _eval(GetItem(Literal(EMPTY), Literal(0))) is INVALID
    assert _eval(GetItem(Literal([1, 2]), Literal(INVALID))) is INVALID
    assert _eval(Len(Literal(EMPTY))) is INVALID
    assert _eval(Contains(Literal(INVALID), Literal(1))) is INVALID
    assert _eval(GetAttr(Literal(EMPTY), Literal("x"))) is INVALID
    assert _eval(HasAttr(Literal(1j), Literal(EMPTY))) is INVALID
    assert _eval(Slice(Literal(EMPTY), Literal(1), Literal(1))) is INVALID


# --- writes: effects and laws --------------------------------------------


def test_set_item_tracks_a_write_and_a_read():
    program = compile(SetItem(Ref("grid"), Literal("k"), Ref("v")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("grid", Effect.WRITE), ("v", Effect.READ)}
    )


def test_del_item_tracks_a_write():
    program = compile(DelItem(Ref("grid"), Literal("k")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("grid", Effect.WRITE)}
    )


def test_set_attr_tracks_a_write_and_a_read():
    program = compile(SetAttr(Ref("obj"), Literal("field"), Ref("val")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("obj", Effect.WRITE), ("val", Effect.READ)}
    )


def test_del_attr_tracks_a_write():
    program = compile(DelAttr(Ref("obj"), Literal("field")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("obj", Effect.WRITE)}
    )


def test_a_clean_write_validates():
    program = compile(SetItem(Ref("grid"), Literal("k"), Literal(1)))
    assert validate(program, *LAWS) is program


def test_a_write_in_a_query_slot_is_refused():
    verdict = gate(compile(Len(SetItem(Ref("g"), Literal("k"), Literal(1)))), *LAWS)
    assert any(v.law == "composition" for v in verdict)
