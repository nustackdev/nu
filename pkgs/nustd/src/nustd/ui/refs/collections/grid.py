"""``GridRef`` -- children in equal cells, row after row.

A flow container, Column and Row's sibling. Every child is one cell, every
cell has the same width, and the width of the page decides how many fit on
a row: a dashboard of stat cards, a gallery, a wall of charts. A child says
nothing about its cell; the grid sizes them all.

- ``max_columns=0`` puts as many columns on a row as fit at ``min_width``.
- ``max_columns=N`` puts at most N, never narrower than ``min_width``, so the
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

    overview = Overview.slot(max_columns=3, spans={"revenue": (2, 2)})

or at run time, a key computed like any address:

    grid.set_span(nu.Str("c") + nu.str(top), 2)

Declared, as a Shape:

    class Stats(Grid):
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")
        errors = CardRef.slot(title="Errors")

    stats = Stats.slot(max_columns=3)

Or as Refs alone, with computed keys for as many cells as there are items:

    grid = GridRef("g", parent_ref=page_column, props={"min_width": 200})
    card = CardRef(nu.Str("c") + nu.str(i), parent_ref=grid)
    StatRef("s", parent_ref=card).set(value)

Placed: a track template (``cols``) turns the grid into a board of places.
``grid[r, c]`` is the cell at row ``r``, column ``c``, the way a content
table's ``t[r, c]`` is; a cell nobody writes stays empty, and ``spans`` keyed
``(r, c)`` make a cell cover more tracks:

    board = GridRef("board", parent_ref=page, props={"cols": "2fr 1fr", "rows": [64, "1fr"]})
    board[0, 0].to(HeadingRef).set("Overview")
    board[1, 0].to(ChartRef.slot(type="line"))
    board[1, 1].to(ColumnRef)[0].to(StatRef).set(42)

- ``cols``: the column tracks. An int N is N equal columns, a list is one
  track each (an int is px, text is any CSS track: ``"2fr"``, ``"auto"``,
  ``"minmax(200px, 1fr)"``), a string is the template as CSS writes it.
- ``rows``: the row tracks, the same way. Rows past the template size to
  their content.
- ``stack_below``: under this width (px) the board stacks to one column,
  cells in reading order, so a phone gets a column. 0 never stacks.

A placed grid takes keyed children too (``grid["note"]``, ``grid[0]``): they
fill the free places, row after row. ``max_columns``, ``min_width`` and the
width-driven span clamp are the flow grid's: a placed grid refuses them.

Same ``[r, c]`` as a content ``TableRef``, different wire: the grid sits the
cell at one segment ``"r,c"`` right under itself (no row of its own, so no
``grid[r]``), the table has a row level (``t[r]`` is a ``TableRowRef`` and
the cell ``c`` sits under it).

The Shape over it lives in ``nustd.ui.shapes.grid``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang import Nu
from nustd.ui.core import ItemRef, Ref, Write, child_at
from nustd.ui.core.places import SetSpan, Span, normalize_spans, place, place_of, span_key

from .base import DictCollectionRef
from .sizing import sizing_props


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot
    from nu.lang.args import IntArg, StrArg
    from nustd.ui.core import Section

    from .sizing import Length, Scroll


__all__ = ["GridRef", "SetSpan", "Tracks"]


GridAlign = Literal["stretch", "start", "center", "end"]

#: A track template as written: N equal tracks, one entry per track, or CSS text.
Tracks = int | str | Sequence[int | str]

# What a track template may hold: CSS track sizes and the functions that build
# them. Anything else (a ``;``, a ``url(``) is refused before it reaches a style.
_TRACKS = re.compile(r"^[a-z0-9.%(), \-]+$")
_TRACK_FUNCTIONS = frozenset({"repeat", "minmax", "fit-content", "min", "max", "calc"})


def _span_key(key: object) -> str:
    """A spans key as the wire carries it: a child's key, or ``"r,c"`` for a place."""
    if isinstance(key, tuple):
        return span_key("GridRef", key, what="a placed span")
    return str(key)


def _normalize_tracks(name: str, tracks: Tracks | None) -> str | None:
    """A track template as CSS text: N equal tracks, one per entry, or the text itself."""
    if tracks is None:
        return None
    if isinstance(tracks, bool):
        msg = f"GridRef {name} is a count, a list of tracks or CSS text, not {tracks!r}"
        raise TypeError(msg)
    if isinstance(tracks, int):
        if tracks < 1:
            msg = f"GridRef {name}={tracks}: a template has at least one track"
            raise ValueError(msg)
        return f"repeat({tracks}, minmax(0, 1fr))"
    if isinstance(tracks, str):
        text = " ".join(tracks.split())
    else:
        parts = []
        for t in tracks:
            if isinstance(t, bool) or not isinstance(t, int | str):
                msg = f"GridRef {name} track is px (int) or CSS text, not {t!r}"
                raise TypeError(msg)
            parts.append(f"{t}px" if isinstance(t, int) else str(t).strip())
        text = " ".join(parts)
    if not text:
        msg = f"GridRef {name}: a template has at least one track"
        raise ValueError(msg)
    calls = set(re.findall(r"([a-z-]+)\(", text))
    if not _TRACKS.match(text) or not calls <= _TRACK_FUNCTIONS:
        msg = f"GridRef {name}={tracks!r} is not a track template (2fr 1fr, 240px auto, ...)"
        raise ValueError(msg)
    return text


class GridRef(DictCollectionRef):
    """Equal cells, one child per cell, as many per row as the width allows.

    `max_columns` caps the cells on a row (0: no cap, the width decides),
    `min_width` is the narrowest a cell gets in px, `gap` and `padding` are
    steps on the spacing ladder. `align` places each child in its cell
    along the row: "stretch" gives every cell on a row the height of the
    tallest, so a row of cards lines up. `spans` maps a child's key to its
    columns, or to (columns, rows); `dense` backfills the holes spans leave.
    Pin chrome on slot().

    `cols` (and `rows`) make it a placed grid: ``grid[r, c]`` is the cell at
    a place, spans are keyed ``(r, c)``, `stack_below` stacks it on a narrow
    screen. A placed grid takes no `max_columns` / `min_width` and ships
    neither; a flowing one ships no templates. Both a placed grid and a
    content ``TableRef`` take ``[r, c]``, but the grid places the cell at one
    segment ``"r,c"`` (there is no ``grid[r]`` row), while the table has a row
    level on the wire (``t[r]`` is a ``TableRowRef``, the cell sits under it). `height`, `max_height` and `scroll` size it (see ``sizing``).
    """

    _wire_type = "Grid"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        max_columns: int | None = None,
        min_width: int | None = None,
        gap: int = 4,
        align: GridAlign = "stretch",
        padding: int = 0,
        dense: bool = False,
        spans: Mapping[object, Span] | None = None,
        cols: Tracks | None = None,
        rows: Tracks | None = None,
        stack_below: int = 0,
        height: Length | None = None,
        max_height: Length | None = None,
        scroll: Scroll = "none",
    ) -> Self:
        # Each mode ships its own props only: a flow grid its width-driven
        # cap and cell width, a placed one its templates.
        mode: dict[str, object]
        col_tracks = _normalize_tracks("cols", cols)
        row_tracks = _normalize_tracks("rows", rows)
        if col_tracks is not None:
            if max_columns is not None or min_width is not None:
                msg = (
                    "GridRef max_columns= and min_width= size a flowing grid;"
                    " a placed grid (cols=) sizes its cells by the template"
                )
                raise ValueError(msg)
            mode = {"cols": col_tracks, "stack_below": int(stack_below)}
            if row_tracks is not None:
                mode["rows"] = row_tracks
        elif row_tracks is not None or stack_below:
            msg = "GridRef rows= and stack_below= place cells on a template; give cols= too"
            raise ValueError(msg)
        elif any(isinstance(k, tuple) for k in spans or {}):
            msg = "GridRef spans keyed (r, c) are for a placed grid; give cols= too"
            raise ValueError(msg)
        else:
            mode = {
                "max_columns": int(max_columns or 0),
                "min_width": int(240 if min_width is None else min_width),
            }
        return super().slot(
            item,
            **mode,
            gap=int(gap),
            align=align,
            padding=int(padding),
            dense=bool(dense),
            spans=normalize_spans(spans, _span_key),
            **sizing_props("GridRef", height=height, max_height=max_height, scroll=scroll),
        )

    # --- descent -------------------------------------------------------------

    def __getitem__(self, key: object) -> ItemRef:
        """``grid[i]`` / ``grid["k"]`` is a flowing cell; ``grid[r, c]`` a placed one."""
        if isinstance(key, tuple):
            if len(key) != 2:
                msg = f"GridRef places are grid[row, column], not grid[{key!r}]"
                raise TypeError(msg)
            return self.cell(*key)
        if isinstance(key, str) and "," in key:
            msg = f"GridRef[{key!r}] reads as a place; use grid[r, c] for a placed cell"
            raise ValueError(msg)
        return self._child(key)

    def cell(self, r: IntArg, c: IntArg) -> ItemRef:
        """The cell at row ``r``, column ``c`` of a placed grid, the same as ``grid[r, c]``."""
        owner = self._owner_name()
        if not self._placed():
            msg = (
                f"{owner}[r, c] places a cell on a track template, and this grid has none;"
                f' declare one with cols= (GridRef.slot(cols="2fr 1fr")), or reach'
                f" flowing cells as {owner}[i]"
            )
            raise TypeError(msg)
        return child_at(self, place(owner, r, c), self._payload.get("item"))

    def _placed(self) -> bool:
        props = self._payload.get("props") or {}
        return bool(props.get("cols"))

    # --- chrome --------------------------------------------------------------

    def set_max_columns(self, n: IntArg) -> Nu:
        """Cap a flowing grid at ``n`` cells a row; 0 lets the width decide."""
        return Write(self, Dict.of(max_columns=n))

    def set_cols(self, tracks: Tracks) -> Nu:
        """Replace a placed grid's column tracks (``"2fr 1fr"``, ``[240, "1fr"]``, 3)."""
        value = tracks if isinstance(tracks, Nu) else _normalize_tracks("cols", tracks)
        return Write(self, Dict.of(cols=value))

    def set_rows(self, tracks: Tracks) -> Nu:
        """Replace a placed grid's row tracks, the same way as ``set_cols``."""
        value = tracks if isinstance(tracks, Nu) else _normalize_tracks("rows", tracks)
        return Write(self, Dict.of(rows=value))

    def set_span(
        self, cell: Ref | StrArg | tuple[IntArg, IntArg], cols: IntArg, rows: IntArg = 1
    ) -> Nu:
        """Span one cell, leaving the others' spans as they are.

        Args:
            cell: the child Ref, its key, or ``(r, c)`` for a placed cell. A
                Ref is read for its key only, so it names the cell whichever
                grid it was built under.
            cols: tracks wide, never more than the grid has.
            rows: tracks tall. 1 by 1 makes the cell plain again.
        """
        if isinstance(cell, tuple):
            key: object = place_of(self._owner_name(), cell, what="a placed cell")
        else:
            key = cell._payload["segment"] if isinstance(cell, Ref) else cell
        return SetSpan(self, key, cols, rows)
