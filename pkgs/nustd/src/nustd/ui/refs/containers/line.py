"""``LineRef`` -- inline flow: children run and wrap like words in a paragraph.

STUB, wired end to end so the line unit only fills it in. A Line is how text
runs, links, badges and keys sit in one sentence; a plain string is still a
TextRef, and prose is still Markdown. How each content leaf draws inline is
the line unit's.
"""

from __future__ import annotations

from typing_extensions import Self

from .base import ContainerRef


__all__ = ["LineRef"]


class LineRef(ContainerRef):
    """Children inline, wrapping at the container's width."""

    _wire_type = "Line"

    @classmethod
    def slot(cls) -> Self:
        return super().slot()
