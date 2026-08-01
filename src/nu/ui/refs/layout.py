"""Layout Sections -- Shape-based containers that wrap other Refs.

Most of these are `Section` subclasses (not Refs) -- Shape-based
composition primitives that mount other Refs and Sections. Section
and SectionRef come from ``nu.ui.core``; this module defines the
concrete layout primitives (Row, Column, Card, Tabs, Modal, Field,
Fieldset, Form, Accordion) that build on them, plus the chrome
interactions those primitives expose.

The chrome commands (`_SetSectionStr`, `_SetTabs`, `_SetActive`) target
the abstract ``Session`` from core -- so this module is host-agnostic;
any host that implements ``Session`` runs it. Address resolution for
section-scoped chrome writes goes through ``_SectionMountRef``, which
asks the section's own ``_wire_prefix()`` classmethod (stamped by the
host, e.g. nudle's Page) for its wire path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Self

from nu import DictForm
from nu.domains.shape import Slot
from nu.engine.structure import Declared
from nu.lang import Command
from nu.lang.sentinels import UNSET
from nu.ui.core import Frame, Ref, Section, SectionRef, Session
from nu.ui.core.interactions import Changed, Write


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.args import Arg, BoolArg, ListArg, StrArg
    from nu.lang.runtime import Runtime


class _SectionMountRef(Ref):
    """Ref that resolves to a Section's mount path directly (no segment walk).

    Used by Section subclasses whose chrome interactions (title, tabs, ...)
    target the section's OWN wire path rather than a child slot. Reads
    ``_wire_prefix()`` classmethod stamped by the host onto the section
    subclass at mount registration time.
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def _aresolve_address(self, rt: Runtime, nid: int) -> str:
        section_cls = self._payload["section_cls"]
        prefix = getattr(section_cls, "_wire_prefix", None)
        if prefix is None:
            raise RuntimeError(
                f"Section {section_cls.__name__} has no mount point. "
                "Declare it as a Slot on a Page before driving it.",
            )
        return ".".join(prefix())


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


class AccordionRef(Section):
    """Stack of collapsible sections. Tab owns open state, server owns the section list."""

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

    @classmethod
    def _mount_ref(cls) -> _SectionMountRef:
        return _SectionMountRef(section_cls=cls)

    @classmethod
    def set_sections(cls, items: ListArg[dict[str, str]]) -> Nu:
        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(cls._mount_ref(), DictForm.of(sections=value))

    @classmethod
    def set_open(cls, ids: ListArg[str]) -> Nu:
        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(cls._mount_ref(), DictForm.of(open=value))

    @classmethod
    def changed(cls) -> Changed:
        return Changed(cls._mount_ref())


class _SetSectionStr(Command):
    """Send a string-payload Frame to a Section by mount path.

    Slot 0 holds a mount Ref (``_SectionMountRef``) so this is a well-formed
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


class CardRef(Section):
    """Card-styled Section: title + subtitle + body slots + footer."""

    @classmethod
    def slot(cls, *, title: str = "", subtitle: str = "", footer: str = "") -> Self:
        return super().slot(title=title, subtitle=subtitle, footer=footer)

    @classmethod
    def _mount_ref(cls) -> _SectionMountRef:
        return _SectionMountRef(section_cls=cls)

    @classmethod
    def set_title(cls, text: StrArg) -> Nu:
        return _SetSectionStr(cls._mount_ref(), "set_title", text)

    @classmethod
    def set_subtitle(cls, text: StrArg) -> Nu:
        return _SetSectionStr(cls._mount_ref(), "set_subtitle", text)

    @classmethod
    def set_footer(cls, text: StrArg) -> Nu:
        return _SetSectionStr(cls._mount_ref(), "set_footer", text)


Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around"]


class Column(Section):
    """Vertical flex layout. Pin chrome on the slot()."""

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


class FieldRef(Section):
    """Label + child input + help / error text. Exactly one child slot."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        slot_count = len(getattr(cls, "_slots", {}))
        if slot_count != 1:
            raise RuntimeError(
                f"FieldRef {cls.__name__} declares {slot_count} child slots; "
                "FieldRef requires exactly one.",
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

    @classmethod
    def _mount_ref(cls) -> _SectionMountRef:
        return _SectionMountRef(section_cls=cls)

    @classmethod
    def set_label(cls, text: StrArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(label=text))

    @classmethod
    def set_help(cls, text: StrArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(help=text))

    @classmethod
    def set_error(cls, text: StrArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(error=text))

    @classmethod
    def set_required(cls, flag: BoolArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(required=flag))


FieldsetGap = Literal["sm", "md", "lg"]


class Fieldset(Section):
    """Grouped fields with a legend. Display-only, server-owned."""

    @classmethod
    def slot(
        cls,
        *,
        legend: str = "",
        gap: FieldsetGap = "md",
        disabled: bool = False,
    ) -> Self:
        return super().slot(legend=legend, gap=gap, disabled=disabled)

    @classmethod
    def _mount_ref(cls) -> _SectionMountRef:
        return _SectionMountRef(section_cls=cls)

    @classmethod
    def set_legend(cls, text: StrArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(legend=text))

    @classmethod
    def set_gap(cls, value: FieldsetGap | StrArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(gap=value))

    @classmethod
    def set_disabled(cls, flag: BoolArg) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(disabled=flag))


class Form(Section):
    """Semantic form wrapper. Pin chrome on slot(); submit lives on a child ButtonRef."""

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

    def set_open(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        payload: dict[str, object] = {}
        if open is not UNSET:
            payload["open"] = open
        if title is not UNSET:
            payload["title"] = title
        return Write(self, DictForm.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


class Modal(Section):
    """Dialog overlay. Pin chrome on slot(); declare body Refs as slots."""

    @classmethod
    def slot(
        cls,
        *,
        open: bool = False,
        title: str = "",
        dismissible: bool = True,
    ) -> Self:
        return Slot(  # type: ignore[return-value]
            ModalRef,
            props={"open": open, "title": title, "dismissible": dismissible},
            section_cls=cls,
        )


RowAlign = Literal["start", "center", "end", "stretch", "baseline"]
RowJustify = Literal["start", "center", "end", "between", "around", "evenly"]


class Row(Section):
    """Horizontal flex layout. Pin chrome on slot()."""

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


class TabsRef(Section):
    """Tab strip plus active body. Subclass and declare one child slot per tab body."""

    @classmethod
    def slot(
        cls,
        *,
        tabs: list[dict[str, str]] | None = None,
        active: str = "",
    ) -> Self:
        return super().slot(tabs=_normalize_tabs(tabs or []), active=active)

    @classmethod
    def _mount_ref(cls) -> _SectionMountRef:
        return _SectionMountRef(section_cls=cls)

    @classmethod
    def set_tabs(cls, value: ListArg[dict[str, str]]) -> Nu:
        return _SetTabs(cls._mount_ref(), value)

    @classmethod
    def set_active(cls, value: StrArg) -> Nu:
        return _SetActive(cls._mount_ref(), value)

    @classmethod
    def changed(cls) -> Changed:
        return Changed(cls._mount_ref())


__all__ = [
    "AccordionRef",
    "CardRef",
    "Column",
    "Container",
    "FieldRef",
    "Fieldset",
    "Form",
    "Modal",
    "ModalRef",
    "Row",
    "TabsRef",
]
