"""Paged key reads on mapping refs: ``keys(after=, limit=)``, ``reversed_keys(before=, limit=)``.

Verifies:
- A page reads in the view's order: key order on a dict, placed order on an
  ordered dict, oldest first on a log; reversed pages run last first.
- The cursor: a position on a dict (a deleted key still resumes), an id on an
  ordered dict and a log (a missing one raises KeyError). NULL starts at the end.
- A page of an empty or never-written mapping is empty; a path with a NULL key
  reads NULL.
- ``limit`` is a count: 0 reads nothing, NULL or negative raises.
- Without arguments ``keys()`` and ``reversed_keys()`` read as before.
- Views that cannot seek are refused at build.
"""

from __future__ import annotations

import pytest

import nu
from nu import Shape, arun, run
from nu.lang import is_null
from nustd.kv import DictRef, KeysPage, Kh57Ref, LogDictRef, OrderedDictRef, StrRef
from virtuals.views import FlatDictView


class Group(Shape):
    ids = LogDictRef.slot(bool)


class Board(Shape):
    scores = DictRef.slot(int)
    cells = OrderedDictRef.slot(bool)
    log = LogDictRef.slot(bool)
    groups = DictRef.slot(Group)
    by_key = DictRef.slot(str)
    cursor = StrRef.slot()
    points = Kh57Ref.slot(int)


COLLECTIONS = {
    "dict": Board.scores,
    "ordered": Board.cells,
    "log": Board.log,
}


def _fill(ctx, ref, ids) -> None:
    for i, k in enumerate(ids):
        run(ref.set_item(k, i), ctx)


def _page(ctx, term) -> list:
    return run(term, ctx)[0]


# --- order ---------------------------------------------------------------------


def test_a_dict_pages_in_key_order(ctx) -> None:
    _fill(ctx, Board.scores, ["c", "a", "d", "b"])
    assert _page(ctx, Board.scores.keys(limit=2)) == ["a", "b"]
    assert _page(ctx, Board.scores.keys(after="b", limit=2)) == ["c", "d"]
    assert _page(ctx, Board.scores.reversed_keys(limit=3)) == ["d", "c", "b"]
    assert _page(ctx, Board.scores.reversed_keys(before="b", limit=3)) == ["a"]


def test_an_ordered_dict_pages_in_placed_order(ctx) -> None:
    _fill(ctx, Board.cells, ["c", "a", "d"])
    run(Board.cells.move("d", before="c"), ctx)
    assert _page(ctx, Board.cells.keys(limit=2)) == ["d", "c"]
    assert _page(ctx, Board.cells.keys(after="c", limit=5)) == ["a"]
    assert _page(ctx, Board.cells.reversed_keys(before="a", limit=5)) == ["c", "d"]


def test_a_log_pages_oldest_first_and_reversed_newest_first(ctx) -> None:
    _fill(ctx, Board.log, ["c", "a", "d", "b"])
    assert _page(ctx, Board.log.keys(limit=3)) == ["c", "a", "d"]
    assert _page(ctx, Board.log.keys(after="a", limit=3)) == ["d", "b"]
    assert _page(ctx, Board.log.reversed_keys(limit=2)) == ["b", "d"]
    assert _page(ctx, Board.log.reversed_keys(before="d", limit=5)) == ["a", "c"]


@pytest.mark.parametrize("name", COLLECTIONS)
def test_pages_walk_the_whole_collection_once(ctx, name) -> None:
    ref = COLLECTIONS[name]
    ids = [f"k{i:02d}" for i in range(11)]
    _fill(ctx, ref, ids)
    seen: list = []
    cursor = None
    while page := _page(ctx, ref.keys(after=cursor, limit=4)):
        seen += page
        cursor = page[-1]
    assert seen == ids


@pytest.mark.parametrize("name", COLLECTIONS)
def test_a_cursor_read_from_a_ref(ctx, name) -> None:
    ref = COLLECTIONS[name]
    _fill(ctx, ref, ["a", "b", "c"])
    run(Board.cursor.set("a"), ctx)
    assert _page(ctx, ref.keys(after=Board.cursor, limit=5)) == ["b", "c"]


@pytest.mark.parametrize("name", COLLECTIONS)
def test_a_null_cursor_starts_at_the_end(ctx, name) -> None:
    ref = COLLECTIONS[name]
    _fill(ctx, ref, ["a", "b"])
    assert _page(ctx, ref.keys(after=Board.cursor, limit=5)) == ["a", "b"]
    assert _page(ctx, ref.reversed_keys(before=Board.cursor, limit=1)) == ["b"]


# --- cursor that is gone -------------------------------------------------------


def test_a_dict_resumes_past_a_deleted_key(ctx) -> None:
    _fill(ctx, Board.scores, ["a", "b", "c"])
    run(Board.scores.del_item("b"), ctx)
    assert _page(ctx, Board.scores.keys(after="b", limit=5)) == ["c"]
    assert _page(ctx, Board.scores.reversed_keys(before="b", limit=5)) == ["a"]


@pytest.mark.parametrize("name", ["ordered", "log"])
def test_a_missing_id_cursor_raises_naming_the_path(ctx, name) -> None:
    ref = COLLECTIONS[name]
    _fill(ctx, ref, ["a", "b"])
    with pytest.raises(KeyError, match="Board"):
        run(ref.keys(after="gone", limit=5), ctx)
    with pytest.raises(KeyError, match="Board"):
        run(ref.reversed_keys(before="gone", limit=5), ctx)


# --- nothing there -------------------------------------------------------------


@pytest.mark.parametrize("name", COLLECTIONS)
def test_a_never_written_mapping_reads_an_empty_page(ctx, name) -> None:
    ref = COLLECTIONS[name]
    assert _page(ctx, ref.keys(limit=5)) == []
    assert _page(ctx, ref.reversed_keys(limit=5)) == []


@pytest.mark.parametrize("name", COLLECTIONS)
def test_an_emptied_mapping_reads_an_empty_page(ctx, name) -> None:
    ref = COLLECTIONS[name]
    _fill(ctx, ref, ["a"])
    run(ref.del_item("a"), ctx)
    assert _page(ctx, ref.keys(limit=5)) == []


def test_a_null_key_in_the_path_reads_null(ctx) -> None:
    gone = Board.groups[Board.by_key["gone"]].ids
    got = run(gone.reversed_keys(limit=5), ctx)[0]
    assert is_null(got)
    assert "Board.groups" in repr(got)


# --- limit ---------------------------------------------------------------------


@pytest.mark.parametrize("name", COLLECTIONS)
def test_limit_zero_reads_nothing(ctx, name) -> None:
    ref = COLLECTIONS[name]
    _fill(ctx, ref, ["a"])
    assert _page(ctx, ref.keys(limit=0)) == []


def test_without_a_limit_a_page_reads_to_the_end(ctx) -> None:
    _fill(ctx, Board.log, ["a", "b", "c"])
    assert _page(ctx, Board.log.keys(after="a")) == ["b", "c"]


@pytest.mark.parametrize("limit", [-1, 1.5, True])
def test_a_limit_that_is_not_a_count_raises(ctx, limit) -> None:
    _fill(ctx, Board.log, ["a"])
    with pytest.raises(ValueError, match="limit"):
        run(KeysPage(Board.log, None, limit), ctx)


def test_a_null_limit_raises(ctx) -> None:
    _fill(ctx, Board.log, ["a"])
    with pytest.raises(ValueError, match="NULL"):
        run(Board.log.keys(limit=nu.Int(Board.scores["absent"])), ctx)


# --- surface -------------------------------------------------------------------


def test_without_arguments_keys_read_as_before(ctx) -> None:
    _fill(ctx, Board.log, ["b", "a"])
    assert list(run(Board.log.keys(), ctx)[0]) == ["b", "a"]
    assert list(run(Board.log.reversed_keys(), ctx)[0]) == ["a", "b"]


def test_a_page_is_a_typed_list(ctx) -> None:
    _fill(ctx, Board.log, ["a", "b", "c"])
    page = Board.log.keys(limit=2)
    assert isinstance(page, nu.List)
    assert run(page.len(), ctx)[0] == 2
    assert run(page.contains("b"), ctx)[0] is True


def test_a_view_that_cannot_seek_is_refused_at_build() -> None:
    with pytest.raises(TypeError, match="Kh57View does not page"):
        Board.points.keys(limit=3)

    class Flat(Shape):
        rows = DictRef.slot(int, view=FlatDictView)

    with pytest.raises(TypeError, match="FlatDictView does not page"):
        Flat.rows.reversed_keys(limit=3)


@pytest.mark.asyncio
async def test_pages_read_under_arun(ctx) -> None:
    _fill(ctx, Board.log, ["a", "b", "c"])
    run(Board.cursor.set("c"), ctx)
    got, _ = await arun(Board.log.reversed_keys(before=Board.cursor, limit=1), ctx)
    assert got == ["b"]


# --- first and last on a dict ------------------------------------------------------


def test_a_dict_reads_its_first_and_last_key_in_key_order(ctx) -> None:
    _fill(ctx, Board.scores, ["c", "a", "d", "b"])
    assert run(Board.scores.first(), ctx)[0] == "a"
    assert run(Board.scores.last(), ctx)[0] == "d"


def test_a_dict_first_is_null_when_nothing_is_there(ctx) -> None:
    assert is_null(run(Board.scores.first(), ctx)[0])
    assert run(Board.scores.first().fallback(""), ctx)[0] == ""
    assert is_null(run(Board.groups[Board.by_key["gone"]].ids.last(), ctx)[0])


def test_first_on_a_view_that_cannot_page_is_refused_at_build() -> None:
    with pytest.raises(TypeError, match="does not page"):
        Board.points.first()
