"""``DataTableRef`` -- rows and columns, and the row ops that change them in place.

A collection leaf: the rows are data on the node, never child nodes, so a
table has no children. Server owns the rows, the browser reports what you do
to them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.forms import Dict, List
from nustd.ui.core import Append, Changed, Ref, Send, Write
from nustd.ui.core.base import _wire_type_of

from ..collections.columns import normalize_columns
from ..collections.layout import one_of
from ..collections.table import DENSITIES, VARIANTS, TableDensity, TableVariant
from .base import LeafRef


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.args import DictArg, IntArg, ListArg, StrArg


__all__ = ["DataTableRef", "InsertRow", "RemoveRows", "SetOrder", "SetRow"]


SortDirection = Literal["asc", "desc"]
Selection = Literal["none", "single", "multi"]

# ---- table interactions -----------------------------------------------------
#
# A table's own changes, each its own op on the wire (``set_row``,
# ``insert_row``, ``remove_rows``, ``set_order``) and its own handler on the
# browser's DataTableRef node. The DataTableRef methods build them; they are exported
# for code that composes frames directly. Keys are the ones the browser draws:
# the ``row_key`` field, or the position as a string without one.


class SetRow(Send):
    """Replace the row keyed ``key`` with ``row``, or add it last when none is shown."""

    _payload_fields = ("key", "row")


class InsertRow(Send):
    """Insert ``row`` before the row at ``index``, clamped to the rows shown."""

    _payload_fields = ("index", "row")


class RemoveRows(Send):
    """Drop the rows with these ``keys``; keys not shown are skipped."""

    _payload_fields = ("keys",)


class SetOrder(Send):
    """Show the rows named by ``keys`` first, in that order; the rest keep theirs after."""

    _payload_fields = ("keys",)


# ---- column cell specs ------------------------------------------------------
#
# A column may say how its cells draw: ``{"key": "status", "cell":
# BadgeRef.slot(variant="info")}``. The browser draws that kind in every cell
# of the column from the cell's value; the value itself stays what sorts,
# edits and is read back. A scalar value lands on the kind's main prop (a
# Badge's ``label``, a RelativeTime's ``ts``); a mapping value merges over the
# spec's props, so a link cell can carry ``{"href": ..., "label": ...}``.

#: The kinds a column cell can draw as, by wire kind, and the prop a scalar
#: cell value lands on. Display kinds only: a cell draws, it never asks.
CELL_KINDS: dict[str, str] = {
    "BadgeRef": "label",
    "IconRef": "name",
    "KbdRef": "label",
    "LinkRef": "label",
    "PageLinkRef": "title",
    "ProgressRef": "value",
    "RelativeTimeRef": "ts",
    "StatusDotRef": "tone",
    "StatusPillRef": "label",
    "StatusSquaresRef": "counts",
    "TextRef": "value",
}


def _cell_spec(column: str, spec: object) -> dict[str, object]:
    """A column's ``cell`` as the wire carries it: ``{kind, props, prop}``."""
    if isinstance(spec, type) and issubclass(spec, Ref):
        spec = Slot(spec)
    if isinstance(spec, Slot):
        kind, props = _wire_type_of(spec.ref_cls), dict(spec.props)
    elif isinstance(spec, dict) and "kind" in spec:
        # Already lowered (a column read back from a store, a driver's copy).
        kind, props = str(spec["kind"]), dict(spec.get("props") or {})  # type: ignore[arg-type]
    else:
        msg = f"column {column!r} cell must be a ref class or a Kind.slot(...) spec, not {spec!r}"
        raise TypeError(msg)
    if kind not in CELL_KINDS:
        supported = ", ".join(sorted(CELL_KINDS))
        msg = f"column {column!r} cell cannot draw as {kind}; a cell draws as one of {supported}"
        raise TypeError(msg)
    return {"kind": kind, "props": props, "prop": CELL_KINDS[kind]}


_KINDS = ("text", "number", "bool", "select")


def _kind(column: object, value: object) -> object:
    if value not in _KINDS:
        msg = f"DataTableRef column {column!r} kind is one of {', '.join(_KINDS)}, not {value!r}"
        raise ValueError(msg)
    return value


def _flag(column: object, value: object) -> object:
    if not isinstance(value, bool):
        msg = f"DataTableRef column {column!r} flag is True or False, not {value!r}"
        raise TypeError(msg)
    return value


def _options(column: object, value: object) -> object:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        msg = f"DataTableRef column {column!r} options is a list, not {value!r}"
        raise TypeError(msg)
    return [str(o) for o in value]


#: The data keys a data table column adds to the column record.
DATA_KEYS = {
    "kind": _kind,
    "options": _options,
    "editable": _flag,
    "sortable": _flag,
    "cell": lambda column, spec: _cell_spec(str(column), spec),
}


def _columns(columns: object) -> object:
    """Column records as the wire carries them (see ``columns``); a term passes through."""
    if isinstance(columns, (list, tuple)):
        return normalize_columns("DataTableRef", list(columns), DATA_KEYS)
    return columns


def _looks(variant: object, density: object) -> dict[str, object]:
    """``variant`` and ``density`` as the wire carries them, each only when set."""
    out: dict[str, object] = {}
    if variant is not None:
        out["variant"] = one_of("DataTableRef", "variant", variant, VARIANTS)
    if density is not None:
        out["density"] = one_of("DataTableRef", "density", density, DENSITIES)
    return out


class DataTableRef(LeafRef):
    """Rows and columns. The server owns the rows; the browser reports what you do.

    Reads by default: a header click asks for a sort, and that is all. Each
    flag below turns on one more thing to ask for. Everything the user does
    arrives as one notify on the table, its kind named in the payload's
    ``event`` field, and each ``on_*`` takes only its own kind::

        class Shelf(nustd.ui.Column):
            table = nustd.ui.DataTableRef.slot(
                columns=["id", {"key": "title", "label": "Title"}],
                row_key="id",
                editable=True,
            )

        nu.ReactEvery(Shelf.table.on_edit(), lambda ev: save(ev["key"], ev["column"], ev["value"]))

    The browser never changes the rows itself. An edit, an add, a delete or a
    move is a request: the server applies it to whatever the table stands for
    and ships the rows again, all of them with :meth:`set_rows` or only what
    changed with :meth:`set_row`, :meth:`insert_row`, :meth:`remove_rows` and
    :meth:`set_order` (a sort it confirms with :meth:`set_sort`). A request
    the server turns down leaves the table as it was. Which rows are selected
    the browser keeps as you click, and the server can set it with
    :meth:`set_selected`.

    **Column requests** (``columns_editable``) work the same way: an insert,
    delete, rename, move, kind or align change arrives as an ``on_column_*``
    event, and the server confirms it by shipping the columns again with
    :meth:`set_columns`, and the rows too when it rewrote cells. List rows
    hold cells by position, so a server that inserts, deletes or moves
    columns must ship list rows again with their cells where the new columns
    are, in one frame with the columns: ``table.set({"columns": ..., "rows":
    ...})``, not ``set_columns(...) | set_rows(...)``, which arrives as two
    frames and shows cells under the wrong header in between. Mapping rows
    hold cells by column key and come through a reshape untouched (a column
    added shows empty until its cells are written). A table always keeps one
    column: delete is not offered on the last one::

        nu.ReactEvery(
            Shelf.table.on_column_rename(),
            lambda ev: Shelf.table.set_columns(renamed(ev["column"], ev["label"])),
        )

    **Columns** are column records (``nustd.ui.refs.collections.columns``),
    the same as a content table's: ``key``, ``label``, ``width``,
    ``min_width``, ``max_width``, ``wrap``, ``hide_below``, ``align``, plus
    the data keys ``kind`` (``"text"``, the default, ``"number"``, ``"bool"``
    or ``"select"``, which picks from ``options``), ``editable``,
    ``sortable`` and ``cell``. A string ``s`` is ``{"key": s}``. Every column
    sorts unless it says ``sortable: False``. A key the record does not have
    fails where it is written.

    **Cell specs.** A column mapping's ``cell`` draws every cell of that
    column as a ui kind, from the cell's value: ``{"key": "status", "cell":
    BadgeRef.slot(variant="info")}``. The value stays the data (it sorts,
    edits and reads back as sent), only its look changes; an edit opens the
    column's ``kind`` editor as before. A scalar value lands on the kind's
    main prop (``CELL_KINDS``: a Badge's ``label``, a RelativeTime's ``ts``, a
    StatusSquares' ``counts``); a mapping value merges over the spec's props,
    so a ``LinkRef`` cell takes ``{"href": ..., "label": ...}``. A blank cell
    (None or "") draws nothing. Supported kinds: TextRef, BadgeRef, LinkRef,
    PageLinkRef, StatusDotRef, StatusPillRef, StatusSquaresRef,
    RelativeTimeRef, ProgressRef, KbdRef, IconRef. Display kinds only; for
    anything else in a cell (a button, a row of controls, a nested table) use
    a content ``TableRef``.

    **Rows** are lists (cells by column position) or mappings (cells by column
    key), mixed freely. ``row_key`` names the field that keys a row: a column
    key for list rows, any field for mapping rows.

    **Row keys.** Without ``row_key`` a row's key is its position as a string,
    and the selection the browser keeps follows positions, not rows; so set
    ``row_key`` whenever rows can be inserted, deleted, moved or re-sorted. Its
    values must be unique: a duplicate gets "~2", "~3", ... in order so the
    grid still works, and that suffixed key is what events carry. A row whose
    key is missing or empty falls back to its index, which may collide with a
    real key, so give every row one. Every event that names rows by key also
    names them by position (``row_index``, ``row_indexes``), so a table
    without ``row_key`` is still fully usable. Keys of rows that are no longer
    shown drop out of the selection.

    **Positions** (``row_index``, ``row_indexes``, the add and move ``index``)
    count within the rows shown, which under ``max_rows`` are the newest ones.

    Args:
        columns: The columns, strings or mappings (see above).
        label: The table's accessible name, eg "Movies".
        variant: "striped" (the default, framed with alternate rows tinted),
            "default" (framed) or "borderless", the content table's looks.
        density: "compact", "default" or "comfortable" row heights.
        max_rows: Keep only the newest rows on ``set``, ``append``, ``set_row``
            and ``insert_row``; 0 keeps all.
        sort_column: The column the arrows show, by key.
        sort_direction: "asc" or "desc".
        clickable_rows: A row click arrives on :meth:`on_row_click`.
        row_key: The field that keys a row (see above).
        selection: "single" or "multi" rows select; the selection arrives on
            :meth:`on_select`.
        editable: Cells edit in place, every column but ``row_key`` and those
            that say ``editable: False``; an edit arrives on :meth:`on_edit`.
        addable: An "Add row" button and insert above / below in the row
            menu; a request arrives on :meth:`on_add`.
        deletable: Delete or the row menu; a request arrives on :meth:`on_delete`.
        draggable: Rows move by Alt + Up / Down, the row menu or a drag; a
            request arrives on :meth:`on_move`.
        columns_editable: Columns can be inserted, deleted, renamed, moved,
            and given another kind or alignment, from the column handle's
            menu, a header right-click or F2 on a header; each request
            arrives on its ``on_column_*``.
    """

    _wire_type = "DataTableRef"

    @classmethod
    def slot(
        cls,
        *,
        columns: Sequence[str | Mapping[str, object]] | None = None,
        label: str = "Table",
        variant: TableVariant | None = None,
        density: TableDensity | None = None,
        max_rows: int = 0,
        sort_column: str = "",
        sort_direction: SortDirection = "asc",
        clickable_rows: bool = False,
        row_key: str = "",
        selection: Selection = "none",
        editable: bool = False,
        addable: bool = False,
        deletable: bool = False,
        draggable: bool = False,
        columns_editable: bool = False,
    ) -> Self:
        return super().slot(
            columns=_columns(list(columns or ())),
            label=label,
            **_looks(variant, density),
            max_rows=max_rows,
            sort_column=sort_column,
            sort_direction=sort_direction,
            clickable_rows=clickable_rows,
            row_key=row_key,
            selection=selection,
            editable=editable,
            addable=addable,
            deletable=deletable,
            draggable=draggable,
            columns_editable=columns_editable,
        )

    # --- server -> browser ---------------------------------------------------

    def set(self, table: DictArg[str, Any]) -> Nu:
        """Merge any props, eg ``{"columns": [...], "rows": [...]}``."""
        if isinstance(table, dict) and "columns" in table:
            table = {**table, "columns": _columns(table["columns"])}
        return Write(self, table)

    def set_rows(self, rows: ListArg[Any]) -> Nu:
        """Replace every row. The selection stays where its keys still apply."""
        return Write(self, Dict.of(rows=rows))

    def clear(self) -> Nu:
        """Drop every row."""
        return Write(self, Dict.of(rows=[]))

    def append(self, row: ListArg[Any] | DictArg[str, Any]) -> Nu:
        """Add one row at the end, a list or a mapping; ``max_rows`` drops the oldest."""
        return Append(self, row)

    def set_columns(self, columns: ListArg[Any]) -> Nu:
        """Replace the columns, strings or mappings as on the slot; the rows stay.

        Mapping rows follow the columns by key. Over list rows a reshape
        (insert, delete, move) needs the rows in the same frame:
        ``set({"columns": columns, "rows": rows})``, since a second frame
        would show the old cells under the new headers until it lands.
        """
        return Write(self, Dict.of(columns=_columns(columns)))

    # The row-level ops below each ship one frame of their own (``SetRow``,
    # ``InsertRow``, ``RemoveRows``, ``SetOrder``) with only the row or the
    # order that changed. They name rows by key as the browser computes
    # it (the ``row_key`` field, or the position as a string without one), and
    # the first row with that key is the one they touch.

    def set_row(self, key: StrArg, row: ListArg[Any] | DictArg[str, Any]) -> Nu:
        """Replace the row keyed ``key`` in place, or add it at the end if none is shown.

        An upsert: a row that is new to the browser lands last (``max_rows``
        drops the oldest), and :meth:`set_order` can put it where it belongs.
        ``row`` is a whole row, a list or a mapping, not a partial one.
        """
        return SetRow(self, key, row)

    def insert_row(self, index: IntArg, row: ListArg[Any] | DictArg[str, Any]) -> Nu:
        """Insert ``row`` before the row at ``index``, or last past the end.

        ``index`` counts the rows shown and is clamped to them; ``max_rows``
        then drops the oldest.
        """
        return InsertRow(self, index, row)

    def remove_row(self, key: StrArg) -> Nu:
        """Drop the row keyed ``key``; a key not shown is a no-op."""
        return RemoveRows(self, List.of(key))

    def remove_rows(self, keys: ListArg[str]) -> Nu:
        """Drop the rows with these keys; keys not shown are skipped."""
        return RemoveRows(self, keys)

    def set_order(self, keys: ListArg[str]) -> Nu:
        """Reorder the rows shown to these keys, without shipping a row.

        Rows named come first in this order; the ones left out keep their
        order after them; keys not shown are skipped.
        """
        return SetOrder(self, keys)

    def set_sort(self, column: StrArg, direction: SortDirection | StrArg) -> Nu:
        """Show the arrows on ``column``; the rows are the server's to sort."""
        return Write(self, Dict.of(sort_column=column, sort_direction=direction))

    def set_selected(self, keys: ListArg[str]) -> Nu:
        """Select exactly these rows, by key; [] selects none."""
        return Write(self, Dict.of(selected=keys))

    # --- browser -> server ---------------------------------------------------

    def on_change(self) -> Changed:
        """Every event below, each naming itself in ``event``."""
        return Changed(self)

    def on_sort(self) -> Changed:
        """``{event, sort_column, sort_direction}``: a header clicked; confirm with ``set_sort``."""
        return Changed(self, "sort")

    def on_row_click(self) -> Changed:
        """``{event, row_index, key}``: a body row clicked. Needs ``clickable_rows``."""
        return Changed(self, "row")

    def on_select(self) -> Changed:
        """``{event, keys, row_indexes}``: the whole next selection. Needs ``selection``.

        ``row_indexes`` runs parallel to ``keys``: each row's position as shown.
        """
        return Changed(self, "select")

    def on_edit(self) -> Changed:
        """``{event, key, row_index, column, value, previous}``: a cell's new value. Needs ``editable``.

        ``value`` is typed by the column's kind: a str for "text" and
        "select", a number for "number", a bool for "bool".
        """
        return Changed(self, "edit")

    def on_add(self) -> Changed:
        """``{event, index}``: a new row asked for at ``index``. Needs ``addable``.

        The server decides what is in it, and its key.
        """
        return Changed(self, "add")

    def on_delete(self) -> Changed:
        """``{event, keys, row_indexes}``: these rows asked to go. Needs ``deletable``.

        ``row_indexes`` runs parallel to ``keys``: each row's position as shown.
        """
        return Changed(self, "delete")

    def on_move(self) -> Changed:
        """``{event, key, row_index, index}``: a row asked to move. Needs ``draggable``.

        ``row_index`` is where the row is now; ``index`` counts the rows
        without it, so the row lands before the row at that index, or last.
        """
        return Changed(self, "move")

    # Each column event names the column by its key as sent (``column``) and
    # by its position among the columns shown (``column_index``).

    def on_column_add(self) -> Changed:
        """``{event, index}``: a new column asked for at ``index``. Needs ``columns_editable``.

        The server decides what it is (key, label, kind) and confirms with
        :meth:`set_columns`; list rows go again with a cell at ``index``.
        """
        return Changed(self, "column_add")

    def on_column_delete(self) -> Changed:
        """``{event, column, column_index}``: a column asked to go. Needs ``columns_editable``.

        Confirm with :meth:`set_columns`; list rows go again without its
        cells, in the same frame (:meth:`set`). A table always keeps one
        column: the browser does not offer delete on the last one.
        """
        return Changed(self, "column_delete")

    def on_column_rename(self) -> Changed:
        """``{event, column, column_index, label, previous}``: new header text. Needs ``columns_editable``.

        ``label`` is as typed, untrimmed and possibly empty; ``previous`` is
        the label shown. The header keeps ``previous`` until the server
        confirms with :meth:`set_columns`.
        """
        return Changed(self, "column_rename")

    def on_column_move(self) -> Changed:
        """``{event, column, column_index, index}``: a column asked to move. Needs ``columns_editable``.

        ``index`` counts the columns without it, so the column lands before
        the column at that index, or last. Confirm with :meth:`set_columns`;
        list rows go again with their cells moved the same way.
        """
        return Changed(self, "column_move")

    def on_column_kind(self) -> Changed:
        """``{event, column, column_index, kind, previous}``: another kind asked for. Needs ``columns_editable``.

        ``kind`` and ``previous`` are "text", "number", "bool" or "select"
        (``previous`` "text" when the column sets none). Confirm with
        :meth:`set_columns`, and the rows when their cells were converted. A
        column switched to "select" needs its ``options`` sent with it.
        """
        return Changed(self, "column_kind")

    def on_column_align(self) -> Changed:
        """``{event, column, column_index, align, previous}``: another alignment. Needs ``columns_editable``.

        ``align`` and ``previous`` are "start", "center" or "end";
        ``previous`` is what the column shows, its kind's default (number
        end, bool center, else start) when it sets none.
        """
        return Changed(self, "column_align")
