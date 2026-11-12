"""Page containers -- the parts a page is made of: titled sections and navs.

``PageSectionRef`` is a titled part of a page, a heading and a line under
it with actions on the right and a body of children. ``NavListRef`` is a
run of nav items, a sidebar's list or a top bar's links. Both are
``CollectionRef``s with open-ended children; their chrome is props seeded by
``slot()`` and driven by ``set_*``. The Shapes over them live in
``nustd.ui.shapes.page``.

A page, end to end, from Refs alone:

    page = ContainerRef("page", props={"max_width": "main"})
    usage = PageSectionRef("usage", parent_ref=page, props={"title": "Usage"})
    ButtonRef("export", parent_ref=usage.actions, props={"label": "Export"})
    GridRef("stats", parent_ref=usage, props={"max_columns": 3})

The section is named ``PageSection`` because ``Section`` is already the
Shape base every container Shape builds on. Shape, Ref and wire type are
``PageSection`` all three, like every other container.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import Self, Unpack

from nu.forms import Dict
from nustd.ui.core import Write

from .base import DictCollectionRef
from .flow import FLOW_CHILDREN, STACK
from .layout import SIZE, SPACE, ChildLayout, SpaceLayout, StackLayout, choice
from .named import ACTIONS, actions_ref


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import StrArg
    from nustd.ui.core import Ref, Section

    from .layout import Check


__all__ = ["NavListRef", "PageSectionRef"]


SectionSize = Literal["md", "lg"]
NavVariant = Literal["vertical", "horizontal"]
_SECTION_SIZES = ("md", "lg")
_NAV_VARIANTS = ("vertical", "horizontal")


class PageSectionRef(ChildLayout, DictCollectionRef):
    """A titled part of a page: heading, description, actions, then the body.

    The child at key ``"actions"`` draws on the header's right, at its own
    size, a Button or a Row of them; ``section.actions`` is that Row, ready
    to put buttons in. Every other child is the body. No header draws with
    no title, description or actions.

    Surface: ``size`` is the preset for the section's look, the space
    between header and body (``md`` 24, ``lg`` 32 px), changed at run time
    through ``set_layout`` with the layers. The body speaks the
    layers of a Column (``layout``): ``gap`` (4), ``padding``, ``justify``,
    ``align``, ``divided``, and the per child maps. For a hairline between
    one section and the next, say ``divided=True`` on what stacks them.
    """

    _wire_type = "PageSection"
    _parts: ClassVar[frozenset[str]] = frozenset({ACTIONS})
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN
    _family: ClassVar[Mapping[str, Check]] = {"size": choice(*_SECTION_SIZES)}

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        title: str = "",
        description: str = "",
        size: SectionSize | None = None,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            title=title,
            description=description,
            **cls._laid_out({**layout, "size": size}),
        )

    @property
    def actions(self) -> Ref:
        """The header's action area: the Shape's ``actions`` slot, or a Row there."""
        return actions_ref(self)

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set_description(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(description=text))


class NavListRef(DictCollectionRef):
    """A run of nav items: a sidebar's list, or a top bar's links.

    "vertical" stacks the items as full width rows, under `label` as a small
    group heading. "horizontal" puts them on one line at their own widths,
    scrolling sideways when it runs out of room; `label` only names the
    landmark there. Mostly ``NavItemRef`` children, but any child goes: a
    Divider between groups, a Button at the end of a bar. Layers
    (``layout``): size, ``padding``, ``gap`` (2px vertical, 4px horizontal
    unless set); ``set_layout`` changes them and ``variant`` at run time.
    """

    _wire_type = "NavList"
    _layout: ClassVar[frozenset[str]] = SIZE | SPACE
    _family: ClassVar[Mapping[str, Check]] = {"variant": choice(*_NAV_VARIANTS)}

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        variant: NavVariant = "vertical",
        label: str = "",
        **layout: Unpack[SpaceLayout],
    ) -> Self:
        return super().slot(item, label=label, **cls._laid_out({**layout, "variant": variant}))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))
