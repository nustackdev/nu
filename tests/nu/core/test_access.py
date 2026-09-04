"""Tests for the access atoms (item / attribute member access).

Every atom is an evaluable ScalarQuery: reads (GetItem, Len, Contains, Slice,
GetAttr, HasAttr) yield the member; writes (SetItem, DelItem, SetAttr, DelAttr)
mutate the Python value in place and yield it back. All driven end to end -
value, sentinel propagation, async mirror. The writes are local Python mutation
off a value, not a fabric write (that is context.Set's job).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from nu.core.access import (
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
from nu.lang import EMPTY, INVALID
from nu.lang.helpers import aeval, compile, eval
from nu.lang.literal import Literal


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
        GetItem(
            Literal([0, 1, 2, 3, 4]),
            Slice(Literal(1), Literal(3), Literal(None)),
        )
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


# --- writes: evaluation --------------------------------------------------
# Commands mutate in place and return None (matching Python's ``x[k] = v``).


def test_set_item_mutates_dict_returns_none():
    grid = {"a": 1}
    out = _eval(SetItem(Literal(grid), Literal("b"), Literal(2)))
    assert out is None
    assert grid == {"a": 1, "b": 2}


def test_del_item_removes_key_returns_none():
    grid = {"a": 1, "b": 2}
    out = _eval(DelItem(Literal(grid), Literal("a")))
    assert out is None
    assert grid == {"b": 2}


def test_set_attr_mutates_object_returns_none():
    obj = SimpleNamespace(x=1)
    out = _eval(SetAttr(Literal(obj), Literal("y"), Literal(2)))
    assert out is None
    assert obj.y == 2


def test_del_attr_removes_attribute_returns_none():
    obj = SimpleNamespace(x=1, y=2)
    out = _eval(DelAttr(Literal(obj), Literal("y")))
    assert out is None
    assert not hasattr(obj, "y")


# --- writes: sentinel propagation ----------------------------------------
# A sentinel operand causes the command to bail early without mutation.


def test_a_sentinel_operand_skips_a_write():
    grid = {"a": 1}
    # EMPTY/INVALID container or key/value: bail, no mutation, return None
    assert _eval(SetItem(Literal(EMPTY), Literal("k"), Literal(1))) is None
    assert _eval(SetItem(Literal(grid), Literal("k"), Literal(INVALID))) is None
    assert _eval(DelItem(Literal(grid), Literal(EMPTY))) is None
    assert _eval(SetAttr(Literal(EMPTY), Literal("x"), Literal(1))) is None
    assert _eval(DelAttr(Literal(INVALID), Literal("x"))) is None
    # A refused write leaves the value untouched.
    assert grid == {"a": 1}


# --- writes: async mirrors sync ------------------------------------------


def test_async_writes_mirror_sync():
    grid = {"a": 1}
    assert asyncio.run(_aeval(SetItem(Literal(grid), Literal("b"), Literal(2)))) is None
    assert grid == {"a": 1, "b": 2}
    obj = SimpleNamespace()
    assert asyncio.run(_aeval(SetAttr(Literal(obj), Literal("z"), Literal(9)))) is None
    assert obj.z == 9
