"""Chrome containers -- Refs for the boxes that frame their children.

Card, Container (``BoxRef``), Tabs, Modal, Accordion, Form, Fieldset and
Field. Each is a ``ContainerRef``: children are open-ended, and the chrome
the box carries of its own (a Card's title, a Tabs' active tab, a Field's
label) is props seeded by ``slot()`` and driven by ``set_*``. The Shapes over
them live in ``nustd.ui.shapes.chrome``.

The chrome commands (`_SetSectionStr`, `_SetTabs`, `_SetActive`) target the
abstract ``Session`` from core, so this module is host-agnostic; any host
that implements ``Session`` runs it. Chrome is driven off the bound Ref --
``page.card.set_title(...)`` or ``CardRef("c", parent_ref=col).set_title(...)``
-- and the address comes from that Ref's chain. There is no way to drive a
container off a Shape class: a class has no mount point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.engine.structure import Declared
from nu.forms import Dict
from nu.lang import Command
from nu.lang.sentinels import EMPTY, UNSET
from nustd.ui.core import Frame, Ref, Session
from nustd.ui.core.interactions import Changed, Write

from .base import ContainerRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.args import Arg, BoolArg, ListArg, StrArg
    from nu.lang.runtime import Runtime


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


class AccordionRef(ContainerRef):
    """Stack of collapsible sections. Tab owns open state, server owns the section list."""

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

    def set_sections(self, items: ListArg[dict[str, str]]) -> Nu:
        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(self, Dict.of(sections=value))

    def set_open(self, ids: ListArg[str]) -> Nu:
        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(self, Dict.of(open=value))

    def on_change(self) -> Changed:
        return Changed(self)


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
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            if value is EMPTY:
                raise ValueError("cannot write EMPTY")
            await session.send(Frame(self._op, ref=path, payload=value))

        return athunk


class CardRef(ContainerRef):
    """Card-styled container: title + subtitle + body children + footer."""

    _wire_type = "Card"

    @classmethod
    def slot(cls, *, title: str = "", subtitle: str = "", footer: str = "") -> Self:
        return super().slot(title=title, subtitle=subtitle, footer=footer)

    def set_title(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_title", text)

    def set_subtitle(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_subtitle", text)

    def set_footer(self, text: StrArg) -> Nu:
        return _SetSectionStr(self, "set_footer", text)


Padding = Literal["none", "sm", "md", "lg"]
Border = Literal["none", "hairline", "card"]
Background = Literal["none", "muted", "accent"]
Shadow = Literal["none", "sm", "md"]
Gap = Literal["none", "sm", "md", "lg"]


# Backs the ``Container`` Shape and draws as the browser's "Container" node.
# It cannot be called ContainerRef: that name is the base every container
# Ref subclasses, so the Ref behind this one box is BoxRef.
class BoxRef(ContainerRef):
    """Styled card-like box with an optional title. Pin chrome on slot()."""

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


class FieldRef(ContainerRef):
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
        return super().slot(label=label, help=help, error=error, required=required)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_help(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(help=text))

    def set_error(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(error=text))

    def set_required(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(required=flag))


FieldsetGap = Literal["sm", "md", "lg"]


class FieldsetRef(ContainerRef):
    """Grouped fields with a legend. Display-only, server-owned."""

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

    def set_legend(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(legend=text))

    def set_gap(self, value: FieldsetGap | StrArg) -> Nu:
        return Write(self, Dict.of(gap=value))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))


Align = Literal["start", "center", "end", "stretch"]


class FormRef(ContainerRef):
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


class ModalRef(ContainerRef):
    """Dialog overlay. Open vs closed is the thing it carries, so it has a `set()`."""

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


class _SetTabs(Command):
    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: Ref, value: Arg[Any]) -> None:
        super().__init__(ref, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            if value is EMPTY:
                raise ValueError("cannot write EMPTY")
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
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            if value is EMPTY:
                raise ValueError("cannot write EMPTY")
            payload = "" if value is None else str(value)
            await session.send(Frame("set_active", ref=path, payload=payload))

        return athunk


class TabsRef(ContainerRef):
    """Tab strip plus active body. One child per tab body."""

    _wire_type = "Tabs"

    @classmethod
    def slot(
        cls,
        *,
        tabs: list[dict[str, str]] | None = None,
        active: str = "",
    ) -> Self:
        return super().slot(tabs=_normalize_tabs(tabs or []), active=active)

    def set_tabs(self, value: ListArg[dict[str, str]]) -> Nu:
        return _SetTabs(self, value)

    def set_active(self, value: StrArg) -> Nu:
        return _SetActive(self, value)

    def on_change(self) -> Changed:
        return Changed(self)
