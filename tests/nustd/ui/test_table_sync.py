"""nustd.ui.table: the rules on plain values, then ``sync`` over a memory store.

The preset runs as a tab would: a recorder stands in for the browser, taking
every frame the program ships and firing notifies by hand. Two recorders on one
navigator are two tabs on one store, which is what "live" is about.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest

import nu
import nustd.kv
import nustd.ui
from nu.core.spans.bracket import _LifecycleBracket
from nustd.ui.table import values


# ---- the rules --------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "kind", "stored"),
    [
        ("12", "number", 12),
        (" 2.5 ", "number", 2.5),
        (3.0, "number", 3),
        ("abc", "number", None),
        ("", "number", None),
        (float("nan"), "number", None),
        (True, "number", 1),
        (True, "bool", True),
        ("Yes", "bool", True),
        ("x", "bool", True),
        ("no", "bool", False),
        (0, "bool", False),
        (float("nan"), "bool", False),
        ("1_000", "number", None),
        (True, "text", "true"),
        (False, "select", "false"),
        (None, "bool", False),
        (5, "text", "5"),
        (None, "text", ""),
        ("drama", "select", "drama"),
    ],
)
def test_coerce_stores_a_value_as_its_column_kind(value, kind, stored):
    out = values.coerce(value, kind)
    assert out == stored
    assert type(out) is type(stored)


def test_ordered_skips_ghosts_and_repeats_and_shows_orphans_last():
    assert values.ordered(["b", "x", "a", "b"], ["a", "b", "c"]) == ["b", "a", "c"]


def test_moved_and_inserted_count_the_others():
    assert values.moved(["a", "b", "c"], "a", 2) == ["b", "c", "a"]
    assert values.moved(["a", "b", "c"], "c", 0) == ["c", "a", "b"]
    assert values.moved(["a", "b"], "z", 0) == ["a", "b"]
    assert values.inserted(["a", "b"], 1, "n") == ["a", "n", "b"]
    assert values.inserted(["a", "b"], 99, "n") == ["a", "b", "n"]


def test_sorted_keys_puts_blanks_last_either_way():
    cells = {"a": {"y": 3}, "b": {"y": None}, "c": {"y": 1}, "d": {}, "e": {"y": "z"}}
    keys = ["a", "b", "c", "d", "e"]
    assert values.sorted_keys(keys, cells, "y", "asc", "_key") == ["c", "a", "e", "b", "d"]
    assert values.sorted_keys(keys, cells, "y", "desc", "_key") == ["e", "a", "c", "b", "d"]
    assert values.sorted_keys(["b", "a"], {}, "_key", "asc", "_key") == ["a", "b"]


def test_column_ops_on_plain_lists():
    cols = [{"key": "a", "label": "Column 2"}, "b"]
    added = values.column_added(cols, 1, "k")
    assert added[1] == {"key": "k", "label": "Column 3", "kind": "text"}
    assert [c["key"] for c in values.column_moved(added, "a", 2)] == ["k", "b", "a"]
    assert values.column_removed(added, "k") == [{"key": "a", "label": "Column 2"}, {"key": "b"}]
    assert values.column_set(cols, "b", "align", "right")[1] == {"key": "b", "align": "right"}
    assert values.kind_of([{"key": "n", "kind": "number"}], "n") == "number"
    assert values.kind_of([{"key": "n", "kind": "weird"}], "n") == "text"


def test_marked_names_the_row_or_owes_everything():
    state = values.marked(values.CLEAN, "rows", ("/", "rows", "a", "cells", "t"), 2)
    state = values.marked(state, "rows", ("/", "rows", "a"), 2)
    assert state["keys"] == ["a"]
    assert not state["all"]
    assert values.marked(state, "rows", ("/", "rows"), 2)["all"]
    assert values.marked(state, "order", ("/", "order", 0), 0)["order"]
    assert values.marked(state, "columns", ("/", "columns"), 0)["all"]


def test_settled_clears_only_what_was_shipped():
    owed = values.marked(values.CLEAN, "rows", ("/", "rows", "a"), 2)
    assert values.settled(owed, owed)["keys"] == []
    later = values.marked(owed, "rows", ("/", "rows", "b"), 2)
    assert values.settled(later, owed)["keys"] == ["a", "b"]


# ---- the preset -------------------------------------------------------------


class Sheet(nu.Shape):
    rows = nustd.kv.DictRef.slot(nustd.ui.table.Row)
    order = nustd.kv.ListRef.slot(str)
    columns = nustd.kv.ListRef.slot(object)
    sort = nustd.kv.ObjectRef.slot()


_COLUMNS = [
    {"key": "title", "label": "Title"},
    {"key": "year", "label": "Year", "kind": "number"},
    {"key": "seen", "label": "Seen", "kind": "bool"},
]


class SheetPage(nustd.ui.Page):
    table = nustd.ui.TableRef.slot(
        columns=_COLUMNS,
        row_key="id",
        editable=True,
        addable=True,
        deletable=True,
        draggable=True,
        columns_editable=True,
    )


class SheetApp(nustd.ui.Index):
    sheet = SheetPage.slot("/")


TABLE = SheetApp.sheet.table
PATH = ("sheet", "table")


class _Subscription:
    """A notify the test fires by hand, standing in for the browser."""

    def __init__(self) -> None:
        self.callbacks = []

    def bind(self, cb):
        self.callbacks.append(cb)

    def unbind(self, cb):
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self):
        self.callbacks = []

    def fire(self, payload):
        for cb in tuple(self.callbacks):
            cb(payload)


class _Tab(nustd.ui.Session):
    """One browser tab: every frame shipped, and a hand on its notifies."""

    def __init__(self) -> None:
        self.frames = []
        self.subscriptions = {}

    async def send(self, frame):
        self.frames.append(frame)

    async def aread(self, path):
        return None

    def subscribe(self, path):
        return self.subscriptions.setdefault(path, _Subscription())

    def fire(self, **payload):
        self.subscriptions[PATH].fire(payload)

    def ops(self):
        """(op, payload) per frame on the table."""
        out = []
        for f in self.frames:
            if f.ref != PATH:
                continue
            out.append((f.op, f.payload))
        return out

    def since(self, n):
        return self.ops()[n:]


_SEED = {
    "m1": {"title": "Arrival", "year": 2016, "seen": True},
    "m2": {"title": "Perfect Days", "year": 2023, "seen": False},
    "m3": {"title": "Dune", "year": 2024, "seen": True},
}


def _seed() -> nu.Nu:
    writes = [Sheet.rows[k].cells.set(v) for k, v in _SEED.items()]
    return nustd.kv.Transaction(nu.Sequential(*writes) >> Sheet.order.set(list(_SEED)), scope=Sheet)


async def _settle(check, deadline=3.0):
    waited = 0.0
    while waited < deadline:
        if check():
            return True
        await asyncio.sleep(0.02)
        waited += 0.02
    return False


async def _quiet(tab, gap=0.2):
    """Wait until ``tab`` has gone ``gap`` seconds without a frame.

    A tab's watchers start beside its first paint, and seeding the columns is
    itself a write the tab then repaints, so a test waits that out before it
    counts frames.
    """
    seen = -1
    while seen != len(tab.frames):
        seen = len(tab.frames)
        await asyncio.sleep(gap)


async def _read(ctx, term):
    out, _ = await nu.arun(nustd.kv.Snapshot(nu.Dict.of(v=term), scope=Sheet), ctx)
    return out["v"]


class _Hold(_LifecycleBracket):
    """Hands the Context its body runs in to the test, so tabs can share its store."""

    def __init__(self, body: nu.Nu, *, into: list) -> None:
        super().__init__(body)
        self._payload["into"] = into

    @asynccontextmanager
    async def _aopen(self, ctx):
        self._payload["into"].append(ctx)
        yield


class _Store:
    """One memory store with change notification, and any number of tabs on it."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.arms = []
        self.ctx = None

    async def open(self) -> _Store:
        held: list = []
        body = _seed() >> _Hold(nu.Delay(3600), into=held)
        self.arms.append(
            asyncio.create_task(nu.arun(nu.With(nustd.kv.memory_navigator(), body=body)))
        )
        assert await _settle(lambda: held)
        self.ctx = held[0]
        return self

    async def tab(self, *, quiet: bool = True) -> _Tab:
        tab = _Tab()
        kwargs = {"columns": Sheet.columns, "sort": Sheet.sort, "debounce": 0.05, **self.kwargs}
        program = nustd.ui.table.sync(TABLE, Sheet.rows, Sheet.order, **kwargs)
        self.arms.append(
            asyncio.create_task(nu.arun(program, self.ctx.bind(nustd.ui.Session, tab)))
        )
        assert await _settle(lambda: tab.ops())
        if quiet:
            await _quiet(tab)
        return tab

    async def order(self):
        return await _read(self.ctx, nu.ToList(Sheet.order))

    async def cells(self, key):
        return await _read(self.ctx, nu.ToDict(Sheet.rows[key].cells))

    async def has(self, key):
        return await _read(self.ctx, Sheet.rows.contains(key))

    async def close(self):
        # Tabs first, the store last, so no tab reads a store already gone.
        for arm in reversed(self.arms):
            arm.cancel()
            await asyncio.gather(arm, return_exceptions=True)


@pytest.fixture
async def store():
    s = await _Store().open()
    yield s
    await s.close()


@pytest.mark.timeout(30)
async def test_connect_paints_the_whole_table(store):
    tab = await store.tab()
    op, props = tab.ops()[0]
    assert op == "write"
    assert props["row_key"] == "id"
    assert [r["id"] for r in props["rows"]] == ["m1", "m2", "m3"]
    assert props["rows"][0] == {"id": "m1", "title": "Arrival", "year": 2016, "seen": True}
    assert [c["key"] for c in props["columns"]] == ["title", "year", "seen"]
    # The columns were never written, so the slot's seed them.
    assert [
        c["key"] for c in await _read(store.ctx, values.ColumnsOf(nu.ToList(Sheet.columns)))
    ] == [
        "title",
        "year",
        "seen",
    ]


@pytest.mark.timeout(30)
async def test_an_edit_is_stored_coerced_and_answered_with_its_row(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="edit", key="m2", row_index=1, column="year", value="1999", previous=2023)
    assert await _settle(lambda: tab.since(n))
    assert (await store.cells("m2"))["year"] == 1999
    op, payload = tab.since(n)[0]
    assert op == "set_row"
    assert payload["key"] == "m2"
    assert payload["row"] == {"id": "m2", "title": "Perfect Days", "year": 1999, "seen": False}


@pytest.mark.timeout(30)
async def test_an_add_stores_a_blank_row_under_a_fresh_key(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="add", index=1)
    assert await _settle(lambda: tab.since(n))
    order = await store.order()
    assert len(order) == 4
    assert order[0] == "m1" and order[2:] == ["m2", "m3"]
    key = order[1]
    assert len(key) == 8
    assert await store.cells(key) == {"title": "", "year": None, "seen": False}
    op, payload = tab.since(n)[0]
    assert (op, payload["index"], payload["row"]["id"]) == ("insert_row", 1, key)


@pytest.mark.timeout(30)
async def test_a_delete_deletes_and_drops_the_keys_from_the_order(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="delete", keys=["m1", "m3"], row_indexes=[0, 2])
    assert await _settle(lambda: tab.since(n))
    assert await store.order() == ["m2"]
    assert not await store.has("m1")
    assert tab.since(n)[0] == ("remove_rows", {"keys": ["m1", "m3"]})


@pytest.mark.timeout(30)
async def test_a_move_rewrites_only_the_order(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="move", key="m3", row_index=2, index=0)
    assert await _settle(lambda: tab.since(n))
    assert await store.order() == ["m3", "m1", "m2"]
    assert tab.since(n)[0] == ("set_order", {"keys": ["m3", "m1", "m2"]})


@pytest.mark.timeout(30)
async def test_a_sort_rewrites_the_order_and_stores_the_arrows_until_a_move(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="sort", sort_column="year", sort_direction="desc")
    assert await _settle(lambda: len(tab.since(n)) >= 2)
    assert await store.order() == ["m3", "m2", "m1"]
    assert await _read(store.ctx, Sheet.sort) == {"column": "year", "direction": "desc"}
    assert tab.since(n)[:2] == [
        ("set_order", {"keys": ["m3", "m2", "m1"]}),
        ("write", {"sort_column": "year", "sort_direction": "desc"}),
    ]
    # An edit of a sorted column keeps the rows where the arrows say.
    n = len(tab.ops())
    tab.fire(event="edit", key="m1", row_index=2, column="year", value=2030, previous=2016)
    assert await _settle(lambda: len(tab.since(n)) >= 2)
    assert await store.order() == ["m1", "m3", "m2"]
    # An edit of another column leaves the order alone and ships only the row.
    await _quiet(tab)
    n = len(tab.ops())
    tab.fire(event="edit", key="m2", row_index=2, column="title", value="PD", previous="")
    assert await _settle(lambda: tab.since(n))
    await asyncio.sleep(0.1)
    assert [op for op, _ in tab.since(n) if op != "set_row"] == []
    # A move puts the rows in an order of their own: no arrows.
    n = len(tab.ops())
    tab.fire(event="move", key="m2", row_index=2, index=0)
    assert await _settle(lambda: len(tab.since(n)) >= 2)
    assert (await _read(store.ctx, values.SortOf(Sheet.sort)))["column"] == ""
    assert ("write", {"sort_column": "", "sort_direction": "asc"}) in tab.since(n)


@pytest.mark.timeout(30)
async def test_a_request_for_a_row_that_is_gone_reships_the_table(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="edit", key="zz", row_index=0, column="title", value="x", previous="")
    assert await _settle(lambda: tab.since(n))
    op, props = tab.since(n)[0]
    assert op == "write"
    assert [r["id"] for r in props["rows"]] == ["m1", "m2", "m3"]
    assert not await store.has("zz")


@pytest.mark.timeout(30)
async def test_a_write_in_one_tab_repaints_the_other_by_row(store):
    one = await store.tab()
    two = await store.tab()
    n = len(two.ops())
    one.fire(
        event="edit", key="m1", row_index=0, column="title", value="Arrival (2016)", previous=""
    )
    assert await _settle(lambda: any(op == "set_row" for op, _ in two.since(n)))
    rows = [p["row"] for op, p in two.since(n) if op == "set_row"]
    assert rows[-1]["title"] == "Arrival (2016)"
    assert all(op != "write" for op, _ in two.since(n))

    n = len(two.ops())
    one.fire(event="delete", keys=["m2"], row_indexes=[1])
    assert await _settle(lambda: any(op == "remove_rows" for op, _ in two.since(n)))
    assert await _settle(lambda: any(op == "set_order" for op, _ in two.since(n)))
    orders = [p["keys"] for op, p in two.since(n) if op == "set_order"]
    assert orders[-1] == ["m1", "m3"]


@pytest.mark.timeout(30)
async def test_a_burst_is_shipped_once(store):
    one = await store.tab()
    two = await store.tab()
    n = len(two.ops())
    for year in range(2000, 2010):
        one.fire(event="edit", key="m1", row_index=0, column="year", value=year, previous=0)
    await asyncio.sleep(0.4)
    rows = [p["row"] for op, p in two.since(n) if op == "set_row"]
    assert rows[-1]["year"] == 2009
    assert len(rows) < 10


@pytest.mark.timeout(30)
async def test_a_flush_cut_short_by_the_next_burst_still_ships_its_rows(store):
    one = await store.tab()
    two = await store.tab()

    # A slow socket: a flush is still shipping when the next write lands, and
    # the debounce cancels it there.
    async def slow(frame):
        await asyncio.sleep(0.03)
        two.frames.append(frame)

    two.send = slow
    keys = ["m1", "m2", "m3"]
    for i in range(9):
        k = keys[i % 3]
        one.fire(event="edit", key=k, row_index=0, column="title", value=f"{k}-{i}", previous="")
        await asyncio.sleep(0.06)

    def shown():
        last = {}
        for op, p in two.ops():
            if op == "set_row":
                last[p["key"]] = p["row"]["title"]
            elif op == "write" and "rows" in p:
                last.update({r["id"]: r["title"] for r in p["rows"]})
        return last

    want = {"m1": "m1-6", "m2": "m2-7", "m3": "m3-8"}
    assert await _settle(lambda: shown() == want)


@pytest.mark.timeout(30)
async def test_a_store_write_from_outside_repaints_every_tab(store):
    one = await store.tab()
    n = len(one.ops())
    await nu.arun(
        nustd.kv.Transaction(Sheet.rows["m9"].cells.set({"title": "New"}), scope=Sheet), store.ctx
    )
    assert await _settle(lambda: any(op == "set_row" for op, _ in one.since(n)))
    (row,) = [p["row"] for op, p in one.since(n) if op == "set_row"]
    assert row == {"id": "m9", "title": "New"}


# ---- columns ----------------------------------------------------------------


@pytest.mark.timeout(30)
async def test_column_add_rename_move_align_are_stored_and_shipped(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="column_add", index=1)
    assert await _settle(lambda: tab.since(n))
    op, payload = tab.since(n)[0]
    assert op == "write"
    cols = payload["columns"]
    assert [c["label"] for c in cols] == ["Title", "Column 4", "Year", "Seen"]
    key = cols[1]["key"]

    async def step(**ev):
        # The last request's own live repaint first, so the next frame is the answer.
        await _quiet(tab)
        m = len(tab.ops())
        tab.fire(**ev)
        assert await _settle(lambda: tab.since(m))
        return tab.since(m)[0][1]["columns"]

    cols = await step(event="column_rename", column=key, column_index=1, label="Notes", previous="")
    assert cols[1] == {"key": key, "label": "Notes", "kind": "text"}
    cols = await step(event="column_move", column=key, column_index=1, index=3)
    assert [c["key"] for c in cols] == ["title", "year", "seen", key]
    cols = await step(
        event="column_align", column="year", column_index=1, align="right", previous=""
    )
    assert cols[1]["align"] == "right"
    stored = await _read(store.ctx, values.ColumnsOf(nu.ToList(Sheet.columns)))
    assert stored == cols


@pytest.mark.timeout(30)
async def test_column_delete_and_kind_rewrite_the_cells(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="column_kind", column="year", column_index=1, kind="text", previous="number")
    assert await _settle(lambda: tab.since(n))
    op, props = tab.since(n)[0]
    assert op == "write"
    assert props["columns"][1]["kind"] == "text"
    assert props["rows"][0]["year"] == "2016"
    assert (await store.cells("m1"))["year"] == "2016"

    await _quiet(tab)
    n = len(tab.ops())
    tab.fire(event="column_delete", column="seen", column_index=2)
    assert await _settle(lambda: tab.since(n))
    op, props = tab.since(n)[0]
    assert [c["key"] for c in props["columns"]] == ["title", "year"]
    assert "seen" not in await store.cells("m1")


@pytest.mark.timeout(30)
async def test_a_column_request_for_a_gone_column_reships_the_table(store):
    tab = await store.tab()
    n = len(tab.ops())
    tab.fire(event="column_rename", column="nope", column_index=0, label="x", previous="")
    assert await _settle(lambda: tab.since(n))
    op, props = tab.since(n)[0]
    assert op == "write" and "rows" in props


@pytest.mark.timeout(30)
async def test_fixed_columns_ignore_column_requests():
    s = await _Store(columns=None, sort=None).open()
    try:
        tab = await s.tab()
        _op, props = tab.ops()[0]
        assert "columns" not in props
        n = len(tab.ops())
        tab.fire(event="column_add", index=0)
        tab.fire(event="sort", sort_column="title", sort_direction="asc")
        assert await _settle(lambda: tab.since(n))
        await asyncio.sleep(0.2)
        assert all("columns" not in p for op, p in tab.since(n) if op == "write")
        # Arrows kept per tab, the order shared.
        assert ("write", {"sort_column": "title", "sort_direction": "asc"}) in tab.since(n)
        assert await s.order() == ["m1", "m3", "m2"]
    finally:
        await s.close()


@pytest.mark.timeout(30)
async def test_a_column_change_in_one_tab_repaints_the_other_whole(store):
    one = await store.tab()
    two = await store.tab()
    n = len(two.ops())
    one.fire(event="column_rename", column="title", column_index=0, label="Name", previous="Title")
    assert await _settle(lambda: any(op == "write" and "columns" in p for op, p in two.since(n)))
    (props,) = [p for op, p in two.since(n) if op == "write" and "columns" in p]
    assert props["columns"][0]["label"] == "Name"
    assert [r["id"] for r in props["rows"]] == ["m1", "m2", "m3"]


@pytest.mark.timeout(30)
async def test_arrows_set_and_cleared_in_one_tab_show_in_the_other(store):
    one = await store.tab()
    two = await store.tab()
    n = len(two.ops())
    one.fire(event="sort", sort_column="year", sort_direction="desc")
    arrows = ("write", {"sort_column": "year", "sort_direction": "desc"})
    assert await _settle(lambda: arrows in two.since(n))
    n = len(two.ops())
    one.fire(event="move", key="m2", row_index=1, index=0)
    cleared = ("write", {"sort_column": "", "sort_direction": "asc"})
    assert await _settle(lambda: cleared in two.since(n))


@pytest.mark.timeout(30)
async def test_the_last_column_is_never_deleted(store):
    tab = await store.tab()
    for c in ("seen", "year"):
        n = len(tab.ops())
        tab.fire(event="column_delete", column=c, column_index=0)
        assert await _settle(lambda n=n: tab.since(n))
        await _quiet(tab)
    n = len(tab.ops())
    tab.fire(event="column_delete", column="title", column_index=0)
    assert await _settle(lambda: tab.since(n))
    op, props = tab.since(n)[0]
    assert op == "write"
    assert [c["key"] for c in props["columns"]] == ["title"]
    stored = await _read(store.ctx, values.ColumnsOf(nu.ToList(Sheet.columns)))
    assert [c["key"] for c in stored] == ["title"]
    assert (await store.cells("m1"))["title"] == "Arrival"


@pytest.mark.timeout(30)
async def test_a_write_racing_the_first_paint_still_reaches_the_tab(store):
    tab = await store.tab(quiet=False)
    await nu.arun(
        nustd.kv.Transaction(Sheet.rows["m9"].cells.set({"title": "Late"}), scope=Sheet), store.ctx
    )

    def shown():
        for op, p in tab.ops():
            if op == "set_row" and p["key"] == "m9":
                return True
            if op == "write" and any(r.get("id") == "m9" for r in p.get("rows", [])):
                return True
        return False

    assert await _settle(shown)
