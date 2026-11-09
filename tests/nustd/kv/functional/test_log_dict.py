"""Functional tests for LogDictRef: an append-only mapping in log order.

Verifies:
- The slot lays out a LogIndexed view, by default and by ``view=``; the
  annotation form declares the same slot.
- Plain dict surface: set, get, contains, delete; descent types the value.
- Iteration, keys, values and items run oldest first; a re-set keeps its place.
- ``first`` / ``last`` read the oldest and newest id, and raise when there is none.
- The view is a MutableMapping; a container ref as the value is refused.
"""

from __future__ import annotations

from collections.abc import MutableMapping

import pytest

from nu import Shape, run
from nu.lang import is_null
from nustd.kv import DictRef, IntRef, LogDictRef, NullAddressError, OrderedDictRef, StrRef
from nustd.kv.refs.base import Facet
from virtuals.container import ContainerNotFoundError
from virtuals.views import EagerLogIndexedDictView, LogIndexedDictView, LogIndexedDictViewBase


class Run(Shape):
    status = StrRef.slot()
    step = IntRef.slot()


class Ids(Shape):
    ids = LogDictRef.slot(bool)


class History(Shape):
    runs = LogDictRef.slot(Run)
    removed = LogDictRef.slot(bool)
    steps = LogDictRef.slot(int, view=EagerLogIndexedDictView)
    noted: LogDictRef[str, int]
    spec_planes = DictRef.slot(Ids)
    by_key = DictRef.slot(str)


def _add(ctx, ref, ids) -> None:
    for k in ids:
        run(ref.set_item(k, True), ctx)


def test_the_slot_lays_out_a_log() -> None:
    assert History.removed._payload["type_marker"] is LogIndexedDictView
    assert History.steps._payload["type_marker"] is EagerLogIndexedDictView
    assert History.noted._payload["type_marker"] is LogIndexedDictView
    assert isinstance(History.noted, LogDictRef)


def test_the_view_is_a_mutable_mapping(ctx) -> None:
    _add(ctx, History.removed, ["a"])
    view = run(History.removed._with_facet(Facet.NONE), ctx)[0]
    assert isinstance(view, LogIndexedDictViewBase)
    assert isinstance(view, MutableMapping)


def test_set_get_contains_delete(ctx) -> None:
    run(History.runs["r1"].status.set("running"), ctx)
    run(History.runs["r1"].step.set(3), ctx)
    assert run(History.runs["r1"].status, ctx)[0] == "running"
    assert run(History.runs.contains("r1"), ctx)[0] is True
    run(History.runs.del_item("r1"), ctx)
    assert run(History.runs.contains("r1"), ctx)[0] is False
    assert is_null(run(History.runs["r1"].status, ctx)[0])


def test_listing_runs_oldest_first(ctx) -> None:
    for i, k in enumerate(["c", "a", "b"]):
        run(History.steps.set_item(k, i), ctx)
    assert list(run(History.steps.keys(), ctx)[0]) == ["c", "a", "b"]
    assert list(run(History.steps.values(), ctx)[0]) == [0, 1, 2]
    assert list(run(History.steps.items(), ctx)[0]) == [("c", 0), ("a", 1), ("b", 2)]
    assert list(run(History.steps.reversed_keys(), ctx)[0]) == ["b", "a", "c"]


def test_a_re_set_keeps_its_place(ctx) -> None:
    for i, k in enumerate(["a", "b", "c"]):
        run(History.steps.set_item(k, i), ctx)
    run(History.steps.set_item("a", 99), ctx)
    assert list(run(History.steps.keys(), ctx)[0]) == ["a", "b", "c"]
    assert run(History.steps.get_item("a"), ctx)[0] == 99


def test_first_and_last_are_the_oldest_and_newest(ctx) -> None:
    _add(ctx, History.removed, ["p2", "p1", "p3"])
    assert run(History.removed.first(), ctx)[0] == "p2"
    assert run(History.removed.last(), ctx)[0] == "p3"
    run(History.removed.del_item("p3"), ctx)
    assert run(History.removed.last(), ctx)[0] == "p1"


def test_first_and_last_of_a_never_written_log_raise(ctx) -> None:
    with pytest.raises(ContainerNotFoundError):
        run(History.removed.first(), ctx)
    with pytest.raises(ContainerNotFoundError):
        run(History.removed.last(), ctx)


def test_first_and_last_of_an_emptied_log_raise(ctx) -> None:
    _add(ctx, History.removed, ["p1"])
    run(History.removed.del_item("p1"), ctx)
    with pytest.raises(IndexError):
        run(History.removed.first(), ctx)
    with pytest.raises(IndexError):
        run(History.removed.last(), ctx)


def test_last_under_a_named_slot(ctx) -> None:
    _add(ctx, History.spec_planes["nulog"].ids, ["p1", "p2"])
    assert run(History.spec_planes["nulog"].ids.last(), ctx)[0] == "p2"


def test_last_under_a_null_key_raises(ctx) -> None:
    with pytest.raises(NullAddressError):
        run(History.spec_planes[History.by_key["gone"]].ids.last(), ctx)


def test_a_container_ref_as_the_value_is_refused() -> None:
    with pytest.raises(TypeError, match="Use a Shape"):
        LogDictRef.slot(OrderedDictRef[str, bool])
