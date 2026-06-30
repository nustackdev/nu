"""End-to-end smoke tests for the ported Forms layer.

Builds fluent Form programs, compiles them, and evaluates both sync and async,
asserting the value the underlying interaction should yield. Covers each form
family and exercises the real eval paths (the interaction thunks), not just
construction.
"""

from __future__ import annotations

from nu.core import LiteralQuery
from nu.forms import (
    BoolForm,
    BytesForm,
    DictForm,
    IntForm,
    ListForm,
    SetForm,
    StrForm,
)
from nu.lang import EMPTY, compile
from nu.lang.helpers import aeval, eval
from nu.lang.runtime import Context


def val(term):
    return eval(compile(term), Context())[0]


async def aval(term):
    return (await aeval(compile(term), Context()))[0]


# --- primitives ----------------------------------------------------------


def test_int_arithmetic_and_promotion():
    assert val(IntForm(5) + 3) == 8
    assert val(IntForm(10) - IntForm(4)) == 6
    assert val(IntForm(6) * 7) == 42
    assert val(IntForm(2) ** 10) == 1024
    assert val(IntForm(7) % 3) == 1
    assert val(IntForm(7) // 2) == 3
    assert val(-IntForm(5)) == -5
    assert val(abs(IntForm(-9))) == 9
    # int op float promotes (still evaluates numerically)
    assert val(IntForm(1) + 2.5) == 3.5


def test_int_comparison_logical_bitwise():
    assert val(IntForm(3) < 5) is True
    assert val(IntForm(5) >= 5) is True
    assert val(IntForm(4).bitand(6)) == 4
    assert val(IntForm(4).bitor(1)) == 5
    assert val(IntForm(1) << 4) == 16
    assert val(IntForm(5).and_(0)) is False


def test_bool_form():
    assert val(BoolForm(True).and_(False)) is False
    assert val(BoolForm(False).or_(True)) is True
    assert val(BoolForm(True).not_()) is False


def test_str_ops():
    assert val(StrForm("hello").upper()) == "HELLO"
    assert val(StrForm("HELLO").lower()) == "hello"
    assert val(StrForm("  hi  ").strip()) == "hi"
    assert val(StrForm("a,b,c").split(",")) == ["a", "b", "c"]
    assert val(StrForm("ab").replace("a", "z")) == "zb"
    assert val(StrForm("foo").startswith("fo")) is True
    assert val(StrForm("123").isdigit()) is True
    assert val(StrForm("-").join(LiteralQuery(["a", "b"]))) == "a-b"
    assert val(StrForm("hello") + " world") == "hello world"


def test_bytes_ops():
    assert val(BytesForm(b"hi").upper()) == b"HI"
    assert val(BytesForm(b"  x ").strip()) == b"x"
    assert val(BytesForm(b"a,b").split_bytes(b",")) == [b"a", b"b"]


# --- collections: reads --------------------------------------------------


def test_list_reads():
    assert val(ListForm([3, 1, 2]).first_elem()) == 3
    assert val(ListForm([3, 1, 2]).last_elem()) == 2
    assert val(ListForm([3, 1, 2]).index(1)) == 1
    assert val(ListForm([1, 1, 2]).count(1)) == 2


def test_dict_reads():
    assert val(DictForm({"a": 1, "b": 2}).keys()) == {"a", "b"} or list(
        val(DictForm({"a": 1, "b": 2}).keys())
    ) == ["a", "b"]
    assert val(DictForm({"a": 1}).get("a")) == 1
    assert val(DictForm({"a": 1}).get("z", 9)) == 9
    assert val(DictForm({"a": 1}).setdefault("b", 5)) == 5


def test_set_reads():
    assert val(SetForm({1, 2}).union(LiteralQuery({3}))) == {1, 2, 3}
    assert val(SetForm({1, 2, 3}).intersection(LiteralQuery({2, 3, 4}))) == {2, 3}
    assert val(SetForm({1, 2}).issubset(LiteralQuery({1, 2, 3}))) is True
    assert val(SetForm({1, 2}).isdisjoint(LiteralQuery({3, 4}))) is True


# --- collections: local mutation (Command yields nothing; Action yields) -


def test_list_mutation_commands_yield_nothing():
    # append/insert/extend/reverse/remove are Commands: they mutate slot 0
    # and yield nothing (None); they do not return the mutated target.
    assert val(ListForm([1, 2]).append(3)) is None
    assert val(ListForm([1, 2]).insert(0, 9)) is None
    assert val(ListForm([1, 2]).extend(LiteralQuery([3, 4]))) is None
    assert val(ListForm([1, 2, 3]).reverse()) is None
    assert val(ListForm([1, 2, 3]).remove(2)) is None
    # pop is an Action: it mutates and yields the popped value.
    assert val(ListForm([1, 2, 3]).pop()) == 3


def test_dict_mutation_commands_yield_nothing():
    # set/delete/update are Commands; they yield nothing.
    assert val(DictForm({"a": 1}).set("b", 2)) is None
    assert val(DictForm({"a": 1, "b": 2}).delete("a")) is None
    assert val(DictForm({"a": 1}).update(LiteralQuery({"b": 2}))) is None
    # pop is an Action: it yields the popped value.
    assert val(DictForm({"a": 1, "b": 2}).pop("a")) == 1


def test_set_mutation_commands_yield_nothing():
    # add/discard/update are Commands; they yield nothing.
    assert val(SetForm({1, 2}).add(3)) is None
    assert val(SetForm({1, 2, 3}).discard(2)) is None
    assert val(SetForm({1, 2}).update(LiteralQuery({3}))) is None


# --- sentinel predicates via Form base -----------------------------------


def test_sentinel_predicates():
    assert val(IntForm(1).is_empty()) is False
    assert val(IntForm(1).not_empty()) is True
    assert val(IntForm(LiteralQuery(EMPTY)).is_empty()) is True


# --- async mirror --------------------------------------------------------


def test_async_mirrors_sync():
    import asyncio

    async def go():
        assert await aval(IntForm(5) + 3) == 8
        assert await aval(StrForm("hi").upper()) == "HI"
        # append is a Command: yields nothing (None) on the async path too.
        assert await aval(ListForm([1, 2]).append(3)) is None
        assert await aval(DictForm({"a": 1}).get("a")) == 1
        assert await aval(SetForm({1, 2}).union(LiteralQuery({3}))) == {1, 2, 3}

    asyncio.run(go())
