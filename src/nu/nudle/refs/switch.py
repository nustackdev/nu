"""SwitchRef: boolean toggle (switch affordance). Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["SwitchRef"]


class SwitchRef(NudleRef):
    """On/off switch whose checked state lives in the browser."""

    label: ClassVar[str] = ""
    default: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "checked": cls.default}

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | bool) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
