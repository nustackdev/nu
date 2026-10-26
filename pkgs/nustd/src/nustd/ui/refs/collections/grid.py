"""``GridRef`` -- children in equal cells, row after row.

A flow container, Column and Row's sibling. Every child is one cell, every
cell has the same width, and the width of the page decides how many fit on
a row: a dashboard of stat cards, a gallery, a wall of charts. A child says
nothing about its cell; the grid sizes them all.

- ``columns=0`` puts as many columns on a row as fit at ``min_width``.
- ``columns=N`` puts at most N, never narrower than ``min_width``, so the
  same grid is three wide on a desktop and stacks on a phone.

A cell can be wider or taller than the rest, and that is the grid's to say
too: ``spans`` names the child by its key and how many tracks it covers, so
a bento of one featured card and small ones around it, or a 2/3 + 1/3 split,
is still a Grid of plain children. A span never exceeds the columns the
width leaves, so a stacked grid is a stack of plain cells. ``dense`` lets a
later cell fill a hole a wide one left.

    class Overview(Grid):
        revenue = CardRef.slot(title="Revenue")
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")

    overview = Overview.slot(columns=3, spans={"revenue": (2, 2)})

or at run time, a key computed like any address:

    grid.set_span(nu.Str("c") + nu.str(top), 2)

Declared, as a Shape:

    class Stats(Grid):
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")
        errors = CardRef.slot(title="Errors")

    stats = Stats.slot(columns=3)

Or as Refs alone, with computed keys for as many cells as there are items:

    grid = GridRef("g", parent_ref=page_column, props={"min_width": 200})
    card = CardRef(nu.Str("c") + nu.str(i), parent_ref=grid)
    StatRef("s", parent_ref=card).set(value)

The Shape over it lives in ``nustd.ui.shapes.grid``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Ref, Send, Write

from .base import DictCollectionRef


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang import Nu
    from nu.lang.args import IntArg, StrArg
    from nustd.ui.core import Section


__all__ = ["GridRef", "SetSpan"]


GridAlign = Literal["stretch", "start", "center", "end"]

#: A cell's span as written: columns alone, or (columns, rows).
Span = int | tuple[int, int]


class SetSpan(Send):
    """Make the cell at ``key`` ``cols`` tracks wide and ``rows`` tall; 1 and 1 is plain."""

    _payload_fields = ("key", "cols", "rows")


def _normalize_spans(spans: Mapping[str, Span] | None) -> dict[str, dict[str, int]]:
    """Spans as the wire carries them, ``{key: {"cols": c, "rows": r}}``.

    A plain 1 by 1 entry is dropped: it is what every cell already is.
    """
    out: dict[str, dict[str, int]] = {}
    for key, span in (spans or {}).items():
        cols, rows = span if isinstance(span, tuple) else (span, 1)
        cols, rows = int(cols), int(rows)
        if cols < 1 or rows < 1:
            msg = f"span of {key!r} must be at least 1 by 1, not {cols} by {rows}"
            raise ValueError(msg)
        if (cols, rows) != (1, 1):
            out[str(key)] = {"cols": cols, "rows": rows}
    return out


class GridRef(DictCollectionRef):
    """Equal cells, one child per cell, as many per row as the width allows.

    `columns` caps the cells on a row (0: no cap, the width decides),
    `min_width` is the narrowest a cell gets in px, `gap` and `padding` are
    steps on the spacing ladder. `align` places each child in its cell
    along the row: "stretch" gives every cell on a row the height of the
    tallest, so a row of cards lines up. `spans` maps a child's key to its
    columns, or to (columns, rows); `dense` backfills the holes spans leave.
    Pin chrome on slot().
    """

    _wire_type = "Grid"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        columns: int = 0,
        min_width: int = 240,
        gap: int = 4,
        align: GridAlign = "stretch",
        padding: int = 0,
        dense: bool = False,
        spans: Mapping[str, Span] | None = None,
    ) -> Self:
        return super().slot(
            item,
            columns=int(columns),
            min_width=int(min_width),
            gap=int(gap),
            align=align,
            padding=int(padding),
            dense=bool(dense),
            spans=_normalize_spans(spans),
        )

    def set_columns(self, n: IntArg) -> Nu:
        return Write(self, Dict.of(columns=n))

    def set_span(self, cell: Ref | StrArg, cols: IntArg, rows: IntArg = 1) -> Nu:
        """Span one cell, leaving the others' spans as they are.

        Args:
            cell: the child Ref, or its key. A Ref is read for its key only,
                so it names the cell whichever grid it was built under.
            cols: tracks wide, never more than the width leaves.
            rows: tracks tall. 1 by 1 makes the cell plain again.
        """
        key = cell._payload["segment"] if isinstance(cell, Ref) else cell
        return SetSpan(self, key, cols, rows)
