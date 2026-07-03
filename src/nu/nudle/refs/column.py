"""Column: vertical Section. Stacks child slots vertically.

A Column is a Shape (Section), not a Ref. Subclass it, declare children
as slots, mount as `toolbar = Toolbar.slot()`.

Example::

    class FeatureCol(nudle.Column):
        gap = 2
        heading = nudle.HeadingRef.slot()
        text = nudle.TextRef.slot()
"""

from __future__ import annotations

from typing import ClassVar, Literal

from .section import Section


__all__ = ["Column"]


Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around"]


class Column(Section):
    """Vertical flex layout. Pin chrome on the subclass."""

    gap: ClassVar[int] = 4
    align: ClassVar[str] = "stretch"
    justify: ClassVar[str] = "start"
    padding: ClassVar[int] = 0

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "gap": cls.gap,
            "align": cls.align,
            "justify": cls.justify,
            "padding": cls.padding,
        }
