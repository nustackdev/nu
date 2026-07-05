"""Layout Sections -- Shape-based containers that wrap other Refs.

Most of these are `Section` subclasses (not Refs) — Shape-based
composition primitives that mount other Refs and Sections. Section
is the base class defined here alongside its subclasses (Row, Column,
Card, Tabs, etc.) and the SectionRef substrate ref backing them.
See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self

from nu import DictForm, Shape
from nu.domains.shape import Slot
from nu.engine.structure import Declared
from nu.lang import Command

from ..interactions import Changed, Write
from ..protocol import Frame
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Context, Nu
    from nu.lang.runtime import Runtime


class SectionRef(NudleRef):
    """Internal Ref backing a Section slot.

    Instances are created by `Section.slot()` and exposed at Page or
    parent-Section class level (e.g. `HomePage.toolbar`). The instance
    carries `section_cls`; attribute access on it (e.g. `.text`) returns
    a child Ref whose `parent` is this SectionRef.
    """

    def __init__(
        self,
        address: object,
        *,
        section_cls: type[Section],
        parent_ref: NudleRef | None = None,
        owner_shape: type[Section] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["section_cls"] = section_cls

    def __getattr__(self, name: str) -> object:
        # Only called when normal attribute lookup fails. Map to a child
        # slot on the bound Section class. Read payload straight off __dict__ so
        # this never recurses back through __getattr__.
        payload = self.__dict__.get("_payload") or {}
        section_cls = payload.get("section_cls")
        if section_cls is None:
            raise AttributeError(name)
        slots = getattr(section_cls, "_slots", {})
        if name in slots:
            slot = slots[name]
            return slot.create_ref(owner_shape=section_cls, parent_ref=self)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
            f" (section '{section_cls.__name__}' has no slot '{name}')"
        )


class Section(Shape):
    """Base for Shape-based layout primitives.

    Subclass `Row`, `Column`, `Container` (defined in `nudle.refs`). User
    code subclasses those to pin chrome defaults and declare child slots:

        class Toolbar(nudle.Row):
            gap = 3
            text = nudle.TextRef.slot()
            btn = nudle.ButtonRef.slot()
    """

    _is_nudle_section: ClassVar[bool] = True
    # Filled in by the enclosing Page (or parent Section) at class
    # creation time. Tuple of slot-path segments from the owning Page
    # down to (but not including) this section.
    # Example: HomePage.toolbar -> ("toolbar",)
    # Example: HomePage.panel.toolbar -> ("panel", "toolbar")
    _nudle_mount: ClassVar[tuple[type, tuple[str, ...]] | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        """Class-level layout chrome shipped in the mount field entry."""
        return {}

    @classmethod
    def slot(cls) -> Self:
        return Slot(SectionRef, section_cls=cls)  # type: ignore[return-value]


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


class _AccordionMountRef(NudleRef):
    """Internal Ref bound to an AccordionRef subclass's mount point."""

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        section_cls = self._payload.get("section_cls")
        mount = getattr(section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"AccordionRef {section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class AccordionRef(Section):
    """Stack of collapsible sections. Tab owns open state, server owns the section list."""

    sections: ClassVar[list[dict[str, str]]] = []
    open: ClassVar[list[str]] = []
    multi: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "sections": _normalize_sections(cls.sections),
            "open": _normalize_open(cls.open),
            "multi": bool(cls.multi),
        }

    @classmethod
    def _mount_ref(cls) -> _AccordionMountRef:
        return _AccordionMountRef(section_cls=cls)

    @classmethod
    def store_sections(cls, items: Nu | list[dict[str, str]]) -> Nu:
        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(cls._mount_ref(), DictForm.of(sections=value))

    @classmethod
    def store_open(cls, ids: Nu | list[str]) -> Nu:
        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(cls._mount_ref(), DictForm.of(open=value))

    @classmethod
    def changed(cls) -> Changed:
        return Changed(cls._mount_ref())


class _CardMountRef(NudleRef):
    """Internal Ref bound to a CardRef subclass's mount point.

    Resolves directly via ``Section._nudle_mount`` so chrome interactions
    (title/subtitle/footer) target the card's own wire path, not a child slot.
    Mirrors ``_TabsMountRef`` — the shared "drive a Section by its mount path"
    shape (the mount-ref family is a candidate for later unification).
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def _aresolve_address(self, rt: Runtime, nid: int) -> str:
        section_cls = self._payload.get("section_cls")
        mount = getattr(section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"Card {section_cls.__name__} has no mount point. "
                "Declare it as a Slot on a Page before driving it.",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class _StoreSectionStr(Command):
    """Send a string-payload Frame to a Section by mount path.

    Slot 0 holds a mount Ref (``_CardMountRef``) so this is a well-formed
    ``mutates={0}`` Command; the wire op is supplied at construction (e.g.
    "store_title") so one class serves all three card chrome ops.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: NudleRef, op: str, value: Nu | Any) -> None:
        super().__init__(ref, value)
        self._payload["op"] = op

    @property
    def _op(self) -> str:
        return self._payload["op"]  # type: ignore[return-value]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            await session.send(Frame(self._op, ref=path, payload=value))

        return athunk

    def __repr__(self) -> str:
        return f"_StoreSectionStr({self._children[0]!r}, {self._op!r}, {self._children[1]!r})"


class CardRef(Section):
    """Card-styled Section: title + subtitle + body slots + footer."""

    title: ClassVar[str] = ""
    subtitle: ClassVar[str] = ""
    footer: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"title": cls.title, "subtitle": cls.subtitle, "footer": cls.footer}

    @classmethod
    def _mount_ref(cls) -> _CardMountRef:
        return _CardMountRef(section_cls=cls)

    @classmethod
    def store_title(cls, text: Nu | str) -> Nu:
        return _StoreSectionStr(cls._mount_ref(), "store_title", text)

    @classmethod
    def store_subtitle(cls, text: Nu | str) -> Nu:
        return _StoreSectionStr(cls._mount_ref(), "store_subtitle", text)

    @classmethod
    def store_footer(cls, text: Nu | str) -> Nu:
        return _StoreSectionStr(cls._mount_ref(), "store_footer", text)


Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around"]


class Column(Section):
    """Vertical flex layout. Pin chrome on the subclass."""

    gap: ClassVar[int] = 4
    align: ClassVar[str] = "stretch"
    justify: ClassVar[str] = "start"
    padding: ClassVar[int] = 0

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "gap": cls.gap,
            "align": cls.align,
            "justify": cls.justify,
            "padding": cls.padding,
        }


Padding = Literal["none", "sm", "md", "lg"]
Border = Literal["none", "hairline", "card"]
Background = Literal["none", "muted", "accent"]
Shadow = Literal["none", "sm", "md"]
Gap = Literal["none", "sm", "md", "lg"]


class Container(Section):
    """Styled card-like box. Pin chrome on the subclass."""

    title: ClassVar[str] = ""
    padding: ClassVar[str] = "md"
    border: ClassVar[str] = "hairline"
    background: ClassVar[str] = "none"
    shadow: ClassVar[str] = "none"
    gap: ClassVar[str] = "md"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "title": cls.title,
            "padding": cls.padding,
            "border": cls.border,
            "background": cls.background,
            "shadow": cls.shadow,
            "gap": cls.gap,
        }


class _FieldMountRef(NudleRef):
    """Internal Ref bound to a FieldRef subclass's mount point.

    Resolves directly via ``Section._nudle_mount`` so chrome writes (label,
    help, error, required) target the section's own wire path -- not the
    wrapped child.
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        section_cls = self._payload.get("section_cls")
        mount = getattr(section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"FieldRef {section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class FieldRef(Section):
    """Label + child input + help / error text. Exactly one child slot."""

    label: ClassVar[str] = ""
    help: ClassVar[str] = ""
    error: ClassVar[str] = ""
    required: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        slot_count = len(getattr(cls, "_slots", {}))
        if slot_count != 1:
            raise RuntimeError(
                f"FieldRef {cls.__name__} declares {slot_count} child slots; "
                "FieldRef requires exactly one.",
            )

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "help": cls.help,
            "error": cls.error,
            "required": cls.required,
        }

    @classmethod
    def _mount_ref(cls) -> _FieldMountRef:
        return _FieldMountRef(section_cls=cls)

    @classmethod
    def store_label(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(label=text))

    @classmethod
    def store_help(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(help=text))

    @classmethod
    def store_error(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(error=text))

    @classmethod
    def store_required(cls, flag: Nu | bool) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(required=flag))


Gap = Literal["sm", "md", "lg"]


class _FieldsetMountRef(NudleRef):
    """Internal Ref bound to a Fieldset subclass's mount point.

    Resolves directly via ``Section._nudle_mount`` so chrome writes (legend,
    gap, disabled) target the section's own wire path -- not a child.
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        section_cls = self._payload.get("section_cls")
        mount = getattr(section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"Fieldset {section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class Fieldset(Section):
    """Grouped fields with a legend. Display-only, server-owned."""

    legend: ClassVar[str] = ""
    gap: ClassVar[str] = "md"
    disabled: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"legend": cls.legend, "gap": cls.gap, "disabled": cls.disabled}

    @classmethod
    def _mount_ref(cls) -> _FieldsetMountRef:
        return _FieldsetMountRef(section_cls=cls)

    @classmethod
    def store_legend(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(legend=text))

    @classmethod
    def store_gap(cls, value: Nu | Gap | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(gap=value))

    @classmethod
    def store_disabled(cls, flag: Nu | bool) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(disabled=flag))


class Form(Section):
    """Semantic form wrapper. Pin chrome on the subclass; submit lives on a child ButtonRef."""

    title: ClassVar[str] = ""
    gap: ClassVar[int] = 4
    padding: ClassVar[int] = 0
    align: ClassVar[str] = "stretch"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "title": cls.title,
            "gap": cls.gap,
            "padding": cls.padding,
            "align": cls.align,
        }


class ModalRef(SectionRef):
    """SectionRef backing a Modal slot. Carries Modal-only interaction methods."""

    def store_open(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(open=flag))

    def store_title(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(title=text))

    def store(self, open: Nu | bool | None = None, title: Nu | str | None = None) -> Nu:
        payload: dict[str, object] = {}
        if open is not None:
            payload["open"] = open
        if title is not None:
            payload["title"] = title
        return Write(self, DictForm.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


class Modal(Section):
    """Dialog overlay. Pin chrome on the subclass; declare body Refs as slots."""

    open: ClassVar[bool] = False
    title: ClassVar[str] = ""
    dismissible: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "open": cls.open,
            "title": cls.title,
            "dismissible": cls.dismissible,
        }

    @classmethod
    def slot(cls) -> Self:
        return Slot(ModalRef, section_cls=cls)  # type: ignore[return-value]


Align = Literal["start", "center", "end", "stretch", "baseline"]
Justify = Literal["start", "center", "end", "between", "around", "evenly"]


class Row(Section):
    """Horizontal flex layout. Pin chrome on the subclass."""

    gap: ClassVar[int] = 4
    align: ClassVar[str] = "center"
    justify: ClassVar[str] = "start"
    wrap: ClassVar[bool] = False
    padding: ClassVar[int] = 0

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "gap": cls.gap,
            "align": cls.align,
            "justify": cls.justify,
            "wrap": cls.wrap,
            "padding": cls.padding,
        }


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


class _StoreTabs(Command):
    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            if isinstance(value, list):
                value = _normalize_tabs(value)
            await session.send(Frame("store_tabs", ref=path, payload=value))

        return athunk


class _StoreActive(Command):
    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            payload = "" if value is None else str(value)
            await session.send(Frame("store_active", ref=path, payload=payload))

        return athunk


class _TabsMountRef(NudleRef):
    """Internal Ref bound to a TabsRef subclass's mount point.

    Resolves directly via Section._nudle_mount so interactions target the
    section's own wire path (not a child slot).
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def _aresolve_address(self, rt: Runtime, nid: int) -> str:
        section_cls = self._payload.get("section_cls")
        mount = getattr(section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"TabsRef {section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class TabsRef(Section):
    """Tab strip plus active body. Subclass and declare one child slot per tab body."""

    tabs: ClassVar[list[dict[str, str]]] = []
    active: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "tabs": _normalize_tabs(cls.tabs),
            "active": cls.active,
        }

    @classmethod
    def _mount_ref(cls) -> _TabsMountRef:
        return _TabsMountRef(section_cls=cls)

    @classmethod
    def store_tabs(cls, value: Nu | list[dict[str, str]]) -> Nu:
        return _StoreTabs(cls._mount_ref(), value)

    @classmethod
    def store_active(cls, value: Nu | str) -> Nu:
        return _StoreActive(cls._mount_ref(), value)

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
    "Section",
    "TabsRef",
]
