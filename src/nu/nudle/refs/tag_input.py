"""TagInputRef: multi-tag entry field. Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["TagInputRef"]


class TagInputRef(NudleRef):
    """Multi-tag entry field whose committed list lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    value: ClassVar[list[str]] = []
    max_tags: ClassVar[int | None] = None
    allow_duplicates: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "value": list(cls.value),
            "max_tags": cls.max_tags,
            "allow_duplicates": cls.allow_duplicates,
        }

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | list[str]) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
