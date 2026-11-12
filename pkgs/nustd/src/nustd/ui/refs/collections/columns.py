"""The column record: one way to describe a table column, for both tables.

A column is a mapping (or a string ``s``, read as ``{"key": s}``):

- ``key``: the column's name. A data table reads a row's cell by it; a
  content table only labels by it.
- ``label``: the header text, the key unless given.
- ``width``, ``min_width``, ``max_width``: a ``Length`` (an int is px).
  ``width`` is where the column starts; the table still shares out room.
- ``wrap``: ``"wrap"`` (the default) breaks long text onto more lines,
  ``"nowrap"`` keeps one line, ``"truncate"`` keeps one line and clips it
  with an ellipsis, the whole text on hover.
- ``hide_below``: px of table width under which the column is not drawn,
  so a narrow pane drops what it has no room for.
- ``align``: ``"start"``, ``"center"`` or ``"end"``.

A ``DataTableRef`` column adds its data keys to the same record: ``kind``,
``options``, ``editable``, ``sortable`` and ``cell`` (see ``DataTableRef``).
Every value is checked where it is written, and a key the record does not
have fails loud.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from nu.lang import Nu

from .layout import normalize_length, one_of


__all__ = ["COLUMN_KEYS", "normalize_column", "normalize_columns"]


#: The keys every column record takes.
COLUMN_KEYS = frozenset(
    {"key", "label", "width", "min_width", "max_width", "wrap", "hide_below", "align"}
)

_WRAPS = ("wrap", "nowrap", "truncate")
_ALIGNS = ("start", "center", "end")


def normalize_column(
    owner: str, column: object, extra: Mapping[str, object] | None = None
) -> dict[str, object]:
    """One column as the wire carries it, every value checked.

    ``extra`` names the keys a table adds to the record, each with a
    function that checks its value (``None`` passes the value as it is).
    """
    if isinstance(column, str):
        return {"key": column}
    if not isinstance(column, Mapping):
        msg = f"{owner} column is a key (str) or a mapping, not {column!r}"
        raise TypeError(msg)
    extra = extra or {}
    takes = COLUMN_KEYS | frozenset(extra)
    unknown = sorted(set(column) - takes)
    name = column.get("key", column.get("label", "?"))
    if unknown:
        msg = (
            f"{owner} column {name!r} takes no {', '.join(map(str, unknown))};"
            f" a column takes {', '.join(sorted(takes))}"
        )
        raise ValueError(msg)
    out: dict[str, object] = {}
    for k, v in column.items():
        if v is None:
            continue
        what = f"column {name!r} {k}"
        if k in ("key", "label"):
            out[k] = str(v)
        elif k in ("width", "min_width", "max_width"):
            out[k] = normalize_length(owner, what, v)
        elif k == "wrap":
            out[k] = one_of(owner, what, v, _WRAPS)
        elif k == "align":
            out[k] = one_of(owner, what, v, _ALIGNS)
        elif k == "hide_below":
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                msg = f"{owner} {what} is a table width in px (int >= 0), not {v!r}"
                raise ValueError(msg)
            out[k] = v
        else:
            check = extra[k]
            out[k] = v if check is None else check(name, v)  # type: ignore[operator]
    return out


def normalize_columns(
    owner: str, columns: object, extra: Mapping[str, object] | None = None
) -> object:
    """A list of columns as the wire carries it; a term passes as it is."""
    if isinstance(columns, Nu):
        return columns
    if isinstance(columns, (str, bytes)) or not isinstance(columns, Sequence):
        msg = f"{owner} columns is a list of columns, not {columns!r}"
        raise TypeError(msg)
    return [normalize_column(owner, c, extra) for c in columns]
