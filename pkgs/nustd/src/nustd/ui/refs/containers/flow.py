"""Flow containers -- Refs that lay their children out and carry nothing else.

Column stacks its children, Row puts them side by side. Neither has chrome
of its own beyond spacing and alignment, so neither has a ``set()``: what
you write to is the children. The Shapes over them live in
``nustd.ui.shapes.flow``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from .base import DictContainerRef


if TYPE_CHECKING:
    from nustd.ui.core import Ref, Section


__all__ = ["ColumnRef", "RowRef"]


Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around"]


class ColumnRef(DictContainerRef):
    """Vertical flex layout. Pin chrome on the slot()."""

    _wire_type = "Column"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        gap: int = 4,
        align: Align = "stretch",
        justify: Justify = "start",
        padding: int = 0,
    ) -> Self:
        return super().slot(item, gap=gap, align=align, justify=justify, padding=padding)


RowAlign = Literal["start", "center", "end", "stretch", "baseline"]
RowJustify = Literal["start", "center", "end", "between", "around", "evenly"]


class RowRef(DictContainerRef):
    """Horizontal flex layout. Pin chrome on slot().

    How a child sizes comes from its kind, not from a prop on it. A child with
    no width of its own (a chart, a table, an input, a card) fills: the fill
    children share the free width equally. Everything else (text, a button, a
    badge) keeps its own size. ``min_width`` (px, on the 4px grid) is the
    width a fill child asks for before it grows: a wrapping Row wraps fill
    children at it, several per line rather than one per line, and a Row that
    does not wrap shrinks them below it only once the line is full.
    """

    _wire_type = "Row"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        gap: int = 4,
        align: RowAlign = "center",
        justify: RowJustify = "start",
        wrap: bool = False,
        padding: int = 0,
        min_width: int = 240,
    ) -> Self:
        return super().slot(
            item,
            gap=gap,
            align=align,
            justify=justify,
            wrap=wrap,
            padding=padding,
            min_width=min_width,
        )
