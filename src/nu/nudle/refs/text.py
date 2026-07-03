"""TextRef: plain-text paragraph or short body string. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["TextRef"]


class TextRef(NudleRef):
    """Display-only string ref. Body copy."""

    value: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        if cls.value == "":
            return {}
        return {"value": cls.value}

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)
