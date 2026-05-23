"""DatePickerRef: single date picker. Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["DatePickerRef"]


class DatePickerRef(NudleRef):
    """Date input whose ISO yyyy-mm-dd value lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    min: ClassVar[str] = ""
    max: ClassVar[str] = ""
    default: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "min": cls.min,
            "max": cls.max,
            "default": cls.default,
        }

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
