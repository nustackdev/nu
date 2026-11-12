"""Places: a cell at ``(row, column)`` and the cells that span, as the wire carries them.

The content table (``t[r, c]``) and the placed grid (``grid[r, c]``) both
address a cell by two positions and both span cells with one map keyed
``"r,c"``. The building of that key lives here, once, so the two never
drift: the same refusals, the same wire text, the same ``SetSpan`` payload.

What differs stays with each container: a table reaches the cell through a
row (``t[r]`` is a row on the wire, then ``c`` under it), a grid sits the
cell at one segment ``"r,c"`` directly under itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Nu

from .descent import check_key
from .interactions import Send


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


__all__ = ["SetSpan", "Span", "normalize_spans", "place", "place_of", "span_key"]


class SetSpan(Send):
    """Make the cell at ``key`` ``cols`` tracks wide and ``rows`` tall; 1 and 1 is plain.

    One entry of a ``spans`` map, the same op for a grid and a content table.
    """

    _payload_fields = ("key", "cols", "rows")


#: A cell's span as written: columns alone, or (columns, rows).
Span = int | tuple[int, int]


def place(owner: str, row: object, col: object, *, header: str | None = None) -> object:
    """The key ``"r,c"`` for row ``row``, column ``col``: a term when either side is one.

    Both sides are positions (``check_key(names=False)``). ``header`` is a row
    name taken as is, the content table's header row.
    """
    if header is None or not (isinstance(row, str) and row == header):
        check_key(owner, row, names=False)
    check_key(owner, col, names=False)
    if isinstance(row, Nu) or isinstance(col, Nu):
        import nu

        return nu.str(row) + nu.Str(",") + nu.str(col)
    return f"{row},{col}"


def place_of(owner: str, at: object, *, what: str = "a cell", header: str | None = None) -> object:
    """``place`` for ``at`` written as one ``(row, column)`` tuple; anything else fails loud."""
    if not isinstance(at, tuple) or len(at) != 2:
        msg = f"{what} is (row, column), not {at!r}"
        raise TypeError(msg)
    return place(owner, *at, header=header)


def span_key(owner: str, at: object, *, what: str = "a span", header: str | None = None) -> str:
    """A ``spans=`` key ``(row, column)`` as the wire carries it, ``"r,c"``. Plain ints only."""
    if not isinstance(at, tuple) or len(at) != 2:
        msg = f"{what} is keyed by (row, column), not {at!r}"
        raise TypeError(msg)
    row, col = at
    key = place(owner, row, col, header=header)
    if isinstance(key, Nu):
        msg = "spans on slot() take plain ints; use set_span for a computed cell"
        raise TypeError(msg)
    return key  # type: ignore[return-value]


def normalize_spans(
    spans: Mapping[object, Span] | None, key: Callable[[object], str]
) -> dict[str, dict[str, int]]:
    """Spans as the wire carries them, ``{key(at): {"cols": c, "rows": r}}``.

    A plain 1 by 1 entry is dropped: it is what every cell already is.
    """
    out: dict[str, dict[str, int]] = {}
    for at, span in (spans or {}).items():
        cols, rows = span if isinstance(span, tuple) else (span, 1)
        cols, rows = int(cols), int(rows)
        if cols < 1 or rows < 1:
            msg = f"span of {at!r} must be at least 1 by 1, not {cols} by {rows}"
            raise ValueError(msg)
        if (cols, rows) != (1, 1):
            out[key(at)] = {"cols": cols, "rows": rows}
    return out
