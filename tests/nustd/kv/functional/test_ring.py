"""Functional tests for RingRef: a capped log of whole entries.

Verifies:
- The slot needs a capacity (``capacity=`` or ``view=RingView.of(n)``); an
  annotation, a capacity-less view and a container ref value are refused.
- Append, extend and clear keep the newest ``capacity`` entries, stored whole.
- The sequence reads (``[i]``, slices, iter, reversed, len, contains, index,
  count, first/last) read them back oldest first, positions from the oldest
  kept.
- Writes at a position are not there: no set_at, del_at, insert, pop,
  remove or reverse, and ``ring[i]`` is a read, not a ref.
- A whole-ring set and ``init`` go through the parent.
- A never-written ring raises on reads; one under a NULL key raises.
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


def test_reads_by_position_count_from_the_oldest_kept(ctx) -> None:
    run(OUT.extend([["a"], ["b"], ["c"], ["d"]]), ctx)
    assert run(OUT[0], ctx)[0] == ["b"]
    assert run(OUT[-1], ctx)[0] == ["d"]
    assert run(OUT[1:], ctx)[0] == [["c"], ["d"]]
    assert run(OUT[::-1], ctx)[0] == [["d"], ["c"], ["b"]]
    assert run(OUT.first_elem(), ctx)[0] == ["b"]
    assert run(OUT.last_elem(), ctx)[0] == ["d"]
    with pytest.raises(IndexError):
        run(OUT[3], ctx)


def test_membership_index_and_count(ctx) -> None:
    run(LINES.extend(["a", "b", "b"]), ctx)
    assert run(LINES.contains("b"), ctx)[0] is True
    assert run(LINES.contains("a"), ctx)[0] is False
    assert run(LINES.index("b"), ctx)[0] == 0
    assert run(LINES.count("b"), ctx)[0] == 2
    with pytest.raises(ValueError):
        run(LINES.index("a"), ctx)


def test_an_entry_read_is_typed_by_the_declared_value(ctx) -> None:
    run(LINES.append("x"), ctx)
    assert type(LINES[0]) is nu.Str
    assert type(LINES[0:1]) is nu.List
    assert run(LINES[0].upper(), ctx)[0] == "X"


def test_clear_empties_the_ring_and_appends_go_on(ctx) -> None:
    run(LINES.extend(["a", "b"]), ctx)
    run(LINES.clear(), ctx)
    assert run(LINES.len(), ctx)[0] == 0
    assert run(LINES.exists(), ctx)[0] is True
    run(LINES.append("c"), ctx)
    assert run(LINES.extract(), ctx)[0] == ["c"]


@pytest.mark.parametrize("name", ["set_at", "del_at", "insert", "pop", "remove", "reverse"])
def test_no_write_at_a_position(name) -> None:
    assert not hasattr(OUT, name)


@pytest.mark.parametrize("name", ["on_child_change", "on_children_change", "on_descendants_change"])
def test_no_child_watch(name) -> None:
    """Entries have no addresses, so the ring offers only the watch it can serve."""
    assert not hasattr(OUT, name)


def test_the_ring_is_watched_whole_and_written_whole() -> None:
    from nu.core.reactive import OnChange
    from nu.domains.shape import MutableCollectionForm, ReactiveCollectionForm

    assert isinstance(OUT.on_change(), OnChange)
    assert isinstance(OUT, MutableCollectionForm)
    assert not isinstance(OUT, ReactiveCollectionForm)


def test_a_position_is_a_read_not_a_ref() -> None:
    assert not isinstance(OUT[0], nu.lang.Ref)


def test_the_view_refuses_a_write_at_a_position(ctx) -> None:
    run(LINES.append("a"), ctx)
    view = run(LINES, ctx)[0]
    with pytest.raises(TypeError):
        view[0] = "b"
    with pytest.raises(TypeError):
        del view[0]


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
        run(OUT.len(), ctx)
    with pytest.raises(ContainerNotFoundError):
        run(OUT[0], ctx)
    assert is_null(run(OUT.extract(), ctx)[0])


def test_a_ring_under_a_null_key_raises(ctx) -> None:
    gone = Exec.cell_runs[Exec.by_key["gone"]].out
    with pytest.raises(NullAddressError):
        run(gone.len(), ctx)
    with pytest.raises(NullAddressError):
        run(gone[0], ctx)
    with pytest.raises(NullAddressError):
        run(gone.exists(), ctx)


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
    got = run(nu.With(sqlite_navigator(path), body=Snapshot(OUT.extract())))[0]
    assert [list(entry) for entry in got] == [[1.5, "stderr", "boom"], [2.5, "stdout", "ok"]]
