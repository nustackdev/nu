"""CardRef: styled card Section. Header + body slots + footer text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.engine.structure import Declared
from nu.lang import Command

from ..protocol import Frame
from ..session import NudleSession
from .section import Section


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


__all__ = ["CardRef"]


class _StoreSectionStr(Command):
    """Send a string-payload Frame to a Section by mount path.

    Wire op is supplied at construction time (e.g. "store_title") so the
    class can serve all three card chrome ops without one Interaction
    class per op.
    """

    mutates = Declared(value=frozenset({0}))
    requires_async = Declared(value=True)

    def __init__(self, section_cls: type[Section], op: str, value: Nu | Any) -> None:
        super().__init__(value)
        self.payload["section_cls"] = section_cls
        self.payload["op"] = op

    @property
    def _section_cls(self) -> type[Section]:
        return self.payload["section_cls"]  # type: ignore[return-value]

    @property
    def _op(self) -> str:
        return self.payload["op"]  # type: ignore[return-value]

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value_thunk = children[0]

        async def athunk(rt: Runtime) -> None:
            mount = getattr(self._section_cls, "_nudle_mount", None)
            if mount is None:
                raise RuntimeError(
                    f"Section {self._section_cls.__name__} has no mount point. "
                    "Declare it as a Slot on a Page before driving it.",
                )
            page_cls, slot_path = mount
            path = ".".join([page_cls.__name__, *slot_path])
            session = rt.ctx.get(NudleSession)
            value = await value_thunk(rt)
            await session.send(Frame(self._op, ref=path, payload=value))

        return athunk

    def __repr__(self) -> str:
        return (
            f"_StoreSectionStr({self._section_cls.__name__}, {self._op!r}, {self.children[0]!r})"
        )


class CardRef(Section):
    """Card-styled Section: title + subtitle + body slots + footer."""

    title: ClassVar[str] = ""
    subtitle: ClassVar[str] = ""
    footer: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"title": cls.title, "subtitle": cls.subtitle, "footer": cls.footer}

    @classmethod
    def store_title(cls, text: Nu | str) -> Nu:
        return _StoreSectionStr(cls, "store_title", text)

    @classmethod
    def store_subtitle(cls, text: Nu | str) -> Nu:
        return _StoreSectionStr(cls, "store_subtitle", text)

    @classmethod
    def store_footer(cls, text: Nu | str) -> Nu:
        return _StoreSectionStr(cls, "store_footer", text)
