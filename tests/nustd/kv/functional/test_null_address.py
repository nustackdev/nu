"""A key that reads NULL leaves a ref path addressing nothing.

Reads there find nothing and give NULL, as an empty slot does: a leaf, a
container's value, ``exists()``, ``extract()``, ``first()`` / ``last()``, a
container's ``keys`` / ``values`` / ``items``, ``get_item`` (its default when
given). Writes and watches have nowhere to land and raise
``NullAddressError`` before anything is written or subscribed: leaf and
whole-container sets, erases, keyed and ordered writes, every ``on_*``.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Shape, arun, run
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


GONE = Board.rows[Board.by_key["gone"]]
HINT = "Board.rows.<NULL Board.by_key.gone>"


# --- reads give NULL ----------------------------------------------------------


def test_a_leaf_under_a_null_key_reads_null_named_by_its_path(ctx) -> None:
    got = run(GONE.count, ctx)[0]
    assert is_null(got)
    assert repr(got) == f"<NULL {HINT}.count>"


def test_a_fallback_covers_it(ctx) -> None:
    assert run(nu.Int(GONE.count).fallback(0), ctx)[0] == 0


def test_a_leaf_under_a_null_key_does_not_exist(ctx) -> None:
    assert run(GONE.count.exists(), ctx)[0] is False


def test_a_container_under_a_null_key_reads_null(ctx) -> None:
    assert is_null(run(GONE.scores, ctx)[0])
    assert run(GONE.scores.exists(), ctx)[0] is False
    assert is_null(run(GONE.scores.extract(), ctx)[0])
    assert run(nu.Not(GONE.scores), ctx)[0] is True


def test_its_ends_read_null(ctx) -> None:
    assert repr(run(GONE.order.first(), ctx)[0]) == f"<NULL {HINT}.order>"
    assert is_null(run(GONE.order.last(), ctx)[0])


MAPPING_READS = {
    "keys": GONE.scores.keys(),
    "values": GONE.scores.values(),
    "items": GONE.scores.items(),
    "reversed_keys": GONE.scores.reversed_keys(),
    "reversed_values": GONE.scores.reversed_values(),
    "reversed_items": GONE.scores.reversed_items(),
    "get_item": GONE.scores.get_item("x"),
    "copy": GONE.scores.copy(),
    "page": GONE.scores.keys(limit=5),
}


@pytest.mark.parametrize("name", MAPPING_READS)
def test_a_mapping_read_under_a_null_key_reads_null(ctx, name) -> None:
    got = run(MAPPING_READS[name], ctx)[0]
    assert is_null(got)
    assert HINT in repr(got)


def test_get_item_with_a_default_reads_the_default(ctx) -> None:
    assert run(GONE.scores.get_item("x", 0), ctx)[0] == 0


def test_a_mapping_read_under_a_null_key_reads_null_on_the_async_path(ctx) -> None:
    async def go() -> None:
        assert is_null((await arun(GONE.scores.keys(), ctx))[0])
        assert is_null((await arun(GONE.scores.reversed_keys(), ctx))[0])
        assert (await arun(GONE.scores.get_item("x", 0), ctx))[0] == 0

    asyncio.run(go())


def test_a_count_or_a_walk_raises_like_any_null(ctx) -> None:
    with pytest.raises(TypeError):
        run(GONE.scores.len(), ctx)
    with pytest.raises(TypeError):
        run(GONE.scores.contains("x"), ctx)


def test_an_unsafe_read_gives_null_too(ctx) -> None:
    assert is_null(run(ItemPrimitiveGetUnsafe(GONE.count), ctx)[0])


def test_a_key_that_resolves_reads_as_usual(ctx) -> None:
    run(Board.by_key["here"].set("r1"), ctx)
    run(Board.rows["r1"].count.set(3), ctx)
    assert run(Board.rows[Board.by_key["here"]].count, ctx)[0] == 3


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
    with pytest.raises(NullAddressError, match="a key in the path read NULL"):
        run(WRITES[name], ctx)
    assert run(Board.rows.exists(), ctx)[0] is False


def test_the_error_names_the_path(ctx) -> None:
    with pytest.raises(NullAddressError) as err:
        run(GONE.count.set(1), ctx)
    assert HINT in str(err.value)


def test_it_is_a_lookup_error(ctx) -> None:
    with pytest.raises(LookupError):
        run(GONE.count.set(1), ctx)


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
        with pytest.raises(NullAddressError, match="a key in the path read NULL"):
            await arun(WATCHES[name](), ctx)

    asyncio.run(go())


# --- the async path answers the same ------------------------------------------


def test_the_async_path_reads_null_and_refuses_writes(ctx) -> None:
    async def go() -> None:
        assert is_null((await arun(GONE.count, ctx))[0])
        assert (await arun(GONE.scores.exists(), ctx))[0] is False
        assert is_null((await arun(GONE.order.first(), ctx))[0])
        with pytest.raises(NullAddressError):
            await arun(GONE.count.set(1), ctx)
        with pytest.raises(NullAddressError):
            await arun(GONE.scores.set_item("a", 1), ctx)

    asyncio.run(go())
