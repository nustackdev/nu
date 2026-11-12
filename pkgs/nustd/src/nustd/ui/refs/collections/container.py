"""``ContainerRef`` -- the page frame: a centred column capped at a page width.

What a program puts its visible content in. Full width up to the cap,
centred, fluid below it, so nothing jumps at a breakpoint. The one thing
that does follow the window is the side gutter: 16px on a phone, 32px from
a tablet, 48px from a desktop. Children stack with ``gap`` between them.
The Shape over it lives in ``nustd.ui.shapes.container``.

    class Movies(nustd.ui.Container):
        heading = nustd.ui.HeadingRef.slot(label="Your movies")
        shelf = Shelf.slot()

    movies = Movies.slot(max_width="panel")

Headless Refs (a TitleRef, a HistoryRef) stay at the root, outside it: they
draw nothing, so there is nothing to frame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self, Unpack

from .base import DictCollectionRef
from .flow import FLOW_CHILDREN, STACK
from .layout import ChildLayout, StackLayout


if TYPE_CHECKING:
    from nu.domains.shape import Slot
    from nustd.ui.core import Ref, Section


__all__ = ["ContainerRef"]


class ContainerRef(ChildLayout, DictCollectionRef):
    """The page frame. Pin layout on the slot().

    It speaks the layers of a Column (``layout``). ``max_width`` is the cap,
    ``"main"`` (1200) unless set: a page width name (``form`` 480, ``prose``
    640, ``panel`` 960, ``main``, ``dashboard`` 1400, ``full`` no cap) or any
    length. ``gap`` is 6. ``padding`` replaces the responsive side gutter with
    one step on every side; ``padding=0`` runs edge to edge.
    """

    _wire_type = "Container"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(item, **cls._laid_out(layout))
