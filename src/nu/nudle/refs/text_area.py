"""TextAreaRef: multi-line text input. Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["TextAreaRef"]


class TextAreaRef(NudleRef):
    """Multi-line text input whose value lives in the browser."""

    value: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    rows: ClassVar[int] = 4
    max_length: ClassVar[int | None] = None
    auto_resize: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "placeholder": cls.placeholder,
            "rows": cls.rows,
            "max_length": cls.max_length,
            "auto_resize": cls.auto_resize,
        }

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
