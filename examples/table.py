"""Table - an editable watchlist on TableRef.

Flow: double click or F2 to edit a cell, click a checkbox to flip it, pick a
genre from its list. Click to select (Cmd/Ctrl or Shift for more), Delete to
remove, Alt + Up / Down or right-click to move or insert, "Add row" to add, a
header to sort. The table never edits itself: each request lands here, is
checked, applied to the store, and only what changed is shipped back (one
row, the keys that went, or the order). A request that is turned down (an
empty title, a negative year, a row another tab removed) changes nothing, and
the status line says why.

The store keeps a row per key and the order apart from the rows, the layout
``nustd.ui.table.sync`` reads: an edit writes one cell, and a move or a sort
rewrites the order and no row. Each connection sees other tabs' changes when it
acts or reloads. ``examples/table_sync.py`` shows the preset over this layout:
no policy of its own, every tab kept live.

Run it and open http://localhost:8092:

    .venv/bin/python examples/table.py
"""

import nu
import nustd


_COLUMNS = [
    {"key": "id", "label": "ID", "width": "4rem"},
    {"key": "title", "label": "Title"},
    {"key": "year", "label": "Year", "kind": "number"},
    {"key": "seen", "label": "Seen", "kind": "bool"},
    {"key": "genre", "label": "Genre", "kind": "select", "options": ["drama", "scifi", "doc"]},
]

_FIELDS = [c["key"] for c in _COLUMNS]


# ---- UI ---------------------------------------------------------------------


class WatchColumn(nustd.ui.Column):
    table = nustd.ui.TableRef.slot(
        columns=_COLUMNS,
        label="Watchlist",
        row_key="id",
        selection="multi",
        editable=True,
        addable=True,
        deletable=True,
        draggable=True,
    )
    status = nustd.ui.TextRef.slot(value="Nothing selected")


class WatchCard(nustd.ui.Card):
    body = WatchColumn.slot(gap=3)


class Watchlist(nustd.ui.Page):
    heading = nustd.ui.HeadingRef.slot(label="Watchlist")
    intro = nustd.ui.TextRef.slot(
        value="Double click to edit, Delete to remove, Alt + arrows to move, a header to sort.",
    )
    card = WatchCard.slot(title="Movies")


class App(nustd.ui.Index):
    title: nustd.ui.TitleRef
    watchlist = Watchlist.slot("/")


TABLE = App.watchlist.card.body.table
STATUS = App.watchlist.card.body.status


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    # One row per key (its cells by column), and the keys in the order shown.
    rows = nustd.kv.DictRef.slot(nustd.ui.table.Row)
    order = nustd.kv.ListRef.slot(str)
    next_id = nustd.kv.IntRef.slot()
    # The order the rows are kept in: a column and a direction, or "" when a
    # move or an insert has put them in an order of their own.
    sort_column = nustd.kv.StrRef.slot()
    sort_direction = nustd.kv.StrRef.slot()


_SEED: dict[str, dict] = {
    "m1": {"title": "Arrival", "year": 2016, "seen": True, "genre": "scifi"},
    "m2": {"title": "Perfect Days", "year": 2023, "seen": False, "genre": "drama"},
    "m3": {"title": "Dune: Part Two", "year": 2024, "seen": True, "genre": "scifi"},
    "m4": {"title": "Free Solo", "year": 2018, "seen": False, "genre": "doc"},
}

_CELLS = [f for f in _FIELDS if f != "id"]


# ---- Ops --------------------------------------------------------------------


def has(key: nu.Nu) -> nu.Nu:
    """Whether a row with ``key`` is in the store."""
    return State.rows.contains(key)


def row(key: nu.Nu) -> nu.Nu:
    """The row at ``key`` as the table ships it, its key under ``id``."""
    cells = State.rows[key].cells
    return nu.Dict.of(id=key, **{f: cells[f] for f in _CELLS})


def every_row() -> nu.Nu:
    """Every row, in order."""
    return nu.Collect(nu.Map(nu.Iter(State.order), row))


def refusal(column: nu.Nu, value: nu.Nu) -> nu.Nu:
    """Why an edit is turned down, or "" when it is fine."""
    return nu.If(
        nu.Eq(column, "title"),
        nu.If(nu.Eq(nu.Str(value).strip(), ""), "A title can't be empty", ""),
        nu.If(
            nu.Eq(column, "year"),
            nu.If(nu.Float(value) < 0, "A year can't be negative", ""),
            "",
        ),
    )


def inserted(index: nu.Nu, key: nu.Nu) -> nu.Nu:
    """The order, ``key`` at ``index``."""
    keys = nu.List(State.order)
    return keys.slice(0, index) + nu.List.of(key) + keys.slice(index, None)


def without(keys: nu.Nu) -> nu.Nu:
    """The order without ``keys``."""
    return nu.Collect(nu.Filter(nu.Iter(State.order), lambda k: nu.Not(nu.List(keys).contains(k))))


def moved(key: nu.Nu, index: nu.Nu) -> nu.Nu:
    """The order, ``key`` at ``index`` among the others."""
    rest = nu.List(nu.Collect(nu.Filter(nu.Iter(State.order), lambda k: nu.Ne(k, key))))
    return rest.slice(0, index) + nu.List.of(key) + rest.slice(index, None)


def sorted_by(column: nu.Nu, direction: nu.Nu) -> nu.Nu:
    """The order, by ``column``."""
    return nu.Collect(
        nu.SortBy(
            nu.Iter(State.order),
            lambda k: State.rows[k].cells[column],
            reverse=nu.Eq(direction, "desc"),
        )
    )


# ---- Wire -------------------------------------------------------------------


# Seed once per store; every connection runs it first, and only the first finds
# the store empty.
init = nustd.kv.Transaction(
    nu.IfDo(
        State.next_id.missing(),
        nu.Sequential(*(State.rows[k].cells.set(cells) for k, cells in _SEED.items()))
        >> State.order.set(list(_SEED))
        >> State.next_id.set(len(_SEED) + 1)
        >> State.sort_column.set("")
        >> State.sort_direction.set("asc"),
    )
)

arrows = TABLE.set_sort(State.sort_column, State.sort_direction)

# The whole table: on connect, and when a request names a row that is gone.
ship = nustd.kv.Snapshot(TABLE.set_rows(every_row()) | arrows)

# A move or an insert puts the rows in an order of their own: no arrows.
unsorted = State.sort_column.set("")

sorting = nu.Ne(State.sort_column, "")

# An edit may change the sorted column: keep the rows in the order the arrows claim.
resort = nu.IfDo(sorting, State.order.set(sorted_by(State.sort_column, State.sort_direction)))


on_edit = nu.ReactForever(
    TABLE.on_edit(),
    lambda ev: nu.IfDo(
        nustd.kv.Snapshot(has(ev["key"])),
        nu.let(
            refusal(ev["column"], ev["value"]),
            lambda why: nu.IfDo(
                nu.Eq(why, ""),
                nustd.kv.Transaction(
                    State.rows[ev["key"]].cells[ev["column"]].set(ev["value"]) >> resort
                )
                >> nustd.kv.Snapshot(
                    TABLE.set_row(ev["key"], row(ev["key"]))
                    >> nu.IfDo(sorting, TABLE.set_order(nu.ToList(State.order)))
                )
                >> STATUS.set("Set " + nu.Str(ev["column"]) + " of " + nu.Str(ev["key"])),
                STATUS.set("Not changed: " + nu.Str(why)),
            ),
        ),
        ship >> STATUS.set("Not changed: that row is gone"),
    ),
)

on_add = nu.ReactForever(
    TABLE.on_add(),
    lambda ev: nu.let(
        nustd.kv.Snapshot("m" + nu.str(State.next_id)),
        lambda key: (
            nustd.kv.Transaction(
                State.rows[key].cells.set(
                    nu.Dict.of(title="Untitled", year=2025, seen=False, genre="drama")
                )
                >> State.order.set(inserted(ev["index"], key))
                >> State.next_id.set(State.next_id + 1)
                >> unsorted
            )
            >> nustd.kv.Snapshot(TABLE.insert_row(ev["index"], row(key)) >> arrows)
            >> STATUS.set("Added " + nu.Str(key))
        ),
    ),
)

on_delete = nu.ReactForever(
    TABLE.on_delete(),
    lambda ev: (
        nustd.kv.Transaction(
            nu.ForEachDo(ev["keys"], lambda k: nu.IfDo(has(k), State.rows.del_item(k)))
            >> State.order.set(without(ev["keys"]))
        )
        >> TABLE.remove_rows(ev["keys"])
        >> STATUS.set("Deleted " + nu.Str(", ").join(ev["keys"]))
    ),
)

on_move = nu.ReactForever(
    TABLE.on_move(),
    lambda ev: nu.IfDo(
        nustd.kv.Snapshot(has(ev["key"])),
        nustd.kv.Transaction(State.order.set(moved(ev["key"], ev["index"])) >> unsorted)
        >> nustd.kv.Snapshot(TABLE.set_order(nu.ToList(State.order)) >> arrows)
        >> STATUS.set("Moved " + nu.Str(ev["key"])),
        ship >> STATUS.set("Not moved: that row is gone"),
    ),
)

on_select = nu.ReactForever(
    TABLE.on_select(),
    lambda ev: STATUS.set(
        nu.If(
            nu.Eq(nu.Len(ev["keys"]), 0),
            "Nothing selected",
            "Selected " + nu.Str(", ").join(ev["keys"]),
        )
    ),
)

on_sort = nu.ReactForever(
    TABLE.on_sort(),
    lambda ev: (
        nustd.kv.Transaction(
            State.sort_column.set(ev["sort_column"])
            >> State.sort_direction.set(ev["sort_direction"])
            >> resort
        )
        >> nustd.kv.Snapshot(TABLE.set_order(nu.ToList(State.order)) >> arrows)
    ),
)

ui = (
    App.title.set("Watchlist")
    >> init
    >> ship
    >> (on_edit | on_add | on_delete | on_move | on_select | on_sort)
)


app = nu.With(
    nustd.kv.memory_navigator(),
    body=nustd.ui.serve(App, nustd.kv.auto_flow_atomic(ui), port=8092),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
