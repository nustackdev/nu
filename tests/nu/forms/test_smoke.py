"""End-to-end smoke tests for the ported Forms layer.

Builds fluent Form programs, compiles them, and evaluates both sync and async,
asserting the value the underlying interaction should yield. Covers each form
family and exercises the real eval paths (the interaction thunks), not just
construction.
"""

from __future__ import annotations

from nu.core import Literal
from nu.forms import (
    Bool,
    Bytes,
    Dict,
    Int,
    List,
    Set,
    Str,
)
from nu.lang import EMPTY
from nu.lang.helpers import aeval, compile, eval
from nu.lang.runtime import Context


def val(term):
    return eval(compile(term), Context())[0]


async def aval(term):
    return (await aeval(compile(term), Context()))[0]


# --- primitives ----------------------------------------------------------


def test_int_arithmetic_and_promotion():
    assert val(Int(5) + 3) == 8
    assert val(Int(10) - Int(4)) == 6
    assert val(Int(6) * 7) == 42
    assert val(Int(2) ** 10) == 1024
    assert val(Int(7) % 3) == 1
    assert val(Int(7) // 2) == 3
    assert val(-Int(5)) == -5
    assert val(abs(Int(-9))) == 9
    # int op float promotes (still evaluates numerically)
    assert val(Int(1) + 2.5) == 3.5


def test_int_comparison_logical_bitwise():
    assert val(Int(3) < 5) is True
    assert val(Int(5) >= 5) is True
    assert val(Int(4).bitand(6)) == 4
    assert val(Int(4).bitor(1)) == 5
    assert val(Int(1) << 4) == 16
    assert val(Int(5).and_(0)) is False


def test_bool_form():
    assert val(Bool(True).and_(False)) is False
    assert val(Bool(False).or_(True)) is True
    assert val(Bool(True).not_()) is False


def test_str_ops():
    assert val(Str("hello").upper()) == "HELLO"
    assert val(Str("HELLO").lower()) == "hello"
    assert val(Str("  hi  ").strip()) == "hi"
    assert val(Str("a,b,c").split(",")) == ["a", "b", "c"]
    assert val(Str("ab").replace("a", "z")) == "zb"
    assert val(Str("foo").startswith("fo")) is True
    assert val(Str("123").isdigit()) is True
    assert val(Str("-").join(Literal(["a", "b"]))) == "a-b"
    assert val(Str("hello") + " world") == "hello world"


def test_bytes_ops():
    assert val(Bytes(b"hi").upper()) == b"HI"
    assert val(Bytes(b"  x ").strip()) == b"x"
    assert val(Bytes(b"a,b").split_bytes(b",")) == [b"a", b"b"]


# --- collections: reads --------------------------------------------------


def test_list_reads():
    assert val(List([3, 1, 2]).first_elem()) == 3
    assert val(List([3, 1, 2]).last_elem()) == 2
    assert val(List([3, 1, 2]).index(1)) == 1
    assert val(List([1, 1, 2]).count(1)) == 2


def test_dict_reads():
    assert val(Dict({"a": 1, "b": 2}).keys()) == {"a", "b"} or list(
        val(Dict({"a": 1, "b": 2}).keys())
    ) == ["a", "b"]
    assert val(Dict({"a": 1}).get_item("a")) == 1
    assert val(Dict({"a": 1}).get_item("z", 9)) == 9
    assert val(Dict({"a": 1}).setdefault("b", 5)) == 5


def test_dict_reversed_reads():
    d = Dict({"a": 1, "b": 2, "c": 3})
    assert list(val(d.reversed_keys())) == ["c", "b", "a"]
    assert list(val(d.reversed_values())) == [3, 2, 1]
    assert list(val(d.reversed_items())) == [("c", 3), ("b", 2), ("a", 1)]


async def test_dict_reversed_reads_async():
    d = Dict({"a": 1, "b": 2, "c": 3})

    async def collect(term):
        out = []
        async for item in await aval(term):
            out.append(item)
        return out

    assert await collect(d.reversed_keys()) == ["c", "b", "a"]
    assert await collect(d.reversed_values()) == [3, 2, 1]
    assert await collect(d.reversed_items()) == [("c", 3), ("b", 2), ("a", 1)]


def test_set_reads():
    assert val(Set({1, 2}).union(Literal({3}))) == {1, 2, 3}
    assert val(Set({1, 2, 3}).intersection(Literal({2, 3, 4}))) == {2, 3}
    assert val(Set({1, 2}).issubset(Literal({1, 2, 3}))) is True
    assert val(Set({1, 2}).isdisjoint(Literal({3, 4}))) is True


# --- collections: local mutation (Command yields nothing; Action yields) -


def test_list_mutation_commands_yield_nothing():
    # append/insert/extend/reverse/remove are Commands: they mutate slot 0
    # and yield nothing (None); they do not return the mutated target.
    assert val(List([1, 2]).append(3)) is None
    assert val(List([1, 2]).insert(0, 9)) is None
    assert val(List([1, 2]).extend(Literal([3, 4]))) is None
    assert val(List([1, 2, 3]).reverse()) is None
    assert val(List([1, 2, 3]).remove(2)) is None
    # pop is an Action: it mutates and yields the popped value.
    assert val(List([1, 2, 3]).pop()) == 3


def test_dict_mutation_commands_yield_nothing():
    # set_item/del_item/update are Commands; they yield nothing.
    assert val(Dict({"a": 1}).set_item("b", 2)) is None
    assert val(Dict({"a": 1, "b": 2}).del_item("a")) is None
    assert val(Dict({"a": 1}).update(Literal({"b": 2}))) is None
    # pop is an Action: it yields the popped value.
    assert val(Dict({"a": 1, "b": 2}).pop("a")) == 1


def test_set_mutation_commands_yield_nothing():
    # add/discard/update are Commands; they yield nothing.
    assert val(Set({1, 2}).add(3)) is None
    assert val(Set({1, 2, 3}).discard(2)) is None
    assert val(Set({1, 2}).update(Literal({3}))) is None


# --- sentinel predicates via Form base -----------------------------------


def test_sentinel_predicates():
    assert val(Int(1).is_empty()) is False
    assert val(Int(1).not_empty()) is True
    assert val(Int(Literal(EMPTY)).is_empty()) is True


# --- async mirror --------------------------------------------------------


def test_async_mirrors_sync():
    import asyncio

    async def go():
        assert await aval(Int(5) + 3) == 8
        assert await aval(Str("hi").upper()) == "HI"
        # append is a Command: yields nothing (None) on the async path too.
        assert await aval(List([1, 2]).append(3)) is None
        assert await aval(Dict({"a": 1}).get_item("a")) == 1
        assert await aval(Set({1, 2}).union(Literal({3}))) == {1, 2, 3}

    asyncio.run(go())
