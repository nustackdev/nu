"""Flow containers -- Refs that lay their children out and carry nothing else.

Column stacks its children, Row puts them side by side. Neither has chrome
of its own beyond spacing and alignment, so neither has a ``set()``: what
you write to is the children. The Shapes over them live in
``nustd.ui.shapes.flow``.
"""

from __future__ import annotations

from typing import Literal

from typing_extensions import Self

from .base import ContainerRef


__all__ = ["ColumnRef", "RowRef"]


Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around"]


class ColumnRef(ContainerRef):
    """Vertical flex layout. Pin chrome on the slot()."""

    _wire_type = "Column"

    @classmethod
    def slot(
        cls,
        *,
        gap: int = 4,
        align: Align = "stretch",
        justify: Justify = "start",
        padding: int = 0,
    ) -> Self:
        return super().slot(gap=gap, align=align, justify=justify, padding=padding)


RowAlign = Literal["start", "center", "end", "stretch", "baseline"]
RowJustify = Literal["start", "center", "end", "between", "around", "evenly"]


class RowRef(ContainerRef):
    """Horizontal flex layout. Pin chrome on slot()."""

    _wire_type = "Row"

    @classmethod
    def slot(
        cls,
        *,
        gap: int = 4,
        align: RowAlign = "center",
        justify: RowJustify = "start",
        wrap: bool = False,
        padding: int = 0,
    ) -> Self:
        return super().slot(gap=gap, align=align, justify=justify, wrap=wrap, padding=padding)
