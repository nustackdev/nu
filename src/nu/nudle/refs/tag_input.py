"""TagInputRef: multi-tag entry field. Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | list[str]) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
