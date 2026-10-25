"""Page containers -- the parts a page is made of: titled sections and navs.

``PageSectionRef`` is a titled part of a page, a heading and a line under
it with actions on the right and a body of children. ``NavListRef`` is a
run of nav items, a sidebar's list or a top bar's links. Both are
``ContainerRef``s with open-ended children; their chrome is props seeded by
``slot()`` and driven by ``set_*``. The Shapes over them live in
``nustd.ui.shapes.page``.

A page, end to end, from Refs alone:

    page = ColumnRef("page", props={"max_width": "main", "padding": 6})
    usage = PageSectionRef("usage", parent_ref=page, props={"title": "Usage"})
    ButtonRef("export", parent_ref=usage.actions, props={"label": "Export"})
    GridRef("stats", parent_ref=usage, props={"columns": 3})

The section is named ``PageSection`` because ``Section`` is already the
Shape base every container Shape builds on. Shape, Ref and wire type are
``PageSection`` all three, like every other container.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Write

from ._named import actions_ref
from .base import DictContainerRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, IntArg, StrArg
    from nustd.ui.core import Ref, Section


__all__ = ["NavListRef", "PageSectionRef"]


SectionSize = Literal["md", "lg"]
NavVariant = Literal["vertical", "horizontal"]


class PageSectionRef(DictContainerRef):
    """A titled part of a page: heading, description, actions, then the body.

    The child at key ``"actions"`` draws on the header's right, at its own
    size, a Button or a Row of them; ``section.actions`` is that Row, ready
    to put buttons in. Every other child is the body, stacked with ``gap``
    (a spacing step) between them. `size` is the space between header and
    body (24 or 32 px), `bordered` a hairline over the section, for one
    section after another down a page. No header draws with no title,
    description or actions.
    """

    _wire_type = "PageSection"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        title: str = "",
        description: str = "",
        size: SectionSize = "md",
        bordered: bool = False,
        gap: int = 4,
    ) -> Self:
        return super().slot(
            item,
            title=title,
            description=description,
            size=size,
            bordered=bool(bordered),
            gap=int(gap),
        )

    @property
    def actions(self) -> Ref:
        """The header's action area: the Shape's ``actions`` slot, or a Row there."""
        return actions_ref(self)

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set_description(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(description=text))

    def set_bordered(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(bordered=flag))

    def set_size(self, name: SectionSize | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set_gap(self, step: IntArg) -> Nu:
        return Write(self, Dict.of(gap=step))


class NavListRef(DictContainerRef):
    """A run of nav items: a sidebar's list, or a top bar's links.

    "vertical" stacks the items as full width rows, under `label` as a small
    group heading. "horizontal" puts them on one line at their own widths,
    scrolling sideways when it runs out of room; `label` only names the
    landmark there. Mostly ``NavItemRef`` children, but any node goes: a
    Divider between groups, a Button at the end of a bar.
    """

    _wire_type = "NavList"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        variant: NavVariant = "vertical",
        label: str = "",
    ) -> Self:
        return super().slot(item, variant=variant, label=label)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_variant(self, name: NavVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))
