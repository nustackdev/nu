"""What a stored table is worth on the wire, and how a request reshapes it.

Plain Python over plain values, no fabric and no Ref: every function here takes
what a read produced (a column list, the cells of a row, the stored order) and
returns what to write or what to ship. The preset reads, calls one of these
through its atom, and writes or ships the answer, so the rules a table follows
(how a typed value is stored, where a blank sorts, what a fresh column is
called) live in one place a test can reach without a store.

Reads hand in kv views and sentinels as well as plain values: a list read back
from a ListRef holds views, and a slot never written reads as EMPTY. Each atom
lowers those first, so nothing that leaves here is tied to a store.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import nu
from nu.lang.sentinels import is_sentinel


__all__ = [
    "KINDS",
    "blank",
    "coerce",
    "column_added",
    "column_moved",
    "column_removed",
    "column_set",
    "columns_of",
    "has_column",
    "inserted",
    "kind_of",
    "marked",
    "moved",
    "ordered",
    "plain",
    "settled",
    "sort_of",
    "sorted_keys",
    "table_props",
    "wire_row",
    "without",
]


#: The kinds a column may say, as the node reads them; anything else is "text".
KINDS = ("text", "number", "bool", "select")

#: Strings a bool cell reads as true, compared stripped and lowercased.
TRUE_WORDS = frozenset({"true", "yes", "1", "x"})


def plain(value: object) -> object:
    """``value`` with every view lowered to a dict or a list, and a sentinel to None."""
    if is_sentinel(value):
        return None
    if isinstance(value, Mapping):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [plain(v) for v in value]
    return value


# ---- cells ------------------------------------------------------------------


def _number(value: object) -> int | float | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if "_" in text:  # Python reads "1_000"; a person typing it did not mean a number.
            return None
        try:
            return int(text)
        except ValueError:
            pass
        try:
            value = float(text)
        except ValueError:
            return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return int(value) if value.is_integer() else value
    return None


def coerce(value: object, kind: object) -> object:
    """``value`` as a cell of ``kind`` stores it.

    A number is an int when it is integral and a float otherwise; text that
    does not parse, or a value that is not a number, is None. A bool is the
    bool itself, a finite number other than 0, or a string among ``TRUE_WORDS``. Text
    and select are strings, None being "" and a bool "true" or "false", the
    words a bool cell reads back.
    """
    value = plain(value)
    if kind == "number":
        return _number(value)
    if kind == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return math.isfinite(value) and value != 0
        if isinstance(value, str):
            return value.strip().lower() in TRUE_WORDS
        return False
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value if isinstance(value, str) else str(value)


def blank(kind: object) -> object:
    """The empty cell of ``kind``: None for a number, False for a bool, else ""."""
    return None if kind == "number" else False if kind == "bool" else ""


def wire_row(key: object, cells: object, field: str) -> dict[str, Any]:
    """A row as the table ships it: its cells, and its key under ``field``."""
    row = plain(cells)
    row = dict(row) if isinstance(row, dict) else {}
    row[field] = key
    return row


# ---- columns ----------------------------------------------------------------


def columns_of(raw: object, fallback: object = ()) -> list[dict[str, Any]]:
    """Columns as mappings: a string ``s`` is ``{"key": s}``. EMPTY reads ``fallback``."""
    value = plain(raw)
    if value is None:
        value = plain(fallback) or []
    return [
        {"key": c} if isinstance(c, str) else dict(c) for c in value if isinstance(c, (str, dict))
    ]


def _find(columns: object, key: object) -> int:
    for i, c in enumerate(columns_of(columns)):
        if c.get("key") == key:
            return i
    return -1


def has_column(columns: object, key: object) -> bool:
    """Whether a column keyed ``key`` is among ``columns``."""
    return _find(columns, key) >= 0


def kind_of(columns: object, key: object) -> str:
    """The kind of the column keyed ``key``; "text" for an unknown column or kind."""
    cols = columns_of(columns)
    i = _find(cols, key)
    kind = cols[i].get("kind", "text") if i >= 0 else "text"
    return kind if kind in KINDS else "text"


def column_added(columns: object, index: object, key: object) -> list[dict[str, Any]]:
    """``columns`` with a text column keyed ``key`` before ``index``, "Column N" by name.

    N is the column's number counted from 1, raised past any label already
    taken so two fresh columns never read the same.
    """
    cols = columns_of(columns)
    taken = {str(c.get("label", c.get("key"))) for c in cols}
    n = len(cols) + 1
    while f"Column {n}" in taken:
        n += 1
    at = max(0, min(len(cols), int(_number(index) or 0)))
    cols.insert(at, {"key": key, "label": f"Column {n}", "kind": "text"})
    return cols


def column_removed(columns: object, key: object) -> list[dict[str, Any]]:
    """``columns`` without the one keyed ``key``."""
    return [c for c in columns_of(columns) if c.get("key") != key]


def column_set(columns: object, key: object, field: str, value: object) -> list[dict[str, Any]]:
    """``columns`` with ``field`` of the column keyed ``key`` set to ``value``."""
    return [{**c, field: plain(value)} if c.get("key") == key else c for c in columns_of(columns)]


def column_moved(columns: object, key: object, index: object) -> list[dict[str, Any]]:
    """``columns`` with the one keyed ``key`` before the column at ``index`` among the others."""
    cols = columns_of(columns)
    i = _find(cols, key)
    if i < 0:
        return cols
    col = cols.pop(i)
    cols.insert(max(0, min(len(cols), int(_number(index) or 0))), col)
    return cols


# ---- order ------------------------------------------------------------------


def ordered(order: object, keys: object) -> list[str]:
    """The rows as shown: the stored order, then any stored row it misses.

    A key in the order with no row is skipped, a repeat is dropped, and a row
    the order never named lands last, so a store written by hand still shows
    every row once.
    """
    present = [str(k) for k in plain(keys) or []]
    have = set(present)
    out: list[str] = []
    seen: set[str] = set()
    for k in plain(order) or []:
        k = str(k)
        if k in have and k not in seen:
            out.append(k)
            seen.add(k)
    out.extend(k for k in present if k not in seen)
    return out


def inserted(keys: object, index: object, key: object) -> list[str]:
    """``keys`` with ``key`` before the key at ``index``, or last past the end."""
    out = [str(k) for k in plain(keys) or [] if k != key]
    out.insert(max(0, min(len(out), int(_number(index) or 0))), str(key))
    return out


def without(keys: object, gone: object) -> list[str]:
    """``keys`` without any of ``gone``."""
    drop = {str(k) for k in plain(gone) or []}
    return [str(k) for k in plain(keys) or [] if str(k) not in drop]


def moved(keys: object, key: object, index: object) -> list[str]:
    """``keys`` with ``key`` before the key at ``index`` among the others; unknown is a no-op."""
    out = [str(k) for k in plain(keys) or []]
    if key not in out:
        return out
    return inserted(out, index, key)


def _rank(value: object) -> tuple[int, Any]:
    if isinstance(value, (bool, int, float)):
        return (0, value)
    return (1, str(value).casefold())


def sorted_keys(
    keys: object, cells: object, column: object, direction: object, field: str
) -> list[str]:
    """``keys`` ordered by each row's cell under ``column``.

    Ascending, numbers and bools come before text, which compares without
    case; descending reverses all of it, text first. A blank cell (missing,
    None or "") sorts last either way, the way a spreadsheet
    keeps empty rows at the bottom. Ties keep their order. ``column`` equal to
    ``field`` sorts by the key itself.
    """
    rows = plain(cells) or {}
    full: list[tuple[str, Any]] = []
    blanks: list[str] = []
    for k in [str(k) for k in plain(keys) or []]:
        value = k if column == field else (rows.get(k) or {}).get(str(column))
        if value is None or value == "":
            blanks.append(k)
        else:
            full.append((k, _rank(value)))
    full.sort(key=lambda kv: kv[1], reverse=direction == "desc")
    return [k for k, _ in full] + blanks


# ---- the whole table --------------------------------------------------------


def sort_of(raw: object) -> dict[str, str]:
    """The stored arrows as ``{column, direction}``; nothing stored reads no column."""
    value = plain(raw)
    if not isinstance(value, dict):
        return {"column": "", "direction": "asc"}
    direction = "desc" if value.get("direction") == "desc" else "asc"
    return {"column": str(value.get("column") or ""), "direction": direction}


def table_props(
    columns: object, order: object, cells: object, field: str, sort: object, ship_columns: bool
) -> dict[str, Any]:
    """Every prop a whole repaint writes: rows in order, the key field, the arrows.

    The columns too when ``ship_columns``; without it a table whose columns
    are fixed on its slot keeps them.
    """
    rows = plain(cells) or {}
    arrows = sort_of(sort)
    props: dict[str, Any] = {
        "rows": [wire_row(k, rows[k], field) for k in ordered(order, list(rows))],
        "row_key": field,
        "sort_column": arrows["column"],
        "sort_direction": arrows["direction"],
    }
    if ship_columns:
        props["columns"] = columns_of(columns)
    return props


# ---- live repaint -----------------------------------------------------------
#
# What a connection owes its browser since it last painted: rows by key, the
# order, the arrows, or everything. Writes from any connection mark it, and a
# debounced flush ships it and then settles it. ``n`` counts the marks, so a
# flush clears only what it shipped: a mark landing while it ships keeps the
# state owed, and so does a flush cut short (a debounce cancels a run that is
# still shipping).

CLEAN: dict[str, Any] = {"all": False, "keys": [], "order": False, "sort": False, "n": 0}


def marked(state: object, what: str, address: object, depth: int) -> dict[str, Any]:
    """``state`` with one change noted.

    ``what`` is the slot that changed. A ``rows`` change whose address reaches
    ``depth`` names its row there, and only that row is owed; one that stops
    above it (the whole mapping written) owes everything, like a ``columns``
    change does.
    """
    out = dict(plain(state) or CLEAN)
    out["n"] = int(out.get("n") or 0) + 1
    addr = plain(address)
    addr = addr if isinstance(addr, list) else []
    if what == "rows" and len(addr) > depth:
        key = str(addr[depth])
        if key not in out["keys"]:
            out["keys"] = [*out["keys"], key]
    elif what in ("order", "sort"):
        out[what] = True
    else:
        out["all"] = True
    return out


def settled(state: object, shipped: object) -> dict[str, Any]:
    """``state`` once ``shipped`` went out: clean, unless a mark landed since.

    Then nothing is cleared, and the next flush ships it all again, which
    repeats a row at worst and never drops one.
    """
    now = dict(plain(state) or CLEAN)
    sent = plain(shipped) or CLEAN
    if now.get("n") != sent.get("n"):
        return now
    return {**CLEAN, "n": now.get("n") or 0}


# ---- atoms ------------------------------------------------------------------
#
# Each function above as a Nu atom, for the preset to call on values it read.
# Sentinels are handed in rather than short-circuiting, because a slot never
# written is an answer here (no rows yet, no arrows), not a reason to stop.


def _atom(fn: Callable[..., object], name: str) -> type[nu.Nu]:
    return nu.host(fn, name=name, propagate_sentinels=False)


Coerce = _atom(coerce, "TableCoerce")
Blanks = _atom(
    lambda columns: {c["key"]: blank(c.get("kind")) for c in columns_of(columns)}, "TableBlanks"
)
WireRow = _atom(wire_row, "TableWireRow")
ColumnsOf = _atom(columns_of, "TableColumnsOf")
HasColumn = _atom(has_column, "TableHasColumn")
KindOf = _atom(kind_of, "TableKindOf")
ColumnAdded = _atom(column_added, "TableColumnAdded")
ColumnRemoved = _atom(column_removed, "TableColumnRemoved")
ColumnSet = _atom(column_set, "TableColumnSet")
ColumnMoved = _atom(column_moved, "TableColumnMoved")
Ordered = _atom(ordered, "TableOrdered")
Inserted = _atom(inserted, "TableInserted")
Without = _atom(without, "TableWithout")
Moved = _atom(moved, "TableMoved")
SortedKeys = _atom(sorted_keys, "TableSortedKeys")
SortOf = _atom(sort_of, "TableSortOf")
TableProps = _atom(table_props, "TableProps")
Marked = _atom(marked, "TableMarked")
Settled = _atom(settled, "TableSettled")
ShortKey = _atom(lambda hex_: str(hex_)[:8], "TableShortKey")
