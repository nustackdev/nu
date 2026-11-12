"""``LineRef`` -- inline flow: children run and wrap like words in a paragraph.

A Line is how text runs, links, badges, keys and status dots sit in one
sentence. A plain string is still a ``TextRef`` and prose is still Markdown;
a Line is for the sentence that mixes a value or a control into the words.

The props are the container's own and nothing else: where the runs sit
along the line (``justify``: start, center, end) and whether they wrap
(``wrap=False`` keeps one line and clips the end with an ellipsis), plus the
size layer and ``padding`` (``layout``). Runs sit on the text's baseline,
the way words do, so a Line has no ``align``. A child carries no placement
props: the Line's inline flow decides how it draws, so the same Badge that
is a block in a Column is a run of text here.

As a Shape:

    class Status(Line):
        lead = TextRef.slot(value="Built with")
        link = LinkRef.slot(href="https://nustack.dev", label="Nu")
        tag = BadgeRef.slot(label="0.6", variant="info")

    status = Status.slot(justify="center")

As Refs alone, no Shape:

    line = LineRef("status", parent_ref=card, props={"wrap": False})
    line[0].to(TextRef).set("Built with")
    line[1].to(BadgeRef).set("0.6")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self, Unpack

from .base import ListCollectionRef
from .layout import SIZE, SizeLayout, flag


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot
    from nustd.ui.core import Ref, Section

    from .layout import Check


__all__ = ["LineRef"]


class LineLayout(SizeLayout, total=False):
    """A Line's layout: the size layer, ``padding`` and ``justify``."""

    padding: int
    justify: str


class LineRef(ListCollectionRef):
    """Children inline, wrapping at the container's width. Pin layout on slot()."""

    _wire_type = "Line"
    _layout: ClassVar[frozenset[str]] = SIZE | {"padding", "justify"}
    _justifies: ClassVar[tuple[str, ...]] = ("start", "center", "end")
    _family: ClassVar[Mapping[str, Check]] = {"wrap": flag}

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        wrap: bool | None = None,
        **layout: Unpack[LineLayout],
    ) -> Self:
        return super().slot(item, **cls._laid_out({**layout, "wrap": wrap}))
