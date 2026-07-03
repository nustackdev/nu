"""Row: horizontal Section. Arranges child slots horizontally.

A Row is a Shape (Section) — not a Ref. Subclass it, declare children
as slots, then drop the subclass into an enclosing Page (or another
Section) as `toolbar = Toolbar.slot()`.

Example::

    class Toolbar(nudle.Row):
        gap = 3
        align = "center"
        text = nudle.TextRef.slot()
        btn = nudle.ButtonRef.slot()


    class HomePage(nudle.Page):
        toolbar = Toolbar.slot()

The wire payload for `HomePage.toolbar` is a layout entry of type
`"Row"` carrying `props` (gap, align, ...) and a nested `fields` list
for the children.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from .section import Section


__all__ = ["Row"]


Align = Literal["start", "center", "end", "stretch", "baseline"]
Justify = Literal["start", "center", "end", "between", "around", "evenly"]


class Row(Section):
    """Horizontal flex layout. Pin chrome on the subclass."""

    gap: ClassVar[int] = 4
    align: ClassVar[str] = "center"
    justify: ClassVar[str] = "start"
    wrap: ClassVar[bool] = False
    padding: ClassVar[int] = 0

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "gap": cls.gap,
            "align": cls.align,
            "justify": cls.justify,
            "wrap": cls.wrap,
            "padding": cls.padding,
        }
