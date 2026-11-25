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

from nu.lang.sentinels import UNSET
from nustd.ui.core import child_at
from nustd.ui.core.interactions import Changed, Reset, Send, Write

from ..vocab import Target
from ..vocab import set_href as _set_href
from .base import DictCollectionRef, ShapeCollectionRef
from .flow import FLOW_CHILDREN, STACK, RowRef
from .layout import SIZE, ChildLayout, SizeLayout, StackLayout, choice, px
from .named import (
    ACTIONS,
    CONTROL,
    FOOTER,
    HEADER,
    MEDIA,
    actions_ref,
    footer_ref,
    header_ref,
    media_ref,
    part_ref,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.domains.shape import Slot
    from nu.forms import Dict
    from nu.lang import Nu
    from nu.lang.args import Arg, BoolArg, ListArg, StrArg
    from nu.lang.runtime import Runtime
    from nustd.ui.core import ItemRef, Ref, Section

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


# An Accordion section's header child sits at this prefix plus the section id.
_SECTION_HEADER = f"{HEADER}:"


def _normalize_sections(items: object) -> list[dict[str, str]]:
    """Coerce a sections list to the canonical [{id, label}, ...] shape.

    An id under the header prefix is refused: its body would sit at the key
    of another section's header.
    """
    if not isinstance(items, list):
        return []
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sid = item.get("id")
        label = item.get("label")
        sid = "" if sid is None else str(sid)
        if sid.startswith(_SECTION_HEADER):
            msg = (
                f"AccordionRef section id {sid!r} starts with {_SECTION_HEADER!r}, the key"
                f" a section's header takes; pick another id"
            )
            raise ValueError(msg)
        out.append({"id": sid, "label": "" if label is None else str(label)})
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
    declared = (ref._props or {}).get(prop)
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

    A section's ``label`` is shorthand for a header that is one line of
    text. ``acc.header("id")`` is a Row at ``header:id`` that takes its place
    in the trigger row when it exists, for a header with a badge or a button
    in it. A click on the row's text or empty space toggles the section; a
    control in the header does its own thing. Like a body, a header for an id
    the declared ``sections`` does not list is refused, and no section id
    may start with ``header:``.
    """

    _wire_type = "Accordion"
    _positions: ClassVar[bool] = False
    _layout: ClassVar[frozenset[str]] = SIZE

    def _admit(self, address: object) -> None:
        super()._admit(address)
        if isinstance(address, str) and address.startswith(_SECTION_HEADER):
            address = address[len(_SECTION_HEADER) :]
        _admit_paired(self, address, "sections", "section")

    def _child(self, key: object) -> ItemRef:
        if isinstance(key, str) and key.startswith(_SECTION_HEADER):
            sid = key[len(_SECTION_HEADER) :]
            msg = (
                f"{self._owner_name()}[{key!r}] is a section's header; reach it as .header({sid!r})"
            )
            raise ValueError(msg)
        return super()._child(key)

    def header(self, section_id: str, **row_props: object) -> Ref:
        """The header of section ``section_id``: a Row at ``header:<id>``, drawn in place of its label."""
        return part_ref(
            self, f"{_SECTION_HEADER}{section_id}", RowRef.slot(**{"gap": 2, **row_props})
        )

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
        from nu.forms import Dict

        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(self, Dict.of(sections=value))

    def set_open(self, ids: ListArg[str]) -> Nu:
        from nu.forms import Dict

        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(self, Dict.of(open=value))

    def on_change(self) -> Changed:
        return Changed(self)


class _SetSectionStr(Send):
    """Send a string to a container's chrome; each subclass ships its own op.

    One subclass per card chrome op ("set_title", "set_subtitle",
    "set_caption"): which string it sets is the kind of the node, so it is
    the class, not a field. The frame carries the chain like every other
    send, so a Card nobody booted (a nested Section, a nuspace cell) comes
    into being and then takes it.
    """

    _op: ClassVar[str] = ""

    def _frame_op(self) -> object:
        return self._op

    def _frame_payload(self, values: list[object]) -> object:
        return values[0]


class _SetTitle(_SetSectionStr):
    """A container's title, ``set_title`` on the wire."""

    _op = "set_title"


class _SetSubtitle(_SetSectionStr):
    """A container's subtitle, ``set_subtitle`` on the wire."""

    _op = "set_subtitle"


class _SetCaption(_SetSectionStr):
    """A container's caption, ``set_caption`` on the wire."""

    _op = "set_caption"


CardVariant = Literal["default", "elevated", "sunken", "outline", "plain", "accent", "brand"]
CardSize = Literal["sm", "md", "lg"]
_CARD_VARIANTS = ("default", "elevated", "sunken", "outline", "plain", "accent", "brand")
_CARD_SIZES = ("sm", "md", "lg")


class CardRef(ChildLayout, DictCollectionRef):
    """A surface: media, a header with actions, the body, a footer.

    Four child keys are the card's own places, not body: ``media`` draws
    full-bleed on top (an image), ``header`` as the header line in place of
    ``title`` and ``subtitle`` (a Row of an avatar, a name and a badge),
    ``actions`` on the header's right rail (a badge, an icon button, a Row
    of them) and ``footer`` along the bottom edge (a button, a Row of them).
    ``card.media``, ``card.header``, ``card.actions`` and ``card.footer``
    answer with those children; declare them as slots with those names on a
    Shape, or build under them with ``parent_ref=``. The strings stay the
    shorthand for a plain heading; a header child is for anything more. The
    card only places it, full width beside the actions and free to shrink, so
    a ``TextRef(lines=1)`` in it cuts with an ellipsis. The footer is pinned
    to the bottom, so a Grid row of cards lines its footers up whatever each
    body holds. Every other child is the body.

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
    _parts: ClassVar[frozenset[str]] = frozenset({MEDIA, HEADER, ACTIONS, FOOTER})
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
    def header(self) -> Ref:
        """The header line, in place of the title: the Shape's ``header`` slot, or a Row there."""
        return header_ref(self)

    @property
    def actions(self) -> Ref:
        """The header's right rail: the Shape's ``actions`` slot, or a Row there."""
        return actions_ref(self)

    @property
    def footer(self) -> Ref:
        """The bottom edge: the Shape's ``footer`` slot, or a Row there."""
        return footer_ref(self)

    def set_title(self, text: StrArg) -> Nu:
        return _SetTitle(self, text)

    def set_subtitle(self, text: StrArg) -> Nu:
        return _SetSubtitle(self, text)

    def set_caption(self, text: StrArg) -> Nu:
        return _SetCaption(self, text)

    def set_href(self, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
        """Point the card somewhere; an empty url makes it a plain card again."""
        return _set_href(self, url, target)


class FieldLayout(SizeLayout, total=False):
    """A Field's layout: the size layer, and the gap between its parts."""

    gap: int


class FieldRef(ShapeCollectionRef):
    """Label + one control + help / error text, and actions at the label's end.

    ``field.control`` is the control: the one slot its Shape declares besides
    ``actions``, or a bare child at ``control`` whose kind ``.to`` names
    (``field.control.to(InputRef)``). A Field holds that one control and no
    other, so a second one is refused where it is built.

    ``field.actions`` is the end of the label row, for small controls about
    the field rather than its value: an icon button, a Popover of settings
    (``field.actions.to(PopoverRef.slot(icon="settings-2"))``). The Shape's
    ``actions`` slot, or a Row there. It sits outside the field's wiring: an
    input in it is never the field's control nor named by its label.

    ``inline=True`` draws it as one row, inspector style: the label in a left
    column ``label_width`` px wide (80 unless set), the control, then the
    actions, help and error under the control. Stacked inline fields line up
    into two columns, the dense look of a settings panel.
    """

    _wire_type = "Field"
    _parts: ClassVar[frozenset[str]] = frozenset({CONTROL, ACTIONS})
    _layout: ClassVar[frozenset[str]] = SIZE | {"gap"}

    def _control_slot(self) -> tuple[str, Any] | None:
        """The Shape's control slot by name, the first that is not ``actions``."""
        slots = getattr(self._section_cls, "_slots", {})
        return next(((k, v) for k, v in slots.items() if k != ACTIONS), None)

    @property
    def control(self) -> Ref:
        """The one control: the Shape's slot, or a bare child at ``control``."""
        found = self._control_slot()
        if found is not None:
            return found[1].create_ref(owner_shape=self._section_cls, parent_ref=self)
        return child_at(self, CONTROL)

    @property
    def actions(self) -> Ref:
        """The label row's end: the Shape's ``actions`` slot, or a Row there."""
        return actions_ref(self, gap=1)

    def _admit(self, address: object) -> None:
        super()._admit(address)
        if not isinstance(address, str) or address == ACTIONS:
            return
        found = self._control_slot()
        place = CONTROL if found is None else found[0]
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
        inline: bool = False,
        label_width: int | None = None,
        **layout: Unpack[FieldLayout],
    ) -> Self:
        """Declare it as a slot; ``gap`` (1) spaces label, control and help."""
        props: dict[str, object] = {}
        if inline:
            props["inline"] = True
        if label_width is not None:
            props["label_width"] = px("FieldRef", "label_width", label_width)
        return super().slot(
            label=label,
            help=help,
            error=error,
            required=bool(required),
            **props,
            **cls._laid_out(layout),
        )

    def set_label(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(label=text))

    def set_help(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(help=text))

    def set_error(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(error=text))

    def set_required(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(required=flag))


class FieldsetRef(ChildLayout, DictCollectionRef):
    """Grouped fields with a legend. Display-only, server-owned.

    ``disabled`` disables every input and button inside, and a Form's checks
    skip them.

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
        from nu.forms import Dict

        return Write(self, Dict.of(legend=text))

    def set_disabled(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(disabled=flag))


class FormRef(ChildLayout, DictCollectionRef):
    """A form: its inputs, sent together.

    ``on_submit()`` hears one ``{event: "submit", values, button}`` per
    submit: Enter in any single-line input inside, a click on a button
    declared ``submit=True``, or shift+Enter in a multi-line one (a
    ``TextAreaRef``, or a ``CodeRef`` or ``MarkdownRef`` with
    ``readonly=False``), where plain Enter stays a newline. A key that
    submits the form fires the input's own ``on_submit()`` first, then the
    form's. Every other button is a plain one, so a Cancel in a form never
    submits.
    ``values`` is every input under the form in one snapshot, nested the way
    the slots are and keyed by slot name, a Field standing for its control::

        {"details": {"title": "Dune", "year": 2021}, "watched": True}

    ``button`` is the slot name of the submit button that fired, or None.
    Read the payload in the reaction rather than reading each input again::

        nu.ReactEvery(App.add.on_submit(), lambda sub: save(sub["values"]))

    The browser checks every input before it sends anything: ``required``,
    ``min``, ``max``, ``max_length``, ``pattern`` and the ``email`` format.
    A failing input's Field (or the input, when it has none) shows why, the
    first one takes focus, and no submit goes out. The program's own verdict
    goes the same way: ``set_errors({"title": "Already in the list"})``,
    keyed like ``values`` (nested by slot name, a Field standing for its
    control), puts each message on its input's Field, clears every input it
    does not name, and focuses the first one named; ``set_errors({})``
    clears them all.

    ``values()`` is the same snapshot as a read, any time. ``reset()`` puts
    every input back to the value its slot declared, and ``clear_on_submit``
    does that after each submit. ``busy_on_submit`` marks the form busy as it
    sends: further submits are dropped and the submit buttons spin until
    ``set_busy(False)``. ``disabled`` disables every input and button in the
    form and drops its submits.

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
        disabled: bool = False,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            title=title,
            clear_on_submit=bool(clear_on_submit),
            busy_on_submit=bool(busy_on_submit),
            disabled=bool(disabled),
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
        from nu.forms import Dict

        return Dict(self)

    def reset(self) -> Nu:
        """Put every input in the form back to the value its slot declared."""
        return Reset(self)

    def set_busy(self, flag: BoolArg) -> Nu:
        """Busy drops submits and spins the submit buttons; ``busy_on_submit`` sets it."""
        from nu.forms import Dict

        return Write(self, Dict.of(busy=flag))

    def set_title(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(title=text))

    def set_disabled(self, flag: BoolArg) -> Nu:
        """Disable every input and button in the form, and drop its submits."""
        from nu.forms import Dict

        return Write(self, Dict.of(disabled=flag))

    def set_errors(self, errors: Arg[Any]) -> Nu:
        """Show the program's errors on the form's inputs, keyed like ``values``.

        Each message lands on its input's Field (or on the input), every input
        not named is cleared, and the first one named takes focus.
        ``set_errors({})`` clears them all.
        """
        return _SetErrors(self, errors)


class _SetErrors(Send):
    """A Form's errors by slot name, ``set_errors`` on the wire."""

    def _frame_op(self) -> object:
        return "set_errors"

    def _frame_payload(self, values: list[object]) -> object:
        return values[0]


class ModalRef(ChildLayout, DictCollectionRef):
    """Dialog overlay. Open vs closed is the thing it carries, so it has a `set()`.

    ``title`` heads the dialog. For more than a string (an icon, a name and
    a badge), build a ``header`` child: ``modal.header`` is the Shape's
    ``header`` slot or a Row there, drawn in the title's place with the close
    button kept beside it, and the dialog is named by its text. The modal
    only places it, full width and free to shrink. Every other child is the
    body.

    The dialog is ``width`` wide (512px unless set; a page width name reads,
    ``width="prose"``) and never grows past the window: a tall body scrolls
    inside it, the title stays put. The body speaks the layers of a Column
    (``layout``): ``gap`` (4), ``padding``, ``justify``, ``align``,
    ``divided``, and the per child maps.
    """

    _wire_type = "Modal"
    _parts: ClassVar[frozenset[str]] = frozenset({HEADER})
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

    @property
    def header(self) -> Ref:
        """The header line, in place of the title: the Shape's ``header`` slot, or a Row there."""
        return header_ref(self)

    def set_open(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        from nu.forms import Dict

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
