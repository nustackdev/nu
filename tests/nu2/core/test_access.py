"""Tests for the access atoms (item / attribute member access).

Every atom is an evaluable ScalarQuery: reads (GetItemQuery, LenQuery, ContainsQuery, SliceQuery,
GetAttrQuery, HasAttrQuery) yield the member; writes (SetItemCommand, DelItemCommand, SetAttrCommand, DelAttrCommand)
mutate the Python value in place and yield it back. All driven end to end -
value, sentinel propagation, async mirror. The writes are local Python mutation
off a value, not a fabric write (that is context.Set's job).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from nu2.core.access import (
    ContainsQuery,
    DelAttrCommand,
    DelItemCommand,
    GetAttrQuery,
    GetItemQuery,
    HasAttrQuery,
    LenQuery,
    SetAttrCommand,
    SetItemCommand,
    SliceQuery,
)
from nu2.core.literal import LiteralQuery
from nu2.lang import EMPTY, INVALID, compile
from nu2.lang.helpers import aeval, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- reads: evaluation ---------------------------------------------------


def test_get_item_indexes_its_target():
    assert _eval(GetItemQuery(LiteralQuery([10, 20, 30]), LiteralQuery(1))) == 20
    assert _eval(GetItemQuery(LiteralQuery({"a": 1, "b": 2}), LiteralQuery("b"))) == 2


def test_len_counts_its_child():
    assert _eval(LenQuery(LiteralQuery([1, 2, 3]))) == 3
    assert _eval(LenQuery(LiteralQuery("abcd"))) == 4


def test_contains_checks_membership():
    assert _eval(ContainsQuery(LiteralQuery([1, 2, 3]), LiteralQuery(2))) is True
    assert _eval(ContainsQuery(LiteralQuery([1, 2, 3]), LiteralQuery(9))) is False


def test_slice_builds_a_slice_object():
    s = _eval(SliceQuery(LiteralQuery(1), LiteralQuery(3), LiteralQuery(None)))
    assert s == slice(1, 3, None)
    assert _eval(
        GetItemQuery(
            LiteralQuery([0, 1, 2, 3, 4]),
            SliceQuery(LiteralQuery(1), LiteralQuery(3), LiteralQuery(None)),
        )
    ) == [1, 2]


def test_get_attr_reads_an_attribute():
    assert _eval(GetAttrQuery(LiteralQuery(1j), LiteralQuery("imag"))) == 1.0


def test_get_attr_falls_back_to_default():
    assert (
        _eval(GetAttrQuery(LiteralQuery(object()), LiteralQuery("nope"), LiteralQuery("fallback")))
        == "fallback"
    )


def test_has_attr_checks_presence():
    assert _eval(HasAttrQuery(LiteralQuery(1j), LiteralQuery("imag"))) is True
    assert _eval(HasAttrQuery(LiteralQuery(object()), LiteralQuery("nope"))) is False


def test_async_reads_mirror_sync():
    assert asyncio.run(_aeval(GetItemQuery(LiteralQuery([10, 20]), LiteralQuery(0)))) == 10
    assert asyncio.run(_aeval(LenQuery(LiteralQuery([1, 2])))) == 2
    assert asyncio.run(_aeval(ContainsQuery(LiteralQuery([1, 2]), LiteralQuery(1)))) is True


# --- reads: sentinel propagation -----------------------------------------


def test_a_sentinel_operand_collapses_a_read_to_invalid():
    assert _eval(GetItemQuery(LiteralQuery(EMPTY), LiteralQuery(0))) is INVALID
    assert _eval(GetItemQuery(LiteralQuery([1, 2]), LiteralQuery(INVALID))) is INVALID
    assert _eval(LenQuery(LiteralQuery(EMPTY))) is INVALID
    assert _eval(ContainsQuery(LiteralQuery(INVALID), LiteralQuery(1))) is INVALID
    assert _eval(GetAttrQuery(LiteralQuery(EMPTY), LiteralQuery("x"))) is INVALID
    assert _eval(HasAttrQuery(LiteralQuery(1j), LiteralQuery(EMPTY))) is INVALID
    assert _eval(SliceQuery(LiteralQuery(EMPTY), LiteralQuery(1), LiteralQuery(1))) is INVALID


# --- writes: evaluation --------------------------------------------------
# Commands mutate in place and return None (matching Python's ``x[k] = v``).


def test_set_item_mutates_dict_returns_none():
    grid = {"a": 1}
    out = _eval(SetItemCommand(LiteralQuery(grid), LiteralQuery("b"), LiteralQuery(2)))
    assert out is None
    assert grid == {"a": 1, "b": 2}


def test_del_item_removes_key_returns_none():
    grid = {"a": 1, "b": 2}
    out = _eval(DelItemCommand(LiteralQuery(grid), LiteralQuery("a")))
    assert out is None
    assert grid == {"b": 2}


def test_set_attr_mutates_object_returns_none():
    obj = SimpleNamespace(x=1)
    out = _eval(SetAttrCommand(LiteralQuery(obj), LiteralQuery("y"), LiteralQuery(2)))
    assert out is None
    assert obj.y == 2


def test_del_attr_removes_attribute_returns_none():
    obj = SimpleNamespace(x=1, y=2)
    out = _eval(DelAttrCommand(LiteralQuery(obj), LiteralQuery("y")))
    assert out is None
    assert not hasattr(obj, "y")


# --- writes: sentinel propagation ----------------------------------------
# A sentinel operand causes the command to bail early without mutation.


def test_a_sentinel_operand_skips_a_write():
    grid = {"a": 1}
    # EMPTY/INVALID container or key/value: bail, no mutation, return None
    assert _eval(SetItemCommand(LiteralQuery(EMPTY), LiteralQuery("k"), LiteralQuery(1))) is None
    assert (
        _eval(SetItemCommand(LiteralQuery(grid), LiteralQuery("k"), LiteralQuery(INVALID))) is None
    )
    assert _eval(DelItemCommand(LiteralQuery(grid), LiteralQuery(EMPTY))) is None
    assert _eval(SetAttrCommand(LiteralQuery(EMPTY), LiteralQuery("x"), LiteralQuery(1))) is None
    assert _eval(DelAttrCommand(LiteralQuery(INVALID), LiteralQuery("x"))) is None
    # A refused write leaves the value untouched.
    assert grid == {"a": 1}


# --- writes: async mirrors sync ------------------------------------------


def test_async_writes_mirror_sync():
    grid = {"a": 1}
    assert (
        asyncio.run(_aeval(SetItemCommand(LiteralQuery(grid), LiteralQuery("b"), LiteralQuery(2))))
        is None
    )
    assert grid == {"a": 1, "b": 2}
    obj = SimpleNamespace()
    assert (
        asyncio.run(_aeval(SetAttrCommand(LiteralQuery(obj), LiteralQuery("z"), LiteralQuery(9))))
        is None
    )
    assert obj.z == 9
