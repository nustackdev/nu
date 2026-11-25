"""Quote -- a header line over a body, set apart as quoted.

``QuoteRef`` draws the conventional quote look: an accent rule down the left
edge and the text inside one step quieter than the page. The header is a
line of anything (an icon, a label and a time; the source of a citation),
the body any children stacked like a Column. It suits citations, notes and
traces of work in progress alike; nothing in it is tied to one use.

The Shape over it lives in ``nustd.ui.shapes.quote``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self, Unpack

from nustd.ui.core.interactions import Write

from .base import DictCollectionRef
from .flow import FLOW_CHILDREN, STACK
from .layout import ChildLayout, StackLayout
from .named import HEADER, header_ref


if TYPE_CHECKING:
    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import StrArg
    from nustd.ui.core import Ref, Section


__all__ = ["QuoteRef"]


class QuoteRef(ChildLayout, DictCollectionRef):
    """A header line over a body, drawn as a quote: a left accent rule, quiet text.

    One child key is the quote's own place, not body: ``header`` draws on
    top, full width, so a Row there (an icon, a label, a time) or a Line
    (a citation) lays itself out and may truncate. ``quote.header`` answers
    with that child: the Shape's ``header`` slot, or a Row there. The string
    ``title`` (``set_title``) is the shorthand header, drawn only when no
    header child is set. Every other child is the body.

    The body speaks the layers of a Column (``layout``): ``gap`` (2),
    ``padding``, ``justify``, ``align``, ``divided``, and the per child maps.
    The size props sit on the quote; with ``scroll`` the body scrolls under
    the header.
    """

    _wire_type = "Quote"
    _parts: ClassVar[frozenset[str]] = frozenset({HEADER})
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        title: str = "",
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(item, title=title, **cls._laid_out(layout))

    @property
    def header(self) -> Ref:
        """The header line: the Shape's ``header`` slot, or a Row there."""
        return header_ref(self)

    def set_title(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(title=text))
