"""Layout Sections -- Shape-based containers that wrap other Refs.

Most of these are `Section` subclasses (not Refs) -- Shape-based
composition primitives that mount other Refs and Sections. Section
and SectionRef come from ``nu.ui.core``; this module defines the
concrete layout primitives (Row, Column, Card, Tabs, Modal, Field,
Fieldset, Form, Accordion) that build on them, plus the chrome
interactions those primitives expose.

The chrome commands (`_SetSectionStr`, `_SetTabs`, `_SetActive`) target
the abstract ``Session`` from core -- so this module is host-agnostic;
any host that implements ``Session`` runs it. Chrome that writes to the
section itself (a Card's title, a Tabs' active tab) lives on a SectionRef
subclass, so it is driven off the bound Ref -- ``page.card.set_title(...)``
-- and the address comes from that Ref's chain. There is no way to drive a
section off its class: a class has no mount point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.engine.structure import Declared
from nu.forms import Dict
from nu.lang import Command
from nu.lang.sentinels import UNSET
from nu.ui.core import Frame, Ref, Section, SectionRef, Session
from nu.ui.core.interactions import Changed, Write


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.args import Arg, BoolArg, ListArg, StrArg
    from nu.lang.runtime import Runtime


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


class AccordionRef(SectionRef):
    """SectionRef backing an Accordion slot. Carries the section-list chrome."""

    _wire_type = "Accordion"

    def set_sections(self, items: ListArg[dict[str, str]]) -> Nu:
        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(self, Dict.of(sections=value))

    def set_open(self, ids: ListArg[str]) -> Nu:
        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(self, Dict.of(open=value))

    def on_change(self) -> Changed:
        return Changed(self)


class Accordion(Section):
    """Stack of collapsible sections. Tab owns open state, server owns the section list."""

    _ref_cls = AccordionRef
    _wire_type = "Accordion"

    @classmethod
    def slot(
        cls,
        *,
        sections: list[dict[str, str]] | None = None,
        open: list[str] | None = None,
        multi: bool = True,
    ) -> Self:
        return super().slot(
            sections=_normalize_sections(sections or []),
            open=_normalize_open(open or []),
            multi=bool(multi),
        )


class _SetSectionStr(Command):
    """Send a string-payload Frame to a Section by mount path.

    Slot 0 holds the section's own bound SectionRef so this is a well-formed
    ``mutates={0}`` Command; the wire op is supplied at construction (e.g.
    "set_title") so one class serves all three card chrome ops.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: Ref, op: str, value: Arg[Any]) -> None:
        super().__init__(ref, value)
        self._payload["op"] = op

    @property
    def _op(self) -> str:
        return self._payload["op"]  # type: ignore[return-value]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            await session.send(Frame(self._op, ref=path, payload=value))

        return athunk


class CardRef(SectionRef):
    """SectionRef backing a Card slot. Carries the card's header/footer chrome."""

    _wire_type = "Card"

    def set_title(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_title", text)

    def set_subtitle(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_subtitle", text)

    def set_footer(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_footer", text)


class Card(Section):
    """Card-styled Section: title + subtitle + body slots + footer."""

    _ref_cls = CardRef
    _wire_type = "Card"

    @classmethod
    def slot(cls, *, title: str = "", subtitle: str = "", footer: str = "") -> Self:
        return super().slot(title=title, subtitle=subtitle, footer=footer)


Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around"]


class Column(Section):
    """Vertical flex layout. Pin chrome on the slot()."""

    _wire_type = "Column"

    @classmethod
    def slot(
        cls,
        *,
        gap: int = 4,
        align: Align = "stretch",
        justify: Justify = "start",
        padding: int = 0,
    ) -> Self:
        return super().slot(gap=gap, align=align, justify=justify, padding=padding)


Padding = Literal["none", "sm", "md", "lg"]
Border = Literal["none", "hairline", "card"]
Background = Literal["none", "muted", "accent"]
Shadow = Literal["none", "sm", "md"]
Gap = Literal["none", "sm", "md", "lg"]


class Container(Section):
    """Styled card-like box. Pin chrome on slot()."""

    _wire_type = "Container"

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        padding: Padding = "md",
        border: Border = "hairline",
        background: Background = "none",
        shadow: Shadow = "none",
        gap: Gap = "md",
    ) -> Self:
        return super().slot(
            title=title,
            padding=padding,
            border=border,
            background=background,
            shadow=shadow,
            gap=gap,
        )


class FieldRef(SectionRef):
    """SectionRef backing a Field slot. Carries the label / help / error chrome."""

    _wire_type = "Field"

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_help(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(help=text))

    def set_error(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(error=text))

    def set_required(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(required=flag))


class Field(Section):
    """Label + child input + help / error text. Exactly one child slot."""

    _ref_cls = FieldRef
    _wire_type = "Field"

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        slot_count = len(getattr(cls, "_slots", {}))
        if slot_count != 1:
            raise RuntimeError(
                f"Field {cls.__name__} declares {slot_count} child slots; "
                "Field requires exactly one.",
            )

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        help: str = "",
        error: str = "",
        required: bool = False,
    ) -> Self:
        return super().slot(label=label, help=help, error=error, required=required)


FieldsetGap = Literal["sm", "md", "lg"]


class FieldsetRef(SectionRef):
    """SectionRef backing a Fieldset slot. Carries the legend / gap / disabled chrome."""

    _wire_type = "Fieldset"

    def set_legend(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(legend=text))

    def set_gap(self, value: FieldsetGap | StrArg) -> Nu:
        return Write(self, Dict.of(gap=value))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))


class Fieldset(Section):
    """Grouped fields with a legend. Display-only, server-owned."""

    _ref_cls = FieldsetRef
    _wire_type = "Fieldset"

    @classmethod
    def slot(
        cls,
        *,
        legend: str = "",
        gap: FieldsetGap = "md",
        disabled: bool = False,
    ) -> Self:
        return super().slot(legend=legend, gap=gap, disabled=disabled)


class Form(Section):
    """Semantic form wrapper. Pin chrome on slot(); submit lives on a child ButtonRef."""

    _wire_type = "Form"

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        gap: int = 4,
        padding: int = 0,
        align: Align = "stretch",
    ) -> Self:
        return super().slot(title=title, gap=gap, padding=padding, align=align)


class ModalRef(SectionRef):
    """SectionRef backing a Modal slot. Carries Modal-only interaction methods."""

    _wire_type = "Modal"

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


class Modal(Section):
    """Dialog overlay. Pin chrome on slot(); declare body Refs as slots."""

    _ref_cls = ModalRef
    _wire_type = "Modal"

    @classmethod
    def slot(
        cls,
        *,
        open: bool = False,
        title: str = "",
        dismissible: bool = True,
    ) -> Self:
        return super().slot(open=open, title=title, dismissible=dismissible)


RowAlign = Literal["start", "center", "end", "stretch", "baseline"]
RowJustify = Literal["start", "center", "end", "between", "around", "evenly"]


class Row(Section):
    """Horizontal flex layout. Pin chrome on slot()."""

    _wire_type = "Row"

    @classmethod
    def slot(
        cls,
        *,
        gap: int = 4,
        align: RowAlign = "center",
        justify: RowJustify = "start",
        wrap: bool = False,
        padding: int = 0,
    ) -> Self:
        return super().slot(gap=gap, align=align, justify=justify, wrap=wrap, padding=padding)


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


class _SetTabs(Command):
    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: Ref, value: Arg[Any]) -> None:
        super().__init__(ref, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            if isinstance(value, list):
                value = _normalize_tabs(value)
            await session.send(Frame("set_tabs", ref=path, payload=value))

        return athunk


class _SetActive(Command):
    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: Ref, value: Arg[Any]) -> None:
        super().__init__(ref, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            payload = "" if value is None else str(value)
            await session.send(Frame("set_active", ref=path, payload=payload))

        return athunk


class TabsRef(SectionRef):
    """SectionRef backing a Tabs slot. Carries the strip + active-tab chrome."""

    _wire_type = "Tabs"

    def set_tabs(self, value: ListArg[dict[str, str]]) -> Nu:
        return _SetTabs(self, value)

    def set_active(self, value: StrArg) -> Nu:
        return _SetActive(self, value)

    def on_change(self) -> Changed:
        return Changed(self)


class Tabs(Section):
    """Tab strip plus active body. Subclass and declare one child slot per tab body."""

    _ref_cls = TabsRef
    _wire_type = "Tabs"

    @classmethod
    def slot(
        cls,
        *,
        tabs: list[dict[str, str]] | None = None,
        active: str = "",
    ) -> Self:
        return super().slot(tabs=_normalize_tabs(tabs or []), active=active)


__all__ = [
    "Accordion",
    "AccordionRef",
    "Card",
    "CardRef",
    "Column",
    "Container",
    "Field",
    "FieldRef",
    "Fieldset",
    "FieldsetRef",
    "Form",
    "Modal",
    "ModalRef",
    "Row",
    "Tabs",
    "TabsRef",
]
