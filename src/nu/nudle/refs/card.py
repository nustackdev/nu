"""CardRef: styled card Section. Header + body slots + footer text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.engine.structure import Declared
from nu.lang import Command

from ..protocol import Frame
from ..session import NudleSession
from .base import NudleRef
from .section import Section


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


__all__ = ["CardRef"]


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
