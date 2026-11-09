"""A key that reads NULL leaves a ref path addressing nothing.

Every access through such a path raises ``NullAddressError`` before anything
is read, written or subscribed: reads (a leaf, a container, ``exists()``,
``extract()``, ``first()`` / ``last()``, the mapping reads), writes (leaf and
whole-container sets, erases, keyed and ordered writes) and every ``on_*``.
A caller that expects a missing key branches on it first with ``IsNull``.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Shape, arun, run
from nu.core import IsNull
from nu.forms import NullForm
from nu.lang import is_null
from nustd.kv import (
    DictRef,
    IntRef,
    ItemPrimitiveGetUnsafe,
    ItemPrimitiveSetUnsafeCmd,
    NullAddressError,
    OrderedDictRef,
    StrRef,
)


class Row(Shape):
    count = IntRef.slot()
    scores = DictRef.slot(int)
    order = OrderedDictRef.slot(bool)


class Board(Shape):
    by_key = DictRef.slot(str)
    rows = DictRef.slot(Row)
    title = StrRef.slot()


KEY = Board.by_key["gone"]
GONE = Board.rows[KEY]
MATCH = "a key under Board.rows read NULL"


# --- reads raise ---------------------------------------------------------------


READS = {
    "leaf": lambda: GONE.count,
    "leaf_exists": lambda: GONE.count.exists(),
    "container": lambda: GONE.scores,
    "container_exists": lambda: GONE.scores.exists(),
    "extract": lambda: GONE.scores.extract(),
    "first": lambda: GONE.order.first(),
    "last": lambda: GONE.order.last(),
    "keys": lambda: GONE.scores.keys(),
    "values": lambda: GONE.scores.values(),
    "items": lambda: GONE.scores.items(),
    "reversed_keys": lambda: GONE.scores.reversed_keys(),
    "get_item": lambda: GONE.scores.get_item("x"),
    "get_item_default": lambda: GONE.scores.get_item("x", 0),
    "copy": lambda: GONE.scores.copy(),
    "len": lambda: GONE.scores.len(),
    "contains": lambda: GONE.scores.contains("x"),
    "unsafe_get": lambda: ItemPrimitiveGetUnsafe(GONE.count),
}


@pytest.mark.parametrize("name", READS)
def test_a_read_under_a_null_key_raises(ctx, name) -> None:
    with pytest.raises(NullAddressError, match=MATCH):
        run(READS[name](), ctx)


@pytest.mark.parametrize("name", READS)
def test_a_read_under_a_null_key_raises_on_the_async_path(ctx, name) -> None:
    async def go() -> None:
        with pytest.raises(NullAddressError, match=MATCH):
            await arun(READS[name](), ctx)

    asyncio.run(go())


def test_a_caller_branches_on_the_key_first(ctx) -> None:
    term = nu.If(IsNull(KEY), NullForm.create(), GONE.count)
    assert is_null(run(term, ctx)[0])
    run(Board.by_key["gone"].set("r1"), ctx)
    run(Board.rows["r1"].count.set(3), ctx)
    assert run(term, ctx)[0] == 3


def test_a_key_that_resolves_reads_as_usual(ctx) -> None:
    run(Board.by_key["here"].set("r1"), ctx)
    run(Board.rows["r1"].count.set(3), ctx)
    assert run(Board.rows[Board.by_key["here"]].count, ctx)[0] == 3


def test_it_is_a_lookup_error(ctx) -> None:
    with pytest.raises(LookupError):
        run(GONE.count, ctx)


# --- writes raise -------------------------------------------------------------


WRITES = {
    "leaf_set": GONE.count.set(1),
    "leaf_erase": GONE.count.erase(),
    "container_set": GONE.scores.set({"a": 1}),
    "container_erase": GONE.scores.erase(),
    "set_item": GONE.scores.set_item("a", 1),
    "del_item": GONE.scores.del_item("a", missing_ok=True),
    "row_set": GONE.set({"count": 1}),
    "ordered_set_item": GONE.order.set_item("c1", True),
    "ordered_move": GONE.order.move("c1", before="c2"),
    "unsafe_set": ItemPrimitiveSetUnsafeCmd(GONE.count, 1),
}


@pytest.mark.parametrize("name", WRITES)
def test_a_write_under_a_null_key_raises_and_lands_nothing(ctx, name) -> None:
    with pytest.raises(NullAddressError, match=MATCH):
        run(WRITES[name], ctx)
    assert run(Board.rows.exists(), ctx)[0] is False


def test_a_write_under_a_null_key_raises_on_the_async_path(ctx) -> None:
    async def go() -> None:
        with pytest.raises(NullAddressError, match=MATCH):
            await arun(GONE.count.set(1), ctx)
        with pytest.raises(NullAddressError, match=MATCH):
            await arun(GONE.scores.set_item("a", 1), ctx)

    asyncio.run(go())


# --- watches raise ------------------------------------------------------------


WATCHES = {
    "leaf_on_change": lambda: GONE.count.on_change(),
    "on_change": lambda: GONE.scores.on_change(),
    "on_child_change": lambda: GONE.scores.on_child_change("a"),
    "on_children_change": lambda: GONE.scores.on_children_change(),
    "on_descendants_change": lambda: GONE.scores.on_descendants_change("*"),
    "ordered_on_children_change": lambda: GONE.order.on_children_change(),
}


@pytest.mark.parametrize("name", WATCHES)
def test_a_watch_under_a_null_key_raises(ctx, name) -> None:
    async def go() -> None:
        with pytest.raises(NullAddressError, match=MATCH):
            await arun(WATCHES[name](), ctx)

    asyncio.run(go())
