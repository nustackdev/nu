"""Functional tests for RingRef: a capped log of whole entries.

Verifies:
- The slot needs a capacity (``capacity=`` or ``view=RingView.of(n)``); an
  annotation, a capacity-less view and a container ref value are refused.
- Append and extend keep the newest ``capacity`` entries, stored whole.
- iter, reversed, len and a page of entries read them back in order.
- A whole-ring set and ``init`` go through the parent.
- A never-written ring pages empty; one under a NULL key raises.
- A watch hears appends, and a sqlite store keeps compound entries whole.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Shape, arun, run
from nu.lang import is_null
from nustd.kv import (
    DictRef,
    NullAddressError,
    OrderedDictRef,
    RingRef,
    Snapshot,
    Transaction,
    memory_navigator,
    sqlite_navigator,
)
from virtuals.container import ContainerNotFoundError
from virtuals.views import DictView, RingView


class CellRun(Shape):
    out = RingRef.slot(list, capacity=3)
    lines = RingRef.slot(str, view=RingView.of(2))


class Exec(Shape):
    by_key = DictRef.slot(str)
    cell_runs = DictRef.slot(CellRun)


OUT = Exec.cell_runs["r1"].out
LINES = Exec.cell_runs["r1"].lines


# --- the slot -----------------------------------------------------------------


def test_the_slot_carries_its_capacity() -> None:
    assert CellRun.out._payload["type_marker"] is RingView.of(3)
    assert CellRun.lines._payload["type_marker"] is RingView.of(2)


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"capacity": 3, "view": RingView.of(3)}, {"view": RingView}, {"view": DictView}],
)
def test_a_slot_without_one_capacity_is_refused(kwargs) -> None:
    with pytest.raises(TypeError, match="capacity"):
        RingRef.slot(str, **kwargs)


def test_a_bad_capacity_is_refused() -> None:
    with pytest.raises(ValueError, match="capacity"):
        RingRef.slot(str, capacity=0)


def test_an_annotation_is_refused() -> None:
    with pytest.raises(TypeError, match="capacity"):

        class Bad(Shape):
            out: RingRef[str]


def test_a_container_ref_value_is_refused() -> None:
    with pytest.raises(TypeError, match="Use a Shape"):
        RingRef.slot(OrderedDictRef[str, bool], capacity=3)


# --- writes and reads ---------------------------------------------------------


def test_append_keeps_the_newest_entries_whole(ctx) -> None:
    for i in range(5):
        run(OUT.append([float(i), "stdout", f"line {i}"]), ctx)
    assert run(OUT.iter().to_list(), ctx)[0] == [
        [2.0, "stdout", "line 2"],
        [3.0, "stdout", "line 3"],
        [4.0, "stdout", "line 4"],
    ]
    assert run(OUT.len(), ctx)[0] == 3


def test_extend_appends_in_order_and_drops_once(ctx) -> None:
    run(LINES.extend(["a", "b", "c"]), ctx)
    assert run(LINES.iter().to_list(), ctx)[0] == ["b", "c"]
    assert run(LINES.reversed().to_list(), ctx)[0] == ["c", "b"]


def test_entries_page_by_sequence_number(ctx) -> None:
    run(OUT.extend([["a"], ["b"], ["c"], ["d"]]), ctx)
    assert run(OUT.entries(), ctx)[0] == [(1, ["b"]), (2, ["c"]), (3, ["d"])]
    assert run(OUT.entries(after=1, limit=1), ctx)[0] == [(2, ["c"])]
    assert run(OUT.entries(after=3), ctx)[0] == []


def test_a_reader_that_fell_behind_resumes_at_the_oldest_kept(ctx) -> None:
    run(OUT.extend([["a"], ["b"], ["c"], ["d"], ["e"]]), ctx)
    assert run(OUT.entries(after=0, limit=2), ctx)[0] == [(2, ["c"]), (3, ["d"])]


def test_a_bad_cursor_is_refused(ctx) -> None:
    run(OUT.append(["a"]), ctx)
    with pytest.raises(TypeError, match="sequence number"):
        run(OUT.entries(after="0"), ctx)
    with pytest.raises(ValueError, match="limit"):
        run(OUT.entries(limit=-1), ctx)


def test_a_whole_ring_set_and_init_go_through_the_parent(ctx) -> None:
    run(LINES.init(["a", "b", "c"]), ctx)
    assert run(LINES.iter().to_list(), ctx)[0] == ["b", "c"]
    run(LINES.init(["x"]), ctx)  # already there: left alone
    assert run(LINES.iter().to_list(), ctx)[0] == ["b", "c"]
    run(LINES.set(["x"]), ctx)
    assert run(LINES.iter().to_list(), ctx)[0] == ["x"]
    assert run(LINES.extract(), ctx)[0] == ["x"]


def test_a_never_written_ring(ctx) -> None:
    assert run(OUT.exists(), ctx)[0] is False
    with pytest.raises(ContainerNotFoundError):
        run(OUT.entries(), ctx)
    assert is_null(run(OUT.extract(), ctx)[0])


def test_a_ring_under_a_null_key_raises(ctx) -> None:
    gone = Exec.cell_runs[Exec.by_key["gone"]].out
    with pytest.raises(NullAddressError):
        run(gone.entries(), ctx)
    with pytest.raises(NullAddressError):
        run(gone.exists(), ctx)


@pytest.mark.parametrize("arg", ["after", "limit"])
def test_a_null_page_arg_is_refused_before_the_view(ctx, arg) -> None:
    run(OUT.append(["a"]), ctx)
    with pytest.raises(ValueError, match=rf"entries\({arg}=\) read NULL"):
        run(OUT.entries(**{arg: Exec.by_key["gone"]}), ctx)


@pytest.mark.asyncio
async def test_a_null_page_arg_is_refused_before_the_view_async(ctx) -> None:
    await arun(OUT.append(["a"]), ctx)
    with pytest.raises(ValueError, match=r"entries\(after=\) read NULL"):
        await arun(OUT.entries(after=Exec.by_key["gone"]), ctx)


# --- watches and stores -------------------------------------------------------


@pytest.mark.asyncio
async def test_a_watch_hears_an_append() -> None:
    heard: list = []

    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    def keep(value: object) -> None:
        heard.append(value)

    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    async def wait_heard(count: int) -> None:
        while len(heard) < count:
            await asyncio.sleep(0.005)

    follow = Snapshot(nu.ReactEvery(OUT.on_change(), lambda key: keep(key)))
    tree = nu.With(
        memory_navigator(),
        body=Transaction(OUT.append(["a"]))
        >> nu.Race(follow, nu.DelayedDo(0.02, Transaction(OUT.append(["b"]))) >> wait_heard(1)),
    )
    await asyncio.wait_for(arun(tree), 5.0)
    assert heard


def test_sqlite_keeps_compound_entries_whole(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    write = Transaction(OUT.extend([[1.5, "stderr", "boom"], [2.5, "stdout", "ok"]]))
    run(nu.With(sqlite_navigator(path), body=write))
    got = run(nu.With(sqlite_navigator(path), body=Snapshot(OUT.entries())))[0]
    assert [(seq, list(entry)) for seq, entry in got] == [
        (0, [1.5, "stderr", "boom"]),
        (1, [2.5, "stdout", "ok"]),
    ]
