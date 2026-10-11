"""``LineRef`` -- inline flow: children run and wrap like words in a paragraph.

A Line is how text runs, links, badges, keys and status dots sit in one
sentence. A plain string is still a ``TextRef`` and prose is still Markdown;
a Line is for the sentence that mixes a value or a control into the words.

The props are the container's own and nothing else: where the runs sit
(``align``) and whether they wrap (``wrap=False`` keeps one line and clips
the end with an ellipsis). A child carries no placement props: the Line's
inline flow decides how it draws, so the same Badge that is a block in a
Column is a run of text here.

As a Shape:

    class Status(Line):
        lead = TextRef.slot(value="Built with")
        link = LinkRef.slot(href="https://nustack.dev", label="Nu")
        tag = BadgeRef.slot(label="0.6", variant="info")

    status = Status.slot(align="center")

As Refs alone, no Shape:

    line = LineRef("status", parent_ref=card, props={"wrap": False})
    TextRef("lead", parent_ref=line).set("Built with")
    BadgeRef("tag", parent_ref=line).set("0.6")
"""

from __future__ import annotations

from typing import Literal

from typing_extensions import Self

from .base import ContainerRef


__all__ = ["LineRef"]


LineAlign = Literal["start", "center", "end"]


class LineRef(ContainerRef):
    """Children inline, wrapping at the container's width. Pin chrome on slot()."""

    _wire_type = "Line"

    @classmethod
    def slot(cls, *, align: LineAlign = "start", wrap: bool = True) -> Self:
        return super().slot(align=align, wrap=bool(wrap))
