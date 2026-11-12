"""Flow containers -- Refs that lay their children out and carry nothing else.

Column stacks its children, Row puts them side by side. Neither has chrome
of its own, so neither has a ``set()``: what you write to is the children.
Both speak the four layers of ``layout`` and keep the flow's per child maps
(``grow``, ``basis``, ``align_self``, ``sticky``), and both are ordered
collections (``insert``, ``move``, ... see ``order``). The Shapes over them
live in ``nustd.ui.shapes.flow``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self, Unpack

from .base import DictCollectionRef
from .layout import ARRANGE, SIZE, SPACE, ChildLayout, StackLayout, flag, px
from .order import Ordered


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot
    from nustd.ui.core import Ref, Section

    from .layout import Check


__all__ = ["FLOW_CHILDREN", "STACK", "ColumnRef", "RowRef"]


#: A stack's layer props: size, space, arrange, and a hairline between children.
STACK = SIZE | SPACE | ARRANGE | {"divided"}

#: The per child maps a flow keeps.
FLOW_CHILDREN = ("grow", "basis", "align_self", "sticky")


class ColumnRef(ChildLayout, Ordered, DictCollectionRef):
    """Children stacked top to bottom. Pin layout on the slot().

    Layers (``layout``): size, ``padding`` (0), ``gap`` (4), ``justify``
    (start) down the column, ``align`` (stretch) across it, ``divided`` a
    hairline between children. A ``max_width`` makes the column take the
    whole width up to it; where a capped column sits is its parent's to say
    (``align``, or ``align_self`` for it alone). For a page's frame,
    centred with its side gutter, reach for ``ContainerRef``.

    Per child: ``grow`` shares the height left over (a list under a header
    in a column of fixed height takes the rest), ``basis`` a child's height
    before growing, ``align_self``, ``sticky`` (``"top"`` / ``"bottom"``) to
    pin a head while the column scrolls.
    """

    _wire_type = "Column"
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


class RowRef(ChildLayout, Ordered, DictCollectionRef):
    """Children side by side, left to right. Pin layout on slot().

    Layers (``layout``): size, ``padding`` (0), ``gap`` (4), ``justify``
    (start) along the row, ``align`` (center) across it, ``baseline``
    included, ``divided`` a hairline between children. ``wrap`` lets
    children run onto more lines; ``stack_below`` (px) turns the row into a
    column when it is narrower than that, so a header with actions or two
    cards side by side stack on a phone.

    How a child sizes comes from its kind, not from a prop on it. A child
    with no width of its own (a chart, a table, an input, a card) fills: the
    fill children share the free width equally, starting from 240px, so a
    wrapping row wraps them there. Everything else (text, a button, a badge)
    keeps its own size.

    Per child: ``grow`` is a true ratio of the free width, ``grow={"a": 1,
    "b": 2}`` draws 1:2, a grown child starting from 0; ``basis`` its width
    before growing (``basis={"side": 280}`` is a 280px sidebar beside a
    filling main); ``align_self``; ``sticky`` (``"left"`` / ``"right"``).
    """

    _wire_type = "Row"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN
    _aligns: ClassVar[tuple[str, ...]] = ("start", "center", "end", "stretch", "baseline")
    _self_aligns: ClassVar[tuple[str, ...]] = ("start", "center", "end", "stretch", "baseline")
    _sticky_sides: ClassVar[tuple[str, ...]] = ("left", "right")
    _family: ClassVar[Mapping[str, Check]] = {"wrap": flag, "stack_below": px}

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        wrap: bool | None = None,
        stack_below: int | None = None,
        **layout: Unpack[StackLayout],
    ) -> Self:
        family = {"wrap": wrap, "stack_below": stack_below}
        return super().slot(item, **cls._laid_out({**layout, **family}))
