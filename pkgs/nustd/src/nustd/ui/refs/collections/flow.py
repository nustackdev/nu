"""Flow containers -- Refs that lay their children out and carry nothing else.

Column stacks its children, Row puts them side by side. Neither has chrome
of its own beyond spacing and alignment, so neither has a ``set()``: what
you write to is the children. The Shapes over them live in
``nustd.ui.shapes.flow``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from .base import DictCollectionRef
from .sizing import normalize_weights, sizing_props


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot
    from nustd.ui.core import Ref, Section

    from ..vocab import Align, PageWidth
    from .sizing import Length, Scroll


__all__ = ["ColumnRef", "RowRef"]


Justify = Literal["start", "center", "end", "between", "around", "evenly"]


class ColumnRef(DictCollectionRef):
    """Vertical flex layout. Pin chrome on the slot().

    `max_width` caps the column at a named page width (``PageWidth``), and
    `center` puts the capped column in the middle of what holds it. Under the
    cap it takes the whole width it is given, the way an uncapped one does.
    For a page's frame, with its side gutter, reach for ``ContainerRef``.

    `height`, `max_height` and `scroll` size the column and scroll what runs
    past it (see ``sizing``). `grow` maps a child's key to its share of the
    height left over, so in a column of fixed height a list under a header
    takes the rest; `basis` maps a child's key to its height in px before
    any growing.
    """

    _wire_type = "Column"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        gap: int = 4,
        align: Align = "stretch",
        justify: Justify = "start",
        padding: int = 0,
        max_width: PageWidth = "full",
        center: bool = True,
        height: Length | None = None,
        max_height: Length | None = None,
        scroll: Scroll = "none",
        grow: Mapping[int | str, int] | None = None,
        basis: Mapping[int | str, int] | None = None,
    ) -> Self:
        return super().slot(
            item,
            gap=int(gap),
            align=align,
            justify=justify,
            padding=int(padding),
            max_width=max_width,
            center=bool(center),
            **sizing_props("ColumnRef", height=height, max_height=max_height, scroll=scroll),
            **_child_sizes("ColumnRef", grow, basis),
        )


RowAlign = Literal["start", "center", "end", "stretch", "baseline"]
RowJustify = Literal["start", "center", "end", "between", "around", "evenly"]


class RowRef(DictCollectionRef):
    """Horizontal flex layout. Pin chrome on slot().

    How a child sizes comes from its kind, not from a prop on it. A child with
    no width of its own (a chart, a table, an input, a card) fills: the fill
    children share the free width equally. Everything else (text, a button, a
    badge) keeps its own size. ``min_width`` (px, on the 4px grid) is the
    width a fill child asks for before it grows: a wrapping Row wraps fill
    children at it, several per line rather than one per line, and a Row that
    does not wrap shrinks them below it only once the line is full.

    One child can still say otherwise, from the Row: `grow` maps a child's
    key to its weight (a fill child weighs 1, so ``grow={"main": 2}`` takes
    twice a plain one's share, and a content child given a weight grows
    too); `basis` maps a child's key to its width in px before any growing,
    so ``basis={"side": 280}`` is a 280px sidebar beside a filling main.
    `height`, `max_height` and `scroll` size the row (see ``sizing``).
    """

    _wire_type = "Row"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        gap: int = 4,
        align: RowAlign = "center",
        justify: RowJustify = "start",
        wrap: bool = False,
        padding: int = 0,
        min_width: int = 240,
        height: Length | None = None,
        max_height: Length | None = None,
        scroll: Scroll = "none",
        grow: Mapping[int | str, int] | None = None,
        basis: Mapping[int | str, int] | None = None,
    ) -> Self:
        return super().slot(
            item,
            gap=int(gap),
            align=align,
            justify=justify,
            wrap=bool(wrap),
            padding=int(padding),
            min_width=int(min_width),
            **sizing_props("RowRef", height=height, max_height=max_height, scroll=scroll),
            **_child_sizes("RowRef", grow, basis),
        )


def _child_sizes(
    owner: str,
    grow: Mapping[int | str, int] | None,
    basis: Mapping[int | str, int] | None,
) -> dict[str, object]:
    """``grow`` / ``basis`` as the wire keys them, each only when given."""
    out: dict[str, object] = {}
    if grow:
        out["grow"] = normalize_weights(owner, "grow", grow)
    if basis:
        out["basis"] = normalize_weights(owner, "basis", basis)
    return out
