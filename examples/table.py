"""Table - an editable watchlist on TableRef.

Flow: the rows are a list of dicts in the store. Double click or F2 to edit a
cell, click a checkbox to flip it, pick a genre from its list. Click to
select (Cmd/Ctrl or Shift for more), Delete to remove, Alt + Up / Down or
right-click to move or insert, "Add row" to add, a header to sort. The table
never edits itself: each request lands here, is checked, applied to the
store, and the rows are shipped again. A request that is turned down (an
empty title, a negative year, a row another tab removed) changes nothing, and
the status line says why. Each connection sees fresh rows when it acts or
reloads; other tabs are not pushed.

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
    # The rows as TableRef ships them, in display order, keyed by `id`.
    rows = nustd.kv.ObjectRef.slot()
    next_id = nustd.kv.IntRef.slot()
    # The order the rows are kept in: a column and a direction, or "" when a
    # move or an insert has put them in an order of their own.
    sort_column = nustd.kv.StrRef.slot()
    sort_direction = nustd.kv.StrRef.slot()


_SEED: list[dict] = [
    {"id": "m1", "title": "Arrival", "year": 2016, "seen": True, "genre": "scifi"},
    {"id": "m2", "title": "Perfect Days", "year": 2023, "seen": False, "genre": "drama"},
    {"id": "m3", "title": "Dune: Part Two", "year": 2024, "seen": True, "genre": "scifi"},
    {"id": "m4", "title": "Free Solo", "year": 2018, "seen": False, "genre": "doc"},
]


# ---- Ops --------------------------------------------------------------------


def has(key: nu.Nu) -> nu.Nu:
    """Whether a row with ``key`` is in the store."""
    return nustd.kv.Snapshot(
        nu.List(nu.Collect(nu.Map(nu.Iter(State.rows), lambda r: r["id"]))).contains(key)
    )


def edited(key: nu.Nu, column: nu.Nu, value: nu.Nu) -> nu.Nu:
    """Every row, the one at ``key`` with ``column`` set to ``value``."""

    def edit(r: nu.Nu) -> nu.Nu:
        return nu.Dict.of(**{f: nu.If(nu.Eq(column, f), value, r[f]) for f in _FIELDS})

    return nu.Collect(nu.Map(nu.Iter(State.rows), lambda r: nu.If(nu.Eq(r["id"], key), edit(r), r)))


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


def inserted(index: nu.Nu) -> nu.Nu:
    """Every row, a fresh one at ``index``."""
    rows = nu.List(State.rows)
    fresh = nu.Dict.of(
        id="m" + nu.str(State.next_id),
        title="Untitled",
        year=2025,
        seen=False,
        genre="drama",
    )
    return rows.slice(0, index) + nu.List.of(fresh) + rows.slice(index, None)


def deleted(keys: nu.Nu) -> nu.Nu:
    """Every row whose key is not in ``keys``."""
    return nu.Collect(
        nu.Filter(nu.Iter(State.rows), lambda r: nu.Not(nu.List(keys).contains(r["id"])))
    )


def moved(key: nu.Nu, index: nu.Nu) -> nu.Nu:
    """Every row, the one at ``key`` at ``index`` among the others."""

    def place(rest: nu.ObjectRef) -> nu.Nu:
        others = nu.List(rest)
        row = nu.List(nu.Collect(nu.Filter(nu.Iter(State.rows), lambda r: nu.Eq(r["id"], key))))
        # Gone since the check (another tab deleted it): nothing to move.
        return nu.IfDo(
            row.len() > 0,
            State.rows.set(others.slice(0, index) + nu.List.of(row[0]) + others.slice(index, None)),
        )

    rest = nu.Collect(nu.Filter(nu.Iter(State.rows), lambda r: nu.Ne(r["id"], key)))
    return nu.let(rest, place)


def sorted_by(column: nu.Nu, direction: nu.Nu) -> nu.Nu:
    """Every row, ordered by ``column``."""
    return nu.Collect(
        nu.SortBy(nu.Iter(State.rows), lambda r: r[column], reverse=nu.Eq(direction, "desc"))
    )


# ---- Wire -------------------------------------------------------------------


# Seed once per store; every connection runs it first, and only the first finds
# the store empty.
init = nustd.kv.Transaction(
    nu.IfDo(
        State.rows.missing(),
        State.rows.set(_SEED)
        >> State.next_id.set(len(_SEED) + 1)
        >> State.sort_column.set("")
        >> State.sort_direction.set("asc"),
    )
)

ship = nustd.kv.Snapshot(
    TABLE.set_rows(State.rows) | TABLE.set_sort(State.sort_column, State.sort_direction)
)

# A move or an insert puts the rows in an order of their own: no arrows.
unsorted = State.sort_column.set("")

# An edit may change the sorted column: keep the rows in the order the arrows claim.
resort = nu.IfDo(
    nu.Ne(State.sort_column, ""),
    State.rows.set(sorted_by(State.sort_column, State.sort_direction)),
)


on_edit = nu.ReactForever(
    TABLE.on_edit(),
    lambda ev: nu.IfDo(
        has(ev["key"]),
        nu.let(
            refusal(ev["column"], ev["value"]),
            lambda why: nu.IfDo(
                nu.Eq(why, ""),
                nustd.kv.Transaction(
                    State.rows.set(edited(ev["key"], ev["column"], ev["value"])) >> resort
                )
                >> ship
                >> STATUS.set("Set " + nu.Str(ev["column"]) + " of " + nu.Str(ev["key"])),
                STATUS.set("Not changed: " + nu.Str(why)),
            ),
        ),
        ship >> STATUS.set("Not changed: that row is gone"),
    ),
)

on_add = nu.ReactForever(
    TABLE.on_add(),
    lambda ev: (
        nustd.kv.Transaction(
            State.rows.set(inserted(ev["index"]))
            >> State.next_id.set(State.next_id + 1)
            >> unsorted
        )
        >> ship
        >> STATUS.set("Added a row")
    ),
)

on_delete = nu.ReactForever(
    TABLE.on_delete(),
    lambda ev: (
        nustd.kv.Transaction(State.rows.set(deleted(ev["keys"])))
        >> ship
        >> STATUS.set("Deleted " + nu.Str(", ").join(ev["keys"]))
    ),
)

on_move = nu.ReactForever(
    TABLE.on_move(),
    lambda ev: nu.IfDo(
        has(ev["key"]),
        nustd.kv.Transaction(moved(ev["key"], ev["index"]) >> unsorted)
        >> ship
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
        >> ship
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
