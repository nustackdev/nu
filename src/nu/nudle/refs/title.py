"""TitleRef: structural Ref bound to document.title.

Lives on an Index, not a Page. Write-only from host. The browser-side
slice writes assignments directly to document.title; it is not a body
slot and is not rendered into the visible tree. Class-level `default`
and `suffix` seed the browser on mount.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["TitleRef"]


class TitleRef(NudleRef):
    """Bound to document.title. Index-level structural Ref."""

    default: ClassVar[str] = ""
    suffix: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        if cls.default == "" and cls.suffix == "":
            return {}
        return {"default": cls.default, "suffix": cls.suffix}

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)
