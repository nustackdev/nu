"""``GridRef`` -- children in equal cells, row after row.

A flow container, Column and Row's sibling. Every child is one cell, every
cell has the same width, and the width of the page decides how many fit on
a row: a dashboard of stat cards, a gallery, a wall of charts. A child says
nothing about its cell; the grid sizes them all.

- ``columns=0`` puts as many columns on a row as fit at ``min_width``.
- ``columns=N`` puts at most N, never narrower than ``min_width``, so the
  same grid is three wide on a desktop and stacks on a phone.

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
from nustd.ui.core import Write

from .base import DictContainerRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import IntArg
    from nustd.ui.core import Ref, Section


__all__ = ["GridRef"]


GridAlign = Literal["stretch", "start", "center", "end"]


class GridRef(DictContainerRef):
    """Equal cells, one child per cell, as many per row as the width allows.

    `columns` caps the cells on a row (0: no cap, the width decides),
    `min_width` is the narrowest a cell gets in px, `gap` and `padding` are
    steps on the spacing ladder. `align` places each child in its cell
    along the row: "stretch" gives every cell on a row the height of the
    tallest, so a row of cards lines up. Pin chrome on slot().
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
    ) -> Self:
        return super().slot(
            item,
            columns=int(columns),
            min_width=int(min_width),
            gap=int(gap),
            align=align,
            padding=int(padding),
        )

    def set_columns(self, n: IntArg) -> Nu:
        return Write(self, Dict.of(columns=n))
