"""Chrome containers -- Refs for the boxes that frame their children.

Card, Box (``BoxRef``), Tabs, Modal, Accordion, Form, Fieldset and
Field. Each is a ``CollectionRef``: children are open-ended, and the chrome
the box carries of its own (a Card's title, a Tabs' active tab, a Field's
label) is props seeded by ``slot()`` and driven by ``set_*``. The Shapes over
them live in ``nustd.ui.shapes.chrome``.

The chrome commands (`_SetSectionStr`, `_SetTabs`, `_SetActive`) are
``Send`` subclasses, so they target the abstract ``Session`` from core like
every other interaction and carry the Ref's chain: a Card or Tabs that does
not exist in the browser yet is created by the frame that sets its chrome.
Chrome is driven off the bound Ref (``page.card.set_title(...)`` or
``CardRef("c", parent_ref=col).set_title(...)``), and the address comes from
that Ref's chain. There is no way to drive a container off a Shape class:
a class has no mount point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core.interactions import Changed, Send, Write

from ..vocab import Align, Target
from ..vocab import set_href as _set_href
from .base import DictCollectionRef, ShapeCollectionRef
from .named import actions_ref, footer_ref, media_ref


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import Arg, BoolArg, ListArg, StrArg
    from nustd.ui.core import Ref, Section


__all__ = [
    "AccordionRef",
    "BoxRef",
    "CardRef",
    "FieldRef",
    "FieldsetRef",
    "FormRef",
    "ModalRef",
    "TabsRef",
]


def _normalize_sections(items: object) -> list[dict[str, str]]:
    """Coerce a sections list to the canonical [{id, label}, ...] shape."""
    if not isinstance(items, list):
        return []
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sid = item.get("id")
        label = item.get("label")
        out.append(
            {
                "id": "" if sid is None else str(sid),
                "label": "" if label is None else str(label),
            },
        )
    return out


def _normalize_open(ids: object) -> list[str]:
    if not isinstance(ids, list):
        return []
    return [str(x) for x in ids if x is not None]


class AccordionRef(DictCollectionRef):
    """Stack of collapsible sections, each body the child at the section's id.

    The tab owns open state, the server owns the section list.
    """

    _wire_type = "Accordion"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        sections: list[dict[str, str]] | None = None,
        open: list[str] | None = None,
        multi: bool = True,
    ) -> Self:
        return super().slot(
            item,
            sections=_normalize_sections(sections or []),
            open=_normalize_open(open or []),
            multi=bool(multi),
        )

    def set_sections(self, items: ListArg[dict[str, str]]) -> Nu:
        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(self, Dict.of(sections=value))

    def set_open(self, ids: ListArg[str]) -> Nu:
        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(self, Dict.of(open=value))

    def on_change(self) -> Changed:
        return Changed(self)


class _SetSectionStr(Send):
    """Send a string to a container's chrome, under an op named at construction.

    One class serves the three card chrome ops ("set_title", "set_subtitle",
    "set_caption"): the op rides in the payload and the frame ships under it.
    The frame carries the chain like every other send, so a Card nobody booted
    (a nested Section, a nuspace cell) comes into being and then takes it.
    """

    def __init__(self, ref: Ref, op: str, value: Arg[Any]) -> None:
        super().__init__(ref, value)
        self._payload["op"] = op

    def _frame_op(self) -> object:
        return self._payload["op"]

    def _frame_payload(self, values: list[object]) -> object:
        return values[0]


CardVariant = Literal["default", "elevated", "sunken", "outline"]
CardSize = Literal["sm", "md", "lg"]


class CardRef(DictCollectionRef):
    """Card-styled container: media, a header with actions, the body, a footer.

    Three child keys are the card's own places, not body: ``media`` draws
    full-bleed on top (an image), ``actions`` on the header's right rail (a
    badge, an icon button, a Row of them) and ``footer`` along the bottom
    edge (a button, a Row of them). ``card.media``, ``card.actions`` and
    ``card.footer`` answer with those children; declare them as slots with
    those names on a Shape, or build under them with ``parent_ref=``. The
    footer is pinned to the bottom, so a Grid row of cards lines its footers
    up whatever each body holds. Every other child is the body.

    ``caption`` (``set_caption``) is a quiet line of text along the bottom,
    drawn under a footer child when there is one.

    ``variant`` is the surface, ``size`` the pad (12 / 16 / 24 px). With
    ``href`` the whole card is one link with a hover border; it should then
    hold no controls of its own, since a button inside a link is two targets.
    """

    _wire_type = "Card"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        title: str = "",
        subtitle: str = "",
        caption: str = "",
        variant: CardVariant = "default",
        size: CardSize = "md",
        href: str = "",
        target: Target = "_self",
    ) -> Self:
        return super().slot(
            item,
            title=title,
            subtitle=subtitle,
            caption=caption,
            variant=variant,
            size=size,
            href=href,
            target=target,
        )

    @property
    def media(self) -> Ref:
        """The full-bleed top: the Shape's ``media`` slot, or a Column there."""
        return media_ref(self)

    @property
    def actions(self) -> Ref:
        """The header's right rail: the Shape's ``actions`` slot, or a Row there."""
        return actions_ref(self)

    @property
    def footer(self) -> Ref:
        """The bottom edge: the Shape's ``footer`` slot, or a Row there."""
        return footer_ref(self)

    def set_title(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_title", text)

    def set_subtitle(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_subtitle", text)

    def set_caption(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_caption", text)

    def set_variant(self, name: CardVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_href(self, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
        """Point the card somewhere; an empty url makes it a plain card again."""
        return _set_href(self, url, target)


Padding = Literal["none", "sm", "md", "lg"]
Border = Literal["none", "hairline", "card"]
Background = Literal["none", "muted", "sunken", "accent", "brand"]
Shadow = Literal["none", "sm", "md"]
Gap = Literal["none", "sm", "md", "lg"]


# Backs the ``Box`` Shape and draws as the browser's "Box" node.
# It cannot be called CollectionRef: that name is the base every container
# Ref subclasses, so the Ref behind this one box is BoxRef.
class BoxRef(DictCollectionRef):
    """Styled card-like box with an optional title. Pin chrome on slot().

    ``background`` is the ground: ``muted`` the hover wash, ``sunken`` a well,
    ``accent`` the Starlight wash (a callout) and ``brand`` the Afterglow soft
    fill (a highlighted plan); the tinted two bring their own border tint.
    """

    _wire_type = "Box"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        title: str = "",
        padding: Padding = "md",
        border: Border = "hairline",
        background: Background = "none",
        shadow: Shadow = "none",
        gap: Gap = "md",
    ) -> Self:
        return super().slot(
            item,
            title=title,
            padding=padding,
            border=border,
            background=background,
            shadow=shadow,
            gap=gap,
        )

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))


class FieldRef(ShapeCollectionRef):
    """Label + one child input + help / error text."""

    _wire_type = "Field"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        help: str = "",
        error: str = "",
        required: bool = False,
    ) -> Self:
        return super().slot(label=label, help=help, error=error, required=bool(required))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_help(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(help=text))

    def set_error(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(error=text))

    def set_required(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(required=flag))


FieldsetGap = Literal["sm", "md", "lg"]


class FieldsetRef(DictCollectionRef):
    """Grouped fields with a legend. Display-only, server-owned."""

    _wire_type = "Fieldset"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        legend: str = "",
        gap: FieldsetGap = "md",
        disabled: bool = False,
    ) -> Self:
        return super().slot(item, legend=legend, gap=gap, disabled=bool(disabled))

    def set_legend(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(legend=text))

    def set_gap(self, value: FieldsetGap | StrArg) -> Nu:
        return Write(self, Dict.of(gap=value))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))


class FormRef(DictCollectionRef):
    """Semantic form wrapper. Pin chrome on slot(); submit lives on a child ButtonRef."""

    _wire_type = "Form"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        title: str = "",
        gap: int = 4,
        padding: int = 0,
        align: Align = "stretch",
    ) -> Self:
        return super().slot(item, title=title, gap=int(gap), padding=int(padding), align=align)

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))


class ModalRef(DictCollectionRef):
    """Dialog overlay. Open vs closed is the thing it carries, so it has a `set()`."""

    _wire_type = "Modal"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        open: bool = False,
        title: str = "",
        dismissible: bool = True,
    ) -> Self:
        return super().slot(item, open=bool(open), title=title, dismissible=bool(dismissible))

    def set_open(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        payload: dict[str, object] = {}
        if open is not UNSET:
            payload["open"] = open
        if title is not UNSET:
            payload["title"] = title
        return Write(self, Dict.of(**payload))

    def on_change(self) -> Changed:
        return Changed(self)


def _normalize_tabs(raw: object) -> list[dict[str, str]]:
    """Coerce a tabs list to the canonical [{id, label}] shape; drop entries without an id."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        rid = item.get("id")
        if rid is None:
            continue
        label = item.get("label")
        out.append({"id": str(rid), "label": "" if label is None else str(label)})
    return out


class _SetTabs(Send):
    """Replace a Tabs' strip, ``set_tabs`` on the wire. A list is normalized first."""

    def _frame_op(self) -> object:
        return "set_tabs"

    def _frame_payload(self, values: list[object]) -> object:
        value = values[0]
        return _normalize_tabs(value) if isinstance(value, list) else value


class _SetActive(Send):
    """Pick a Tabs' active tab by id, ``set_active`` on the wire. Nil is no tab."""

    def _frame_op(self) -> object:
        return "set_active"

    def _frame_payload(self, values: list[object]) -> object:
        value = values[0]
        return "" if value is None else str(value)


TabsVariant = Literal["line", "pill", "segmented"]


class TabsRef(DictCollectionRef):
    """Tab strip plus active body. A tab's body is the child at the tab's id.

    ``variant`` is the strip: ``line`` underlines the active tab across a full
    width rule, ``pill`` puts a chip behind it, ``segmented`` is one track
    with a raised thumb, for a view switch.
    """

    _wire_type = "Tabs"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        tabs: list[dict[str, str]] | None = None,
        active: str = "",
        variant: TabsVariant = "line",
    ) -> Self:
        return super().slot(item, tabs=_normalize_tabs(tabs or []), active=active, variant=variant)

    def set_tabs(self, value: ListArg[dict[str, str]]) -> Nu:
        return _SetTabs(self, value)

    def set_active(self, value: StrArg) -> Nu:
        return _SetActive(self, value)

    def set_variant(self, name: TabsVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def on_change(self) -> Changed:
        return Changed(self)
