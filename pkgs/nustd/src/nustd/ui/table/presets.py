"""A table that is its store: requests written verbatim, every tab kept live.

``TableRef`` is deliberately fabric-free. It sends frames and hands requests
over, and it neither knows nor cares what the rows stand for, so an app can
answer an edit with a refusal, a lookup or a write to anywhere. :mod:`.values`
is fabric-free too: plain rules over plain values.

The common answer, though, is "store it": the grid is the data, and an edit is
a write. Doing that well takes a store. Reads and writes have to sit inside a
storage boundary, a request's writes belong in one transaction, and a write
from one tab has to reach every other. Somebody has to place the
``Transaction`` and the ``Snapshot``, and leaving it to each app makes it a
contract they have to know and can silently get wrong. Doing it here costs this
one module an import of :mod:`nustd.kv`.

So the layering is: the Ref knows nothing about fabrics, the preset knows about
kv. Reach for :func:`sync` when the table should simply be what is stored.
Reach past it, for the Ref's ``on_*`` and its row-level ops, when a request is
a question your app answers (validation, refusals, a status line), the way
``examples/table.py`` does.

**Layout.** One app Shape holds a table as up to four slots::

    class Sheet(nu.Shape):
        rows = nustd.kv.DictRef.slot(nustd.ui.table.Row)  # row key -> Row
        order = nustd.kv.ListRef.slot(str)                 # row keys, as shown
        columns = nustd.kv.ListRef.slot(object)            # column mappings, optional
        sort = nustd.kv.ObjectRef.slot()                   # {column, direction}, optional

A row is a :class:`Row`, whose ``cells`` map column key to value, so a cell is
``rows[key].cells[column]`` with an address of its own: an edit writes one
cell, and a watcher learns which row moved. A move or a sort rewrites
``order`` and no row at all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
import nustd.kv
from nu.domains.shape import root_shape
from nustd.uuid import uuid4

from .values import (
    CLEAN,
    Blanks,
    Coerce,
    ColumnAdded,
    ColumnMoved,
    ColumnRemoved,
    ColumnSet,
    ColumnsOf,
    HasColumn,
    Inserted,
    KindOf,
    Marked,
    Moved,
    Ordered,
    Settled,
    ShortKey,
    SortedKeys,
    SortOf,
    TableProps,
    WireRow,
    Without,
    columns_of,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape import StructuredRef
    from nustd.ui.refs import TableRef


__all__ = ["REPAINT_DELAY", "Row", "sync"]


#: How long a burst of writes is waited out before a tab repaints once.
REPAINT_DELAY = 0.25

#: The field a row's key ships under when the TableRef slot names no ``row_key``.
KEY_FIELD = "_key"


class Row(nu.Shape):
    """One stored row: its cells by column key, each at an address of its own.

    A Shape around a ``DictRef`` rather than the ``DictRef`` itself, because a
    mapping slot declared to hold mappings stores each one as a single value,
    and a row stored whole could be neither written one cell at a time nor
    watched by row.
    """

    cells = nustd.kv.DictRef.slot(object)


def _depth(ref: StructuredRef) -> int:
    """Where a change under ``ref`` names its child: the length of ``ref``'s own address.

    An address starts at the store's root, ``"/"``, and has one segment per
    slot on the chain down to ``ref``: ``("/", "rows", key, ...)`` names its
    row at 2.
    """
    n = 1
    node: StructuredRef | None = ref
    while node is not None:
        n += 1
        node = node._parent
    return n


def _new_key() -> nu.Nu:
    """A fresh key, eight random hex digits: unique enough for one table's rows or columns."""
    return ShortKey(uuid4().hex())


def sync(
    table: TableRef,
    rows: StructuredRef,
    order: StructuredRef,
    columns: StructuredRef | None = None,
    *,
    sort: StructuredRef | None = None,
    debounce: float = REPAINT_DELAY,
) -> nu.Nu:
    """The table as the store holds it, as one tree: paint, apply requests, stay live.

    Policy free: what the browser asks for is what gets stored. An edit writes
    the value coerced to its column's kind (see :func:`.values.coerce`). An
    add stores an empty row under a fresh key, where it was asked for. A
    delete deletes. A move rewrites ``order`` and nothing else. A sort
    rewrites ``order`` by that column and stores the arrows; a later move or
    add clears them, because the rows are no longer in the order they claim.
    An edit of the sorted column re-sorts, for the same reason. The last
    column is never deleted: a table keeps one. Turn on what the
    browser may ask for on the slot (``editable``, ``addable``, ``deletable``,
    ``draggable``, ``columns_editable``); this applies whatever arrives.

    Each request's writes land in one transaction, retried on a conflict, and
    the answer ships after it commits, read from what was stored: one row
    (``set_row``, ``insert_row``), the keys that went (``remove_rows``) or the
    order (``set_order``). A request naming a row or a column that is gone
    changes nothing and ships the whole table, so a browser that was behind
    catches up.

    Live: a write from any tab, or anything else writing the store, repaints
    every tab. A row that changed ships alone (``set_row``, or
    ``remove_rows`` once it is gone), the order on its own, the arrows on
    their own, and a change to the columns or to the whole mapping repaints
    the table. A burst is waited out for ``debounce`` seconds and shipped
    once. The tab that asked gets its answer at once and the same rows again
    when the burst settles, which changes nothing it shows.

    Never finishes, which is what the ws host holds a tab's program to. Put
    several in a :class:`nu.ParallelAsync`.

    Args:
        table: the ``TableRef`` on the mounted page. Its ``row_key`` names the
            field a row's key ships under, ``"_key"`` (not shown) when it names
            none.
        rows: a ``DictRef`` of :class:`Row`, keyed by row key.
        order: a ``ListRef`` of row keys. Rows it does not name show last.
        columns: a ``ListRef`` of column mappings, which turns column requests
            on: add, delete, rename, move, kind and align are stored, and a
            kind change re-coerces the column's cells. Seeded from the slot's
            columns while it holds none (the store cannot tell a list never
            written from an emptied one, which is also why the last column
            is never deleted). None keeps the slot's columns, fixed, and
            column requests change nothing.
        sort: an ``ObjectRef`` to store the arrows in, so every tab shows
            them. None keeps them per tab: the order a sort writes is still
            shared, but only the tab that sorted shows why, and edits from
            other tabs do not re-sort. Pass one whenever more than one tab
            edits.
        debounce: how long a burst of writes is waited out before a tab repaints.

    Example:
        class Sheet(nu.Shape):
            rows = nustd.kv.DictRef.slot(nustd.ui.table.Row)
            order = nustd.kv.ListRef.slot(str)
            columns = nustd.kv.ListRef.slot(object)
            sort = nustd.kv.ObjectRef.slot()

        ui = nustd.ui.table.sync(App.home.table, Sheet.rows, Sheet.order, Sheet.columns, sort=Sheet.sort)
    """
    props = nu.tree.payload(table).get("props", {})
    slot_columns = columns_of(props.get("columns") or [])
    field = str(props.get("row_key") or KEY_FIELD)
    scope = root_shape(rows)
    live_columns = columns is not None

    def snapshot(*body: nu.Nu) -> nu.Nu:
        return nustd.kv.Snapshot(*body, scope=scope)

    def transaction(*body: nu.Nu) -> nu.Nu:
        return nustd.kv.RetryOnConflict(nustd.kv.Transaction(*body, scope=scope))

    # ---- reads, each a term to place inside a boundary ----------------------

    def cols() -> nu.Nu:
        if columns is None:
            return nu.Literal(slot_columns)
        return ColumnsOf(nu.ToList(columns), nu.Literal(slot_columns))

    def keys() -> nu.Nu:
        return nu.Collect(rows.iter())

    def shown() -> nu.Nu:
        return Ordered(nu.ToList(order), keys())

    def cells() -> nu.Nu:
        return nu.ToDict(
            nu.Collect(nu.Map(rows.iter(), lambda k: nu.Tuple.of(k, nu.ToDict(rows[k].cells))))
        )

    def row(key: nu.Nu) -> nu.Nu:
        return WireRow(key, nu.ToDict(rows[key].cells), field)

    def program(arrows: nu.Nu) -> nu.Nu:
        # Everything below reads the arrows through one ref, stored or per tab.
        sorted_on = nu.Ne(nu.Dict(SortOf(arrows))["column"], "")

        def whole() -> nu.Nu:
            return table.set(
                TableProps(cols(), nu.ToList(order), cells(), field, arrows, live_columns)
            )

        def ship_sort() -> nu.Nu:
            state = nu.Dict(SortOf(arrows))
            return table.set_sort(state["column"], state["direction"])

        def put_arrows(column: nu.Nu, direction: nu.Nu) -> nu.Nu:
            value = nu.Dict.of(column=column, direction=direction)
            if sort is None:
                return arrows.set(value)
            # A store keeps a mapping as a key per field, and writing one over
            # another only touches the fields, which the slot's own watchers
            # never hear. Erased first, the write is the slot's again.
            return arrows.erase() >> arrows.set(value)

        def unsort() -> nu.Nu:
            return nu.IfDo(sorted_on, put_arrows("", "asc"))

        def sorted_by(column: nu.Nu) -> nu.Nu:
            return nu.Eq(nu.Dict(SortOf(arrows))["column"], column)

        def resort() -> nu.Nu:
            state = nu.Dict(SortOf(arrows))
            return order.set(
                SortedKeys(shown(), cells(), state["column"], state["direction"], field)
            )

        def answer(ok: nu.Nu, write: nu.Nu, reply: nu.Nu) -> nu.Nu:
            # Checked once to write and once more to answer, after the commit:
            # a row gone by then is answered with the whole table.
            return transaction(nu.IfDo(ok, write)) >> snapshot(nu.IfDo(ok, reply, whole()))

        # ---- row requests ---------------------------------------------------

        def edit(ev: nu.Nu) -> nu.Nu:
            key, column = ev["key"], ev["column"]
            ok = nu.And(rows.contains(key), HasColumn(cols(), column))
            value = Coerce(ev["value"], KindOf(cols(), column))
            # Only an edit of the sorted column can put a row out of order.
            return answer(
                ok,
                rows[key].cells[column].set(value) >> nu.IfDo(sorted_by(column), resort()),
                table.set_row(key, row(key))
                >> nu.IfDo(sorted_by(column), table.set_order(shown())),
            )

        def add(ev: nu.Nu) -> nu.Nu:
            index = ev["index"]
            return nu.let(
                _new_key(),
                lambda key: (
                    transaction(
                        # Eight hex digits can repeat; a key taken is drawn again.
                        nu.WhileDo(rows.contains(key), key.set(_new_key()))
                        >> rows[key].cells.set(Blanks(cols()))
                        >> order.set(Inserted(shown(), index, key))
                        >> unsort()
                    )
                    >> snapshot(table.insert_row(index, row(key)) >> ship_sort())
                ),
            )

        def delete(ev: nu.Nu) -> nu.Nu:
            gone = ev["keys"]
            return transaction(
                nu.ForEachDo(gone, lambda k: nu.IfDo(rows.contains(k), rows.del_item(k)))
                >> order.set(Without(shown(), gone))
            ) >> table.remove_rows(gone)

        def move(ev: nu.Nu) -> nu.Nu:
            key = ev["key"]
            return answer(
                rows.contains(key),
                order.set(Moved(shown(), key, ev["index"])) >> unsort(),
                table.set_order(shown()) >> ship_sort(),
            )

        def sort_rows(ev: nu.Nu) -> nu.Nu:
            column, direction = ev["sort_column"], ev["sort_direction"]
            return answer(
                nu.Or(HasColumn(cols(), column), nu.Eq(column, field)),
                order.set(SortedKeys(shown(), cells(), column, direction, field))
                >> put_arrows(column, direction),
                table.set_order(shown()) >> ship_sort(),
            )

        reactions = [
            nu.ReactForever(table.on_edit(), edit),
            nu.ReactForever(table.on_add(), add),
            nu.ReactForever(table.on_delete(), delete),
            nu.ReactForever(table.on_move(), move),
            nu.ReactForever(table.on_sort(), sort_rows),
        ]

        # ---- column requests, when the columns are stored -------------------

        if columns is not None:

            def has(column: nu.Nu) -> nu.Nu:
                return HasColumn(cols(), column)

            def recolumn(ok: nu.Nu, new: nu.Nu, cells_too: nu.Nu | None = None) -> nu.Nu:
                write = columns.set(new) if cells_too is None else columns.set(new) >> cells_too
                reply = whole() if cells_too is not None else table.set_columns(cols())
                return answer(ok, write, reply)

            def every_cell(column: nu.Nu, body: Callable[[nu.Nu, nu.Nu], nu.Nu]) -> nu.Nu:
                return nu.ForEachDo(
                    keys(),
                    lambda k: nu.IfDo(rows[k].cells.contains(column), body(rows[k].cells, column)),
                )

            def column_add(ev: nu.Nu) -> nu.Nu:
                return nu.let(
                    _new_key(),
                    lambda key: answer(
                        nu.Literal(True),
                        nu.WhileDo(has(key), key.set(_new_key()))
                        >> columns.set(ColumnAdded(cols(), ev["index"], key)),
                        table.set_columns(cols()),
                    ),
                )

            def column_delete(ev: nu.Nu) -> nu.Nu:
                c = ev["column"]
                # A table keeps one column: the last one stays, and the browser
                # is re-sent the table. Emptied, the list would read as never
                # written, and the next tab would seed it from the slot again.
                return recolumn(
                    nu.And(has(c), nu.Gt(nu.Len(cols()), 1)),
                    ColumnRemoved(cols(), c),
                    every_cell(c, lambda cs, col: cs.del_item(col)),
                )

            def column_set(field_name: str, value_key: str) -> Callable[[nu.Nu], nu.Nu]:
                def react(ev: nu.Nu) -> nu.Nu:
                    c = ev["column"]
                    return recolumn(has(c), ColumnSet(cols(), c, field_name, ev[value_key]))

                return react

            def column_move(ev: nu.Nu) -> nu.Nu:
                c = ev["column"]
                return recolumn(has(c), ColumnMoved(cols(), c, ev["index"]))

            def column_kind(ev: nu.Nu) -> nu.Nu:
                c, kind = ev["column"], ev["kind"]
                return recolumn(
                    has(c),
                    ColumnSet(cols(), c, "kind", kind),
                    every_cell(c, lambda cs, col: cs[col].set(Coerce(cs[col], kind))),
                )

            reactions += [
                nu.ReactForever(table.on_column_add(), column_add),
                nu.ReactForever(table.on_column_delete(), column_delete),
                nu.ReactForever(table.on_column_rename(), column_set("label", "label")),
                nu.ReactForever(table.on_column_move(), column_move),
                nu.ReactForever(table.on_column_kind(), column_kind),
                nu.ReactForever(table.on_column_align(), column_set("align", "align")),
            ]

        # ---- live: what other writers changed -------------------------------

        def live(dirty: nu.Nu, pending: nu.Nu) -> nu.Nu:
            def flush() -> nu.Nu:
                def ship(held: nu.Nu) -> nu.Nu:
                    owed = nu.Dict(held)
                    stale = owed["keys"]
                    here = nu.Collect(nu.Filter(nu.Iter(stale), lambda k: rows.contains(k)))
                    gone = nu.Collect(nu.Filter(nu.Iter(stale), lambda k: nu.Not(rows.contains(k))))
                    return snapshot(
                        nu.IfDo(
                            owed["all"],
                            whole(),
                            nu.ForEachDo(here, lambda k: table.set_row(k, row(k)))
                            >> nu.IfDo(nu.Gt(nu.Len(gone), 0), table.remove_rows(gone))
                            >> nu.IfDo(owed["order"], table.set_order(shown()))
                            >> nu.IfDo(owed["sort"], ship_sort()),
                        )
                    )

                # Settled after shipping, not cleared before: a flush cut short
                # leaves its rows owed for the next one.
                return nu.let(dirty, lambda owed: ship(owed) >> dirty.set(Settled(dirty, owed)))

            def watch(change: nu.Nu, what: str, depth: int = 0) -> nu.Nu:
                return nu.ReactForever(
                    snapshot(change),
                    lambda address: (
                        dirty.set(Marked(dirty, what, address, depth))
                        >> nu.Debounce(debounce, flush(), pending=pending)
                    ),
                )

            watched = [
                watch(rows.on_change(), "rows", _depth(rows)),
                watch(order.on_change(), "order"),
            ]
            if columns is not None:
                watched.append(watch(columns.on_change(), "columns"))
            if sort is not None:
                watched.append(watch(sort.on_change(), "sort"))
            # The watchers may bind after the first paint has read, so a write
            # landing in between would be missed. So the paint owes everything
            # once more, and one debounced flush after it repaints whatever
            # the watchers were too late for: one extra repaint per connect.
            first = (
                snapshot(whole())
                >> dirty.set(Marked(dirty, "all", nu.List.of(), 0))
                >> nu.Debounce(debounce, flush(), pending=pending)
            )
            return nu.ParallelAsync(*reactions, *watched, first)

        seed = (
            nu.Noop()
            if columns is None
            else transaction(
                nu.IfDo(nu.Eq(nu.Len(nu.ToList(columns)), 0), columns.set(nu.Literal(slot_columns)))
            )
        )
        return seed >> nu.let(
            nu.Literal(CLEAN), lambda dirty: nu.let(None, lambda pending: live(dirty, pending))
        )

    if sort is not None:
        return program(sort)
    return nu.let(None, program)
