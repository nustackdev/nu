"""CheckboxRef: boolean toggle. Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


__all__ = ["CheckboxRef"]


class CheckboxRef(NudleRef):
    """Boolean toggle whose checked state lives in the browser."""

    label: ClassVar[str] = ""
    checked: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "checked": cls.checked}

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | bool) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
