"""TableRef: frames out, and notifies in where each ``on_*`` takes only its own kind.

A fake subscription fires every payload the moment a reaction binds, so
``React`` runs its body on the first one its filter lets through.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session, TableRef
from nustd.ui.nudle import Index, Page
from nustd.ui.refs import TextRef


class ShelfPage(Page):
    table = TableRef.slot(columns=["title"], clickable_rows=True)
    out = TextRef.slot()


class ShelfApp(Index):
    shelf = ShelfPage.slot("/")


class _Sub:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = payloads

    def bind(self, cb) -> None:
        for p in self.payloads:
            cb(p)

    def unbind(self, cb) -> None:
        pass

    def close(self) -> None:
        pass


class _Session:
    def __init__(self, *payloads: object) -> None:
        self.frames: list = []
        self.payloads = list(payloads)

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    def subscribe(self, path: tuple[str, ...]) -> _Sub:
        return _Sub(self.payloads)


_SORT = {"event": "sort", "sort_column": "title", "sort_direction": "desc"}
_ROW = {"event": "row", "row_index": 3}


def _run(term: nu.Nu, sess: _Session) -> None:
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))


def test_row_click_skips_a_sort():
    sess = _Session(_SORT, _ROW)
    out = ShelfApp.shelf.out
    _run(
        nu.React(ShelfApp.shelf.table.on_row_click(), lambda c: out.set(nu.str(c["row_index"]))),
        sess,
    )
    assert [f.payload for f in sess.frames] == ["3"]


def test_sort_skips_a_row_click():
    sess = _Session(_ROW, _SORT)
    out = ShelfApp.shelf.out
    _run(
        nu.React(
            ShelfApp.shelf.table.on_sort(),
            lambda s: out.set(nu.Str(s["sort_column"]) + " " + nu.Str(s["sort_direction"])),
        ),
        sess,
    )
    assert [f.payload for f in sess.frames] == ["title desc"]


# --- the editable table -------------------------------------------------------


class GridPage(Page):
    table = TableRef.slot(
        columns=["id", {"key": "title", "label": "Title", "kind": "text"}],
        row_key="id",
        selection="multi",
        editable=True,
        addable=True,
        deletable=True,
        draggable=True,
    )
    out = TextRef.slot()


class GridApp(Index):
    grid = GridPage.slot("/")


_KINDS = (
    "sort",
    "row",
    "select",
    "edit",
    "add",
    "delete",
    "move",
    "column_add",
    "column_delete",
    "column_rename",
    "column_move",
    "column_kind",
    "column_align",
)
_ON = {"sort": "on_sort", "row": "on_row_click"}


def _echo(change) -> nu.Nu:
    """React once, writing the event's ``event`` field to ``out``."""
    return nu.React(change, lambda ev: GridApp.grid.out.set(nu.Str(ev["event"])))


def test_slot_defaults_keep_the_old_props():
    props = nu.tree.payload(ShelfPage.table)["props"]
    assert props == {
        "columns": ["title"],
        "label": "Table",
        "striped": True,
        "dense": False,
        "max_rows": 0,
        "sort_column": "",
        "sort_direction": "asc",
        "clickable_rows": True,
        "row_key": "",
        "selection": "none",
        "editable": False,
        "addable": False,
        "deletable": False,
        "draggable": False,
        "columns_editable": False,
    }


def test_slot_takes_mapping_columns_and_copies_them():
    column = {"key": "year", "kind": "number"}

    class Mixed(Page):
        table = TableRef.slot(columns=["title", column])

    column["kind"] = "text"
    props = nu.tree.payload(Mixed.table)["props"]
    assert props["columns"] == ["title", {"key": "year", "kind": "number"}]


@pytest.mark.parametrize(
    ("term", "payload"),
    [
        (GridApp.grid.table.set_rows([{"id": "a"}]), {"rows": [{"id": "a"}]}),
        (GridApp.grid.table.set_selected(["a", "b"]), {"selected": ["a", "b"]}),
        (
            GridApp.grid.table.set_sort("title", "desc"),
            {"sort_column": "title", "sort_direction": "desc"},
        ),
        (GridApp.grid.table.clear(), {"rows": []}),
    ],
)
def test_writes_merge_on_the_table_path(term, payload):
    sess = _Session()
    _run(term, sess)
    (frame,) = sess.frames
    assert (frame.op, frame.ref, frame.payload) == ("write", ("grid", "table"), payload)


def test_append_takes_a_mapping_row():
    sess = _Session()
    _run(GridApp.grid.table.append({"id": "a", "title": "A"}), sess)
    (frame,) = sess.frames
    assert (frame.op, frame.payload) == ("append", {"id": "a", "title": "A"})


@pytest.mark.parametrize("name", _KINDS)
def test_each_on_takes_only_its_own_event(name):
    others = [{"event": e} for e in _KINDS if e != name]
    sess = _Session(*others, {"event": name, "key": "a"})
    _run(_echo(getattr(GridApp.grid.table, _ON.get(name, f"on_{name}"))()), sess)
    assert [f.payload for f in sess.frames] == [name]


def test_on_change_takes_every_event():
    sess = _Session({"event": "move", "key": "a", "index": 0})
    _run(_echo(GridApp.grid.table.on_change()), sess)
    assert [f.payload for f in sess.frames] == ["move"]


def test_an_edit_reads_its_fields():
    sess = _Session(
        {
            "event": "edit",
            "key": "a",
            "row_index": 0,
            "column": "title",
            "value": "B",
            "previous": "A",
        }
    )
    _run(
        nu.React(
            GridApp.grid.table.on_edit(),
            lambda ev: GridApp.grid.out.set(
                nu.Str(ev["key"]) + "." + nu.Str(ev["column"]) + "=" + nu.Str(ev["value"])
            ),
        ),
        sess,
    )
    assert [f.payload for f in sess.frames] == ["a.title=B"]


# --- row-level ops ------------------------------------------------------------


@pytest.mark.parametrize(
    ("term", "payload"),
    [
        (
            GridApp.grid.table.set_row("m1", {"id": "m1", "title": "B"}),
            {"op": "set_row", "key": "m1", "row": {"id": "m1", "title": "B"}},
        ),
        (
            GridApp.grid.table.set_row("1", ["m1", "B"]),
            {"op": "set_row", "key": "1", "row": ["m1", "B"]},
        ),
        (
            GridApp.grid.table.insert_row(2, {"id": "m9"}),
            {"op": "insert_row", "index": 2, "row": {"id": "m9"}},
        ),
        (GridApp.grid.table.remove_row("m1"), {"op": "remove_rows", "keys": ["m1"]}),
        (
            GridApp.grid.table.remove_rows(["m1", "m2"]),
            {"op": "remove_rows", "keys": ["m1", "m2"]},
        ),
        (GridApp.grid.table.set_order(["m2", "m1"]), {"op": "set_order", "keys": ["m2", "m1"]}),
    ],
)
def test_row_ops_patch_the_table_path(term, payload):
    sess = _Session()
    _run(term, sess)
    (frame,) = sess.frames
    assert (frame.op, frame.ref, frame.payload) == ("patch", ("grid", "table"), payload)


def test_set_columns_writes_the_columns():
    sess = _Session()
    _run(GridApp.grid.table.set_columns(["id", {"key": "year", "kind": "number"}]), sess)
    (frame,) = sess.frames
    assert (frame.op, frame.payload) == (
        "write",
        {"columns": ["id", {"key": "year", "kind": "number"}]},
    )


def test_row_ops_take_terms():
    sess = _Session({"event": "delete", "keys": ["m2"], "row_indexes": [1]})
    table = GridApp.grid.table
    _run(
        nu.React(
            table.on_delete(),
            lambda ev: table.remove_row(ev["keys"][0]) >> table.set_order(ev["keys"]),
        ),
        sess,
    )
    assert [(f.op, f.payload) for f in sess.frames] == [
        ("patch", {"op": "remove_rows", "keys": ["m2"]}),
        ("patch", {"op": "set_order", "keys": ["m2"]}),
    ]


def test_patch_frames_encode_with_their_op():
    sess = _Session()
    _run(GridApp.grid.table.set_order(["a"]), sess)
    (frame,) = sess.frames
    assert frame.to_dict()["op"] == "patch"


def test_columns_editable_is_a_slot_flag():
    class Columns(Page):
        table = TableRef.slot(columns=["a"], columns_editable=True)

    assert nu.tree.payload(Columns.table)["props"]["columns_editable"] is True


def test_a_column_rename_reads_its_fields():
    sess = _Session(
        {"event": "column_kind", "column": "title", "column_index": 1, "kind": "number"},
        {
            "event": "column_rename",
            "column": "title",
            "column_index": 1,
            "label": "Name",
            "previous": "Title",
        },
    )
    _run(
        nu.React(
            GridApp.grid.table.on_column_rename(),
            lambda ev: GridApp.grid.out.set(
                nu.Str(ev["column"]) + ": " + nu.Str(ev["previous"]) + " -> " + nu.Str(ev["label"])
            ),
        ),
        sess,
    )
    assert [f.payload for f in sess.frames] == ["title: Title -> Name"]


def test_a_column_reshape_over_list_rows_is_one_frame():
    sess = _Session()
    columns = ["b", {"key": "a", "label": "A", "align": "center"}]
    _run(GridApp.grid.table.set({"columns": columns, "rows": [[2, 1]]}), sess)
    (frame,) = sess.frames
    assert (frame.op, frame.payload) == ("write", {"columns": columns, "rows": [[2, 1]]})


def test_set_columns_alone_leaves_the_rows():
    sess = _Session()
    _run(GridApp.grid.table.set_columns(["b", "a"]), sess)
    assert [(f.op, f.payload) for f in sess.frames] == [("write", {"columns": ["b", "a"]})]
