"""``ContainerRef`` -- the page frame: a centred column capped at a page width.

What a program puts its visible content in. Full width up to the cap,
centred, fluid below it, so nothing jumps at a breakpoint. The one thing
that does follow the window is the side gutter: 16px on a phone, 32px from
a tablet, 48px from a desktop. Children stack with ``gap`` between them.
The Shape over it lives in ``nustd.ui.shapes.container``.

    class Movies(nustd.ui.Container):
        heading = nustd.ui.HeadingRef.slot(label="Your movies")
        shelf = Shelf.slot()

    movies = Movies.slot(size="main")

Headless Refs (a TitleRef, a HistoryRef) stay at the root, outside it: they
draw nothing, so there is nothing to frame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Write

from .base import DictCollectionRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import IntArg, StrArg
    from nustd.ui.core import Ref, Section

    from ..vocab import PageWidth


__all__ = ["ContainerPadding", "ContainerRef"]


#: The side gutter: the responsive one, or none for an edge-to-edge page.
ContainerPadding = Literal["gutter", "none"]


class ContainerRef(DictCollectionRef):
    """The page frame. Pin chrome on the slot().

    `size` is the cap, a named page width (``PageWidth``): ``form`` 480,
    ``prose`` 640, ``panel`` 960, ``main`` 1200 (the default), ``dashboard``
    1400, ``full`` no cap. `gap` is the spacing step between children, as on
    a Column. `padding` ``"none"`` drops the side gutter, for a canvas that
    runs edge to edge.
    """

    _wire_type = "Container"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        size: PageWidth = "main",
        gap: int = 6,
        padding: ContainerPadding = "gutter",
    ) -> Self:
        return super().slot(item, size=size, gap=int(gap), padding=padding)

    def set_size(self, name: PageWidth | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set_gap(self, step: IntArg) -> Nu:
        return Write(self, Dict.of(gap=step))

    def set_padding(self, name: ContainerPadding | StrArg) -> Nu:
        return Write(self, Dict.of(padding=name))
