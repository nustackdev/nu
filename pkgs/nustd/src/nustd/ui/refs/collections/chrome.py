"""Chrome containers -- Refs for the boxes that frame their children.

Card, Tabs, Modal, Accordion, Form, Fieldset and Field. Each is a
``CollectionRef``: children are open-ended, and the chrome the box carries
of its own (a Card's title, a Tabs' active tab, a Field's label) is props
seeded by ``slot()`` and driven by ``set_*``. Their layout is the four layers
of ``layout``: Card, Modal, Form and Fieldset stack a body the way a Column
does and keep the same per child maps; Field, Tabs and Accordion hold fixed
parts and take the size layer (Field its ``gap`` too), the parts carry their
own. The Shapes over them live in ``nustd.ui.shapes.chrome``.

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

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from typing_extensions import Self, Unpack

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import child_at
from nustd.ui.core.interactions import Changed, Reset, Send, Write

from ..vocab import Target
from ..vocab import set_href as _set_href
from .base import DictCollectionRef, ShapeCollectionRef
from .flow import FLOW_CHILDREN, STACK
from .layout import SIZE, ChildLayout, SizeLayout, StackLayout, choice
from .named import ACTIONS, CONTROL, FOOTER, MEDIA, actions_ref, footer_ref, media_ref


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import Arg, BoolArg, ListArg, StrArg
    from nu.lang.runtime import Runtime
    from nustd.ui.core import Ref, Section

    from .layout import Check


__all__ = [
    "AccordionRef",
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


def _admit_paired(ref: Ref, address: object, prop: str, what: str) -> None:
    """Refuse a body at an id the container's declared ``prop`` list does not name.

    A body is drawn only under an entry with its id, so a child at any other
    id would never show. Checked against the list the container was declared
    with; one left empty (filled later by ``set_tabs`` / ``set_sections``)
    has nothing to check against.
    """
    if not isinstance(address, str):
        return
    declared = (ref._payload.get("props") or {}).get(prop)
    if not isinstance(declared, list) or not declared:
        return
    ids = [e.get("id") for e in declared if isinstance(e, dict)]
    if address not in ids:
        owner = type(ref).__name__
        msg = (
            f"{owner}[{address!r}] is no {what} id, so it would never draw; {prop} lists"
            f" {ids}. Add an entry for it, or put it under one of those"
        )
        raise ValueError(msg)


class AccordionRef(DictCollectionRef):
    """Stack of collapsible sections, each body the child at the section's id.

    The tab owns open state, the server owns the section list. ``acc["id"]``
    is the body of section ``id``; an id the declared ``sections`` does not
    list is refused, since it would never draw.
    """

    _wire_type = "Accordion"
    _positions: ClassVar[bool] = False
    _layout: ClassVar[frozenset[str]] = SIZE

    def _admit(self, address: object) -> None:
        super()._admit(address)
        _admit_paired(self, address, "sections", "section")

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        sections: list[dict[str, str]] | None = None,
        open: list[str] | None = None,
        multi: bool = True,
        **layout: Unpack[SizeLayout],
    ) -> Self:
        return super().slot(
            item,
            sections=_normalize_sections(sections or []),
            open=_normalize_open(open or []),
            multi=bool(multi),
            **cls._laid_out(layout),
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


CardVariant = Literal["default", "elevated", "sunken", "outline", "plain", "accent", "brand"]
CardSize = Literal["sm", "md", "lg"]
_CARD_VARIANTS = ("default", "elevated", "sunken", "outline", "plain", "accent", "brand")
_CARD_SIZES = ("sm", "md", "lg")


class CardRef(ChildLayout, DictCollectionRef):
    """A surface: media, a header with actions, the body, a footer.

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

    Surface: ``variant`` is the look (``default``, ``elevated``, ``sunken``,
    ``outline``, ``plain`` with no border and no fill, ``accent`` and
    ``brand`` tinted washes), ``size`` a preset for the whole look (``sm``,
    ``md``, ``lg``: pad 12 / 16 / 24 and the space between header, body and
    footer). Any explicit layer prop wins over the preset. Both change at
    run time through ``set_layout`` with the layers.

    The body speaks the layers of a Column (``layout``): ``padding``
    (the size's pad), ``gap`` (3), ``justify``, ``align``, ``divided``, and
    the per child maps. ``height`` / ``max_height`` with ``scroll`` scroll
    the body; the header and footer stay put.

    With ``href`` the whole card is one link with a hover border; it should
    then hold no controls of its own, since a button inside a link is two
    targets.
    """

    _wire_type = "Card"
    _parts: ClassVar[frozenset[str]] = frozenset({MEDIA, ACTIONS, FOOTER})
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN
    _family: ClassVar[Mapping[str, Check]] = {
        "variant": choice(*_CARD_VARIANTS),
        "size": choice(*_CARD_SIZES),
    }

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        title: str = "",
        subtitle: str = "",
        caption: str = "",
        variant: CardVariant | None = None,
        size: CardSize | None = None,
        href: str = "",
        target: Target = "_self",
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            title=title,
            subtitle=subtitle,
            caption=caption,
            href=href,
            target=target,
            **cls._laid_out({**layout, "variant": variant, "size": size}),
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

    def set_href(self, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
        """Point the card somewhere; an empty url makes it a plain card again."""
        return _set_href(self, url, target)


class FieldLayout(SizeLayout, total=False):
    """A Field's layout: the size layer, and the gap between its parts."""

    gap: int


class FieldRef(ShapeCollectionRef):
    """Label + one control + help / error text.

    ``field.control`` is the control: the one slot its Shape declares, or a
    bare child at ``control`` whose kind ``.to`` names
    (``field.control.to(InputRef)``). A Field holds that one child and no
    other, so a second one is refused where it is built.
    """

    _wire_type = "Field"
    _parts: ClassVar[frozenset[str]] = frozenset({CONTROL})
    _layout: ClassVar[frozenset[str]] = SIZE | {"gap"}

    @property
    def control(self) -> Ref:
        """The one control: the Shape's slot, or a bare child at ``control``."""
        section_cls = self._payload.get("section_cls")
        slots = getattr(section_cls, "_slots", {})
        if slots:
            slot = next(iter(slots.values()))
            return slot.create_ref(owner_shape=section_cls, parent_ref=self)
        return child_at(self, CONTROL)

    def _admit(self, address: object) -> None:
        super()._admit(address)
        if not isinstance(address, str):
            return
        slots = getattr(self._payload.get("section_cls"), "_slots", {})
        place = next(iter(slots), CONTROL)
        if address != place:
            msg = (
                f"Field holds one control, at {place!r}, not {address!r}; reach it as"
                f" field.control, and put several inputs in a Row or a Column there"
            )
            raise TypeError(msg)

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        help: str = "",
        error: str = "",
        required: bool = False,
        **layout: Unpack[FieldLayout],
    ) -> Self:
        """Declare it as a slot; ``gap`` (1) spaces label, control and help."""
        return super().slot(
            label=label,
            help=help,
            error=error,
            required=bool(required),
            **cls._laid_out(layout),
        )

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_help(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(help=text))

    def set_error(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(error=text))

    def set_required(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(required=flag))


class FieldsetRef(ChildLayout, DictCollectionRef):
    """Grouped fields with a legend. Display-only, server-owned.

    The body speaks the layers of a Column (``layout``): ``padding`` (4),
    ``gap`` (4), ``justify``, ``align``, ``divided``, and the per child maps.
    """

    _wire_type = "Fieldset"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        legend: str = "",
        disabled: bool = False,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(item, legend=legend, disabled=bool(disabled), **cls._laid_out(layout))

    def set_legend(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(legend=text))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))


class FormRef(ChildLayout, DictCollectionRef):
    """A form: its inputs, sent together.

    ``on_submit()`` hears one ``{event: "submit", values, button}`` per
    submit: Enter in any single-line input inside, a click on a button
    declared ``submit=True``, or cmd/ctrl+Enter in a multi-line one. Every
    other button is a plain one, so a Cancel in a form never submits.
    ``values`` is every input under the form in one snapshot, nested the way
    the slots are and keyed by slot name, a Field standing for its control::

        {"details": {"title": "Dune", "year": 2021}, "watched": True}

    ``button`` is the slot name of the submit button that fired, or None.
    The browser checks ``required``, ``min``, ``max`` and the like before it
    sends anything. Read the payload in the reaction rather than reading each
    input again::

        nu.ReactEvery(App.add.on_submit(), lambda sub: save(sub["values"]))

    ``values()`` is the same snapshot as a read, any time. ``reset()`` puts
    every input back to the value its slot declared, and ``clear_on_submit``
    does that after each submit. ``busy_on_submit`` marks the form busy as it
    sends: further submits are dropped and the submit buttons spin until
    ``set_busy(False)``.

    The body speaks the layers of a Column (``layout``): ``padding`` (0),
    ``gap`` (4), ``justify``, ``align`` (stretch), ``divided``, and the per
    child maps.
    """

    _wire_type = "Form"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        title: str = "",
        clear_on_submit: bool = False,
        busy_on_submit: bool = False,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            title=title,
            clear_on_submit=bool(clear_on_submit),
            busy_on_submit=bool(busy_on_submit),
            **cls._laid_out(layout),
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def on_submit(self) -> Changed:
        """Each submit, its payload ``{event: "submit", values, button}``."""
        return Changed(self, "submit")

    def values(self) -> Dict:
        """Every input under the form, nested by slot name, in one read."""
        return Dict(self)

    def reset(self) -> Nu:
        """Put every input in the form back to the value its slot declared."""
        return Reset(self)

    def set_busy(self, flag: BoolArg) -> Nu:
        """Busy drops submits and spins the submit buttons; ``busy_on_submit`` sets it."""
        return Write(self, Dict.of(busy=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))


class ModalRef(ChildLayout, DictCollectionRef):
    """Dialog overlay. Open vs closed is the thing it carries, so it has a `set()`.

    The dialog is ``width`` wide (512px unless set; a page width name reads,
    ``width="prose"``) and never grows past the window: a tall body scrolls
    inside it, the title stays put. The body speaks the layers of a Column
    (``layout``): ``gap`` (4), ``padding``, ``justify``, ``align``,
    ``divided``, and the per child maps.
    """

    _wire_type = "Modal"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        open: bool = False,
        title: str = "",
        dismissible: bool = True,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            open=bool(open),
            title=title,
            dismissible=bool(dismissible),
            **cls._laid_out(layout),
        )

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
_TABS_VARIANTS = ("line", "pill", "segmented")


class TabsRef(DictCollectionRef):
    """Tab strip plus active body. A tab's body is the child at the tab's id.

    ``tabs["id"]`` is the body of tab ``id``; an id the declared ``tabs``
    does not list is refused, since it would never draw.

    ``variant`` is the strip: ``line`` underlines the active tab across a full
    width rule, ``pill`` puts a chip behind it, ``segmented`` is one track
    with a raised thumb, for a view switch; ``set_layout(variant=)`` changes
    it at run time.
    """

    _wire_type = "Tabs"
    _positions: ClassVar[bool] = False
    _layout: ClassVar[frozenset[str]] = SIZE
    _family: ClassVar[Mapping[str, Check]] = {"variant": choice(*_TABS_VARIANTS)}

    def _admit(self, address: object) -> None:
        super()._admit(address)
        _admit_paired(self, address, "tabs", "tab")

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        tabs: list[dict[str, str]] | None = None,
        active: str = "",
        variant: TabsVariant = "line",
        **layout: Unpack[SizeLayout],
    ) -> Self:
        return super().slot(
            item,
            tabs=_normalize_tabs(tabs or []),
            active=active,
            **cls._laid_out({**layout, "variant": variant}),
        )

    def set_tabs(self, value: ListArg[dict[str, str]]) -> Nu:
        return _SetTabs(self, value)

    def set_active(self, value: StrArg) -> Nu:
        return _SetActive(self, value)

    def on_change(self) -> Changed:
        return Changed(self)
