"""Functional tests for OrderedDictRef: a mapping kept in collection order.

Verifies:
- Roundtrip set/get/delete through the ref, plain dict ops still work.
- Iteration, keys, values, items in collection order (not key order).
- insert_before / insert_after place next to an anchor, errors on bad ids.
- move(before=/after=) relocates without touching the value.
- first / last read the ends, EMPTY when empty or missing.
- Whole-value set and read keep the order; the view is a MutableMapping.
- Path export/import carries the view class; lazy/eager facets.
"""

from __future__ import annotations

import pickle
from collections.abc import MutableMapping

import pytest

import nu
from nu import Literal, Shape, run
from nu.lang.sentinels import EMPTY
from nustd.kv import OrderedDictRef, StrRef
from nustd.kv.paths import ViewPathSer
from nustd.kv.refs.base import Facet
from virtuals.views import FractionalIndexedDictView, FractionalIndexedDictViewBase


class Plane(Shape):
    name = StrRef.slot()
    cells = OrderedDictRef.slot(bool)  # membership: id -> True
    scores = OrderedDictRef.slot(int)


def _fill(ctx, ids) -> None:
    for i in ids:
        run(Plane.cells.set_item(i, True), ctx)


def _keys(ctx) -> list[str]:
    return list(run(Plane.cells.keys(), ctx)[0])


# ============================================================================
# ROUNDTRIP (plain dict surface)
# ============================================================================


def test_put_get(ctx) -> None:
    run(Plane.scores.set_item("a", 1), ctx)
    assert run(Plane.scores.get_item("a"), ctx)[0] == 1


def test_delete(ctx) -> None:
    _fill(ctx, ["a", "b", "c"])
    run(Plane.cells.del_item("b"), ctx)
    assert run(Plane.cells.get_item("b", Literal(False)), ctx)[0] is False
    assert _keys(ctx) == ["a", "c"]


def test_len_contains(ctx) -> None:
    _fill(ctx, ["a", "b", "c"])
    assert run(Plane.cells.len(), ctx)[0] == 3
    assert run(Plane.cells.contains("b"), ctx)[0] is True
    assert run(Plane.cells.contains("z"), ctx)[0] is False


def test_set_existing_keeps_place(ctx) -> None:
    for i, k in enumerate(["a", "b", "c"]):
        run(Plane.scores.set_item(k, i), ctx)
    run(Plane.scores.set_item("a", 99), ctx)
    assert list(run(Plane.scores.keys(), ctx)[0]) == ["a", "b", "c"]
    assert run(Plane.scores.get_item("a"), ctx)[0] == 99


# ============================================================================
# ITERATION IN COLLECTION ORDER
# ============================================================================


def test_keys_follow_insertion_not_key_order(ctx) -> None:
    _fill(ctx, ["z", "m", "a"])
    assert _keys(ctx) == ["z", "m", "a"]


def test_values_items_follow_order(ctx) -> None:
    for k, v in (("z", 3), ("m", 2), ("a", 1)):
        run(Plane.scores.set_item(k, v), ctx)
    assert list(run(Plane.scores.values(), ctx)[0]) == [3, 2, 1]
    assert list(run(Plane.scores.items(), ctx)[0]) == [("z", 3), ("m", 2), ("a", 1)]


def test_iter_stream_follows_order(ctx) -> None:
    _fill(ctx, ["z", "m", "a"])
    assert list(run(Plane.cells.iter(), ctx)[0]) == ["z", "m", "a"]


# ============================================================================
# INSERT BEFORE / AFTER
# ============================================================================


def test_insert_before(ctx) -> None:
    _fill(ctx, ["a", "c"])
    run(Plane.cells.insert_before("c", "b"), ctx)
    assert _keys(ctx) == ["a", "b", "c"]
    assert run(Plane.cells.get_item("b"), ctx)[0] is True


def test_insert_after(ctx) -> None:
    _fill(ctx, ["a", "c"])
    run(Plane.cells.insert_after("a", "b"), ctx)
    assert _keys(ctx) == ["a", "b", "c"]


def test_insert_at_edges(ctx) -> None:
    _fill(ctx, ["b"])
    run(Plane.cells.insert_before("b", "a"), ctx)
    run(Plane.cells.insert_after("b", "c"), ctx)
    assert _keys(ctx) == ["a", "b", "c"]
    assert run(Plane.cells.first(), ctx)[0] == "a"
    assert run(Plane.cells.last(), ctx)[0] == "c"


def test_insert_with_value(ctx) -> None:
    run(Plane.scores.set_item("a", 1), ctx)
    run(Plane.scores.insert_after("a", "b", 2), ctx)
    assert run(Plane.scores.get_item("b"), ctx)[0] == 2


def test_insert_present_raises(ctx) -> None:
    _fill(ctx, ["a", "b"])
    with pytest.raises(ValueError, match="already"):
        run(Plane.cells.insert_before("b", "a"), ctx)
    assert _keys(ctx) == ["a", "b"]


def test_insert_missing_anchor_raises(ctx) -> None:
    _fill(ctx, ["a"])
    with pytest.raises(KeyError):
        run(Plane.cells.insert_after("nope", "b"), ctx)


def test_insert_ids_from_refs(ctx) -> None:
    _fill(ctx, ["a", "c"])
    run(Plane.name.set("c"), ctx)
    run(Plane.cells.insert_before(Plane.name, "b"), ctx)
    assert _keys(ctx) == ["a", "b", "c"]


# ============================================================================
# MOVE
# ============================================================================


def test_move_before(ctx) -> None:
    _fill(ctx, ["a", "b", "c"])
    run(Plane.cells.move("c", before="a"), ctx)
    assert _keys(ctx) == ["c", "a", "b"]


def test_move_after(ctx) -> None:
    _fill(ctx, ["a", "b", "c"])
    run(Plane.cells.move("a", after="c"), ctx)
    assert _keys(ctx) == ["b", "c", "a"]


def test_move_keeps_value(ctx) -> None:
    for k, v in (("a", 1), ("b", 2), ("c", 3)):
        run(Plane.scores.set_item(k, v), ctx)
    run(Plane.scores.move("c", before="a"), ctx)
    assert list(run(Plane.scores.items(), ctx)[0]) == [("c", 3), ("a", 1), ("b", 2)]


def test_move_to_same_place_is_noop(ctx) -> None:
    _fill(ctx, ["a", "b", "c"])
    run(Plane.cells.move("b", after="a"), ctx)
    run(Plane.cells.move("b", before="b"), ctx)
    assert _keys(ctx) == ["a", "b", "c"]


def test_move_requires_exactly_one_side(ctx) -> None:
    _fill(ctx, ["a", "b"])
    with pytest.raises(ValueError, match="exactly one"):
        run(Plane.cells.move("a"), ctx)
    with pytest.raises(ValueError, match="exactly one"):
        run(Plane.cells.move("a", before="b", after="b"), ctx)


def test_move_missing_raises(ctx) -> None:
    _fill(ctx, ["a"])
    with pytest.raises(KeyError):
        run(Plane.cells.move("zz", before="a"), ctx)
    with pytest.raises(KeyError):
        run(Plane.cells.move("a", after="zz"), ctx)


# ============================================================================
# FIRST / LAST
# ============================================================================


def test_first_last(ctx) -> None:
    _fill(ctx, ["m", "a", "z"])
    assert run(Plane.cells.first(), ctx)[0] == "m"
    assert run(Plane.cells.last(), ctx)[0] == "z"


def test_first_last_track_edits(ctx) -> None:
    _fill(ctx, ["a", "b", "c"])
    run(Plane.cells.del_item("a"), ctx)
    run(Plane.cells.move("b", after="c"), ctx)
    assert run(Plane.cells.first(), ctx)[0] == "c"
    assert run(Plane.cells.last(), ctx)[0] == "b"


def test_first_last_empty_or_missing(ctx) -> None:
    assert run(Plane.cells.first(), ctx)[0] is EMPTY
    assert run(Plane.cells.last(), ctx)[0] is EMPTY
    _fill(ctx, ["a"])
    run(Plane.cells.del_item("a"), ctx)
    assert run(Plane.cells.first(), ctx)[0] is EMPTY
    assert run(Plane.cells.last(), ctx)[0] is EMPTY


# ============================================================================
# WHOLE-VALUE SET AND READ
# ============================================================================


def test_set_whole_keeps_order(ctx) -> None:
    run(Plane.scores.set({"z": 3, "m": 2, "a": 1}), ctx)
    assert list(run(Plane.scores.keys(), ctx)[0]) == ["z", "m", "a"]
    whole = run(Plane.scores.eager, ctx)[0]
    assert list(whole.items()) == [("z", 3), ("m", 2), ("a", 1)]


def test_set_whole_replaces(ctx) -> None:
    run(Plane.scores.set({"z": 3, "m": 2}), ctx)
    run(Plane.scores.set({"q": 9}), ctx)
    assert list(run(Plane.scores.keys(), ctx)[0]) == ["q"]


def test_read_is_ordered_view_and_mutable_mapping(ctx) -> None:
    _fill(ctx, ["a"])
    view = run(Plane.cells, ctx)[0]
    assert isinstance(view, FractionalIndexedDictViewBase)
    assert isinstance(view, MutableMapping)


# ============================================================================
# PATHS AND FACETS
# ============================================================================


def test_slot_carries_view_class() -> None:
    assert nu.tree.payload(Plane.cells)["type_marker"] is FractionalIndexedDictView


def test_view_path_roundtrips_by_value() -> None:
    path = ViewPathSer((("cells", FractionalIndexedDictView),))
    back = pickle.loads(pickle.dumps(path))  # noqa: S301 - our own bytes
    assert back == path
    assert back[0][1] is FractionalIndexedDictView


def test_facet_switch_returns_clone(ctx) -> None:
    ref = Plane.cells
    eager = ref.eager
    lazy = ref.lazy
    assert nu.tree.payload(eager)["facet"] is Facet.EAGER
    assert nu.tree.payload(lazy).get("facet", Facet.LAZY) is Facet.LAZY
    assert nu.tree.payload(eager)["segment"] == nu.tree.payload(ref)["segment"]
