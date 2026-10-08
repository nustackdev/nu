"""Functional tests: a container written into only through nested refs knows its length.

Writing ``Sheet.rows[k].cells.set(...)`` creates ``rows[k]`` on the way down.
Each level is created by its parent view, so a parent that keeps its own
count (``DictView``) or key index (``IndexedDictView``, ``LogIndexedDictView``)
records the new key: ``len()``, ``keys()`` and iteration agree with what is
stored.
"""

from __future__ import annotations

import pytest

from nu import Shape, run
from nustd.kv import DictRef, ListRef, PrimitiveDictRef, StrRef
from virtuals.views import DictView, IndexedDictView, LogIndexedDictView


class Row(Shape):
    cells = DictRef.slot(object)


class Plain(Shape):
    name = StrRef.slot()
    raw = PrimitiveDictRef.slot()


class Sheet(Shape):
    rows = DictRef.slot(Row)
    plain = DictRef.slot(Plain)
    strs = DictRef.slot(str)
    order = ListRef.slot(str)
    indexed = DictRef.slot(Plain, view=IndexedDictView)
    logged = DictRef.slot(Plain, view=LogIndexedDictView)


KEYS = ("r1", "r2", "r3")


def _keys(ref, ctx) -> list:
    return list(run(ref.keys(), ctx)[0])


def test_dict_of_shapes_counts_keys_created_by_nested_writes(ctx) -> None:
    for key in KEYS:
        run(Sheet.rows[key].cells.set({"name": "x", "done": False}), ctx)
        run(Sheet.plain[key].name.set("x"), ctx)
        run(Sheet.strs[key].set("x"), ctx)
    run(Sheet.order.set(list(KEYS)), ctx)

    for ref in (Sheet.rows, Sheet.plain, Sheet.strs, Sheet.order):
        assert run(ref.len(), ctx)[0] == 3
    for ref in (Sheet.rows, Sheet.plain, Sheet.strs):
        assert _keys(ref, ctx) == list(KEYS)
    assert run(Sheet.rows["r1"].cells.len(), ctx)[0] == 2


def test_root_counts_every_top_level_slot(ctx, nav, tx) -> None:
    run(Sheet.rows["r1"].cells.set({"a": 1}), ctx)
    run(Sheet.plain["r1"].name.set("x"), ctx)
    run(Sheet.strs["r1"].set("x"), ctx)

    root = nav.root(tx)
    assert len(root) == 3
    assert sorted(root.keys()) == ["plain", "rows", "strs"]


@pytest.mark.parametrize("ref", [Sheet.plain, Sheet.indexed, Sheet.logged])
def test_nested_writes_are_counted_once(ref, ctx) -> None:
    for _ in range(2):
        for key in KEYS:
            run(ref[key].name.set("x"), ctx)

    assert run(ref.len(), ctx)[0] == 3
    assert _keys(ref, ctx) == list(KEYS)


@pytest.mark.parametrize("ref", [Sheet.indexed, Sheet.logged])
def test_indexed_dicts_index_keys_created_by_nested_writes(ref, ctx) -> None:
    for key in KEYS:
        run(ref[key].name.set("x"), ctx)

    assert run(ref.len(), ctx)[0] == 3
    assert _keys(ref, ctx) == list(KEYS)
    assert run(ref["r2"].name, ctx)[0] == "x"


def test_blob_write_counts_new_key(ctx) -> None:
    run(Sheet.plain["r1"].raw.set({"a": [1, 2]}), ctx)
    run(Sheet.plain["r1"].raw.set({"a": [3]}), ctx)
    run(Sheet.plain["r1"].name.set("x"), ctx)

    assert run(Sheet.plain.len(), ctx)[0] == 1
    assert run(Sheet.plain["r1"].raw, ctx)[0] == {"a": [3]}


def test_whole_value_write_then_nested_write_does_not_double_count(ctx) -> None:
    run(Sheet.plain["r1"].set({"name": "x"}), ctx)
    run(Sheet.plain["r1"].name.set("y"), ctx)
    run(Sheet.plain["r2"].name.set("z"), ctx)

    assert run(Sheet.plain.len(), ctx)[0] == 2
    assert _keys(Sheet.plain, ctx) == ["r1", "r2"]
    assert isinstance(run(Sheet.plain, ctx)[0], DictView)
