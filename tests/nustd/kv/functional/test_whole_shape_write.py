"""A whole Shape value keeps every slot's declared view.

Verifies:
- ``set`` and ``init`` of a row holding a ring, a log dict and an ordered
  dict lay each slot out in its own view: the ring pages and appends, the
  log and the ordered dict read ``first``/``last`` and pages.
- A whole mapping of such rows does the same one level down, keeps the
  rows' order in an ordered parent, and a second ``set`` replaces the first.
- Rows with only plain slots still write and read back whole.
- A list of such rows written whole raises TypeError, nothing lands.
- The async path and a sqlite store behave the same.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Shape, arun, run
from nu.lang import is_null
from nustd.kv import (
    DictRef,
    ListRef,
    LogDictRef,
    OrderedDictRef,
    RingRef,
    Snapshot,
    StrRef,
    Transaction,
    sqlite_navigator,
)


class Row(Shape):
    name = StrRef.slot()
    out = RingRef.slot(list, capacity=3)
    log = LogDictRef.slot(bool)
    od = OrderedDictRef.slot(bool)


class Plain(Shape):
    name = StrRef.slot()
    tags = DictRef.slot(bool)


class S(Shape):
    rows = DictRef.slot(Row)
    ordered = OrderedDictRef.slot(Row)
    plain = DictRef.slot(Plain)
    listed = ListRef.slot(Row)


R = S.rows["r"]
ROW = {"name": "a", "out": [[1]], "log": {"x": True}, "od": {"y": True, "z": True}}


def _reads(row) -> nu.Nu:
    return nu.List.of(
        nu.list(row.out.entries()),
        row.log.keys(limit=5),
        row.log.last(),
        row.od.first(),
        row.od.last(),
        row.extract(),
    )


def _check(got) -> None:
    entries, log_keys, log_last, od_first, od_last, whole = got
    assert [(seq, list(e)) for seq, e in entries] == [(0, [1]), (1, [2])]
    assert list(log_keys) == ["x"]
    assert log_last == "x"
    assert (od_first, od_last) == ("y", "z")
    assert whole == {**ROW, "out": [[1], [2]]}


@pytest.mark.parametrize("verb", ["set", "init"])
def test_a_whole_row_lays_each_slot_out_in_its_view(ctx, verb) -> None:
    run(getattr(R, verb)(ROW), ctx)
    run(R.out.append([2]), ctx)  # a ring laid out as a list would refuse this
    _check(run(_reads(R), ctx)[0])


def test_a_whole_mapping_of_rows_lays_out_each_row(ctx) -> None:
    run(S.rows.set({"a": {"name": "plain"}, "b": ROW}), ctx)
    run(S.rows["b"].out.append([2]), ctx)
    _check(run(_reads(S.rows["b"]), ctx)[0])
    assert run(S.rows["a"].extract(), ctx)[0] == {"name": "plain"}


def test_an_ordered_parent_keeps_the_rows_order(ctx) -> None:
    run(S.ordered.set({"c": {"name": "c"}, "a": ROW, "b": {"od": {"q": True}}}), ctx)
    assert run(nu.list(S.ordered.keys()), ctx)[0] == ["c", "a", "b"]
    assert run(S.ordered["b"].od.first(), ctx)[0] == "q"
    assert run(S.ordered["a"].log.last(), ctx)[0] == "x"


def test_a_second_set_replaces_the_row(ctx) -> None:
    run(R.set(ROW), ctx)
    run(R.set({"od": {"w": True}}), ctx)
    assert run(R.od.first(), ctx)[0] == "w"
    assert is_null(run(R.log.last(), ctx)[0])
    assert run(R.extract(), ctx)[0] == {"od": {"w": True}}


def test_plain_rows_write_and_read_back_whole(ctx) -> None:
    run(S.plain.set({"p": {"name": "n", "tags": {"t": True}}}), ctx)
    assert run(S.plain.extract(), ctx)[0] == {"p": {"name": "n", "tags": {"t": True}}}
    assert list(run(S.plain["p"].tags.keys(limit=5), ctx)[0]) == ["t"]


def test_a_list_of_laid_out_rows_is_refused_whole(ctx) -> None:
    with pytest.raises(TypeError, match="ordered, log or ring slot"):
        run(S.listed.set([ROW]), ctx)
    assert run(S.listed.exists(), ctx)[0] is False


def test_a_list_of_plain_rows_still_writes(ctx) -> None:
    run(S.listed.set([{"name": "a"}]), ctx)
    assert run(S.listed.extract(), ctx)[0] == [{"name": "a"}]


def test_the_async_path_lays_out_the_same(ctx) -> None:
    async def go() -> object:
        await arun(R.set(ROW), ctx)
        await arun(R.out.append([2]), ctx)
        return (await arun(_reads(R), ctx))[0]

    _check(asyncio.run(asyncio.wait_for(go(), 5.0)))


def test_sqlite_lays_out_the_same(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    run(nu.With(sqlite_navigator(path), body=Transaction(R.set(ROW))))
    run(nu.With(sqlite_navigator(path), body=Transaction(R.out.append([2]))))
    _check(run(nu.With(sqlite_navigator(path), body=Snapshot(_reads(R))))[0])
