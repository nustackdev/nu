"""``GridRef`` -- children in cells: equal cells that flow, or places on a board.

A flow container, Column and Row's sibling. Every child is one cell, every
cell has the same width, and the width of the page decides how many fit on
a row: a dashboard of stat cards, a gallery, a wall of charts. A child says
nothing about its cell; the grid sizes them all.

- ``max_columns=0`` (the default) puts as many columns on a row as fit at
  ``min_cell_width`` (240px).
- ``max_columns=N`` puts at most N, never narrower than ``min_cell_width``,
  so the same grid is three wide on a desktop and stacks on a phone.

A cell can be wider or taller than the rest, and that is the grid's to say
too: ``span`` names the child by its key and how many tracks it covers, so
a bento of one featured card and small ones around it, or a 2/3 + 1/3 split,
is still a Grid of plain children. A span never exceeds the columns the
width leaves, so a stacked grid is a stack of plain cells. ``dense`` lets a
later cell fill a hole a wide one left.

    class Overview(Grid):
        revenue = CardRef.slot(title="Revenue")
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")

    overview = Overview.slot(max_columns=3, span={"revenue": {"cols": 2, "rows": 2}})

or at run time, a key computed like any address:

    grid.set_child(nu.Str("c") + nu.str(top), span=2)

and the grid's own props the same way, ``grid.set_layout(max_columns=2)``
(any name ``slot()`` takes: tracks, ``dense``, the layers).

A flowing grid is an ordered collection: ``insert``, ``move``, ``remove``,
``truncate``, ``keep`` and ``set_order`` reorder its cells (see ``order``).

Placed: a track template (``cols``) turns the grid into a board of places.
``grid[r, c]`` is the cell at row ``r``, column ``c``, the way a content
table's ``t[r, c]`` is; a cell nobody writes stays empty, and ``span`` keyed
``(r, c)`` makes a cell cover more tracks:

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
  cells in reading order, so a phone gets a column.

A placed grid takes keyed children too (``grid["note"]``, ``grid[0]``): they
fill the free places, row after row. ``max_columns``, ``min_cell_width``
and the ordering ops are the flowing grid's: a placed grid refuses them.

Same ``[r, c]`` as a content ``TableRef``, different wire: the grid sits the
cell at one segment ``"r,c"`` right under itself (no row of its own, so no
``grid[r]``), the table has a row level (``t[r]`` is a ``TableRowRef`` and
the cell ``c`` sits under it).

The Shape over it lives in ``nustd.ui.shapes.grid``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self, Unpack

from nustd.ui.core import ItemRef, child_at
from nustd.ui.core.places import place, place_of, plain_place

from .base import DictCollectionRef
from .layout import ARRANGE, SIZE, SPACE, ArrangeLayout, ChildLayout, Span, flag, px
from .order import Ordered


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import IntArg
    from nustd.ui.core import Ref, Section

    from .layout import Check


__all__ = ["GridRef", "Tracks"]

#: A track template as written: N equal tracks, one entry per track, or CSS text.
Tracks = int | str | Sequence[int | str]

# What a track template may hold: CSS track sizes and the functions that build
# them. Anything else (a ``;``, a ``url(``) is refused before it reaches a style.
_TRACKS = re.compile(r"^[a-z0-9.%(), \-]+$")
_TRACK_FUNCTIONS = frozenset({"repeat", "minmax", "fit-content", "min", "max", "calc"})


def _normalize_tracks(_owner: str, name: str, tracks: object) -> str:
    """A track template as CSS text: N equal tracks, one per entry, or the text itself."""
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
    elif isinstance(tracks, Sequence):
        parts = []
        for t in tracks:
            if isinstance(t, bool) or not isinstance(t, int | str):
                msg = f"GridRef {name} track is px (int) or CSS text, not {t!r}"
                raise TypeError(msg)
            parts.append(f"{t}px" if isinstance(t, int) else str(t).strip())
        text = " ".join(parts)
    else:
        msg = f"GridRef {name} is a count, a list of tracks or CSS text, not {tracks!r}"
        raise TypeError(msg)
    if not text:
        msg = f"GridRef {name}: a template has at least one track"
        raise ValueError(msg)
    calls = set(re.findall(r"([a-z-]+)\(", text))
    if not _TRACKS.match(text) or not calls <= _TRACK_FUNCTIONS:
        msg = f"GridRef {name}={tracks!r} is not a track template (2fr 1fr, 240px auto, ...)"
        raise ValueError(msg)
    return text


class GridRef(ChildLayout, Ordered, DictCollectionRef):
    """Children in cells, one child per cell: flowing equal cells, or a board of places.

    Layers (``layout``): size, ``padding`` (0), ``gap`` (4), ``justify``
    (stretch) places each child across its cell, ``align`` (stretch) down
    it, so a row of cards lines up. Flowing: ``max_columns`` caps the cells
    on a row (0: the width decides), ``min_cell_width`` (px, 240) is the
    narrowest a cell gets. ``dense`` backfills the holes spans leave.

    ``cols`` (and ``rows``) make it a placed grid: ``grid[r, c]`` is the cell
    at a place, ``stack_below`` stacks it on a narrow screen. A placed grid
    refuses ``max_columns``, ``min_cell_width`` and the ordering ops. Both a
    placed grid and a content ``TableRef`` take ``[r, c]``, but the grid
    places the cell at one segment ``"r,c"`` (there is no ``grid[r]`` row),
    while the table has a row level on the wire.

    Per child: ``span`` (an int is columns, ``{"cols": c, "rows": r}`` both)
    and ``align_self``, keyed by the child's key, or ``(r, c)`` on a board.
    """

    _wire_type = "Grid"
    _layout: ClassVar[frozenset[str]] = SIZE | SPACE | ARRANGE
    _children: ClassVar[tuple[str, ...]] = ("span", "align_self")
    _justifies: ClassVar[tuple[str, ...]] = ("start", "center", "end", "stretch")
    _family: ClassVar[Mapping[str, Check]] = {
        "max_columns": lambda _o, name, v: _count(name, v),
        "min_cell_width": px,
        "dense": flag,
        "cols": _normalize_tracks,
        "rows": _normalize_tracks,
        "stack_below": px,
    }

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        max_columns: int | None = None,
        min_cell_width: int | None = None,
        dense: bool | None = None,
        cols: Tracks | None = None,
        rows: Tracks | None = None,
        stack_below: int | None = None,
        span: Mapping[object, Span] | None = None,
        align_self: Mapping[object, str] | None = None,
        **layout: Unpack[ArrangeLayout],
    ) -> Self:
        _check_mode(
            {
                "max_columns": max_columns,
                "min_cell_width": min_cell_width,
                "cols": cols,
                "rows": rows,
                "stack_below": stack_below,
            }
        )
        if cols is None and (rows is not None or stack_below is not None):
            msg = "GridRef rows= and stack_below= place cells on a template; give cols= too"
            raise ValueError(msg)
        family = {
            "max_columns": max_columns,
            "min_cell_width": min_cell_width,
            "dense": dense,
            "cols": cols,
            "rows": rows,
            "stack_below": stack_below,
        }
        props = cls._laid_out(
            {**layout, **family, "span": span, "align_self": align_self}, placed=cols is not None
        )
        return super().slot(item, **props)

    @classmethod
    def _child_key(cls, key: object, *, placed: bool = False, **_: object) -> str:
        if isinstance(key, tuple):
            if not placed:
                msg = "GridRef per child maps keyed (r, c) are for a placed grid; give cols= too"
                raise ValueError(msg)
            return plain_place("GridRef", key, what="a placed cell")
        if isinstance(key, str) and "," in key:
            msg = f"GridRef key {key!r} reads as a place; key a placed cell as (r, c)"
            raise ValueError(msg)
        return super()._child_key(key)

    def _child_runtime_key(self, key: object) -> object:
        if isinstance(key, tuple):
            self._require_placed()
            return place_of(self._owner_name(), key, what="a placed cell")
        return super()._child_runtime_key(key)

    def _check_ordered(self, op: str) -> None:
        if self._placed():
            owner = self._owner_name()
            msg = (
                f"{owner}.{op}: a placed grid (cols=) puts each cell at its place [r, c] and"
                f" keeps no order; reorder a flowing grid, or write the cell at another place"
            )
            raise TypeError(msg)

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
        self._require_placed()
        owner = self._owner_name()
        return child_at(self, place(owner, r, c), self._payload.get("item"))

    def _require_placed(self) -> None:
        if not self._placed():
            owner = self._owner_name()
            msg = (
                f"{owner}[r, c] places a cell on a track template, and this grid has none;"
                f' declare one with cols= (GridRef.slot(cols="2fr 1fr")), or reach'
                f" flowing cells as {owner}[i]"
            )
            raise TypeError(msg)

    def _placed(self) -> bool:
        props = self._payload.get("props") or {}
        return bool(props.get("cols"))

    def set_layout(self, **props: object) -> Nu:
        """Change the grid's props; a flowing grid's and a placed grid's never in one call."""
        _check_mode(props)
        return super().set_layout(**props)


def _check_mode(given: Mapping[str, object]) -> None:
    """Refuse the flowing grid's sizing beside a template: they are two kinds of grid."""
    flowing = [k for k in ("max_columns", "min_cell_width") if given.get(k) is not None]
    if flowing and given.get("cols") is not None:
        msg = (
            f"GridRef {' and '.join(flowing)} size a flowing grid; a placed grid (cols=)"
            f" sizes its cells by the template"
        )
        raise ValueError(msg)


def _count(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        msg = f"GridRef {name} is a count >= 0, not {value!r}"
        raise ValueError(msg)
    return value
