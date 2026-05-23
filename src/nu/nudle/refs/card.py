"""CardRef: styled card Section. Header + body slots + footer text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode

from ..protocol import Frame
from ..session import NudleSession
from .section import Section


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["CardRef"]


class _StoreSectionStr(ScalarCommand):
    """Send a string-payload Frame to a Section by mount path.

    Wire op is supplied at construction time (e.g. "store_title") so the
    class can serve all three card chrome ops without one Interaction
    class per op.
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, section_cls: type[Section], op: str, value: Nu | Any) -> None:
        super().__init__(value)
        self._section_cls = section_cls
        self._op = op

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        mount = getattr(self._section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"Section {self._section_cls.__name__} has no mount point. "
                "Declare it as a Slot on a Page before driving it.",
            )
        page_cls, slot_path = mount
        path = ".".join([page_cls.__name__, *slot_path])
        session = ctx.get(NudleSession)
        value = await runtime.afirst(self._children[0], ctx)
        await session.send(Frame(self._op, ref=path, payload=value))

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")

    def __repr__(self) -> str:
        return (
            f"_StoreSectionStr({self._section_cls.__name__}, {self._op!r}, {self._children[0]!r})"
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
