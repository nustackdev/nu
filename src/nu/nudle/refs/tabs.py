"""TabsRef: tab strip plus active body. Section-shaped, with children paired to tabs by index."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode

from ..interactions.changed import Changed
from ..protocol import Frame
from ..session import NudleSession
from .base import NudleRef
from .section import Section


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["TabsRef"]


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


class _StoreTabs(ScalarCommand):
    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if isinstance(value, list):
            value = _normalize_tabs(value)
        await session.send(Frame("store_tabs", ref=path, payload=value))

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")


class _StoreActive(ScalarCommand):
    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        value = await runtime.afirst(self._children[1], ctx)
        payload = "" if value is None else str(value)
        await session.send(Frame("store_active", ref=path, payload=payload))

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")


class _TabsMountRef(NudleRef):
    """Internal Ref bound to a TabsRef subclass's mount point.

    Resolves directly via Section._nudle_mount so interactions target the
    section's own wire path (not a child slot).
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._section_cls = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        mount = getattr(self._section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"TabsRef {self._section_cls.__name__} has no mount point. "
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
