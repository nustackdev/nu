"""ProgressRef: progress bar in [0, 1] with optional caption. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["ProgressRef"]


class ProgressRef(NudleRef):
    """Display-only progress ref. One `write` op carries every mutation."""

    value: ClassVar[float] = 0.0
    caption: ClassVar[str] = ""
    indeterminate: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "caption": cls.caption,
            "indeterminate": cls.indeterminate,
        }

    def store_value(self, value: Nu | float) -> Nu:
        return Write(self, {"value": value})

    def store_caption(self, text: Nu | str) -> Nu:
        return Write(self, {"caption": text})

    def store_indeterminate(self, flag: Nu | bool) -> Nu:
        return Write(self, {"indeterminate": flag})

    def store(
        self,
        value: Nu | float,
        caption: Nu | str | None = None,
        indeterminate: Nu | bool | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if caption is not None:
            payload["caption"] = caption
        if indeterminate is not None:
            payload["indeterminate"] = indeterminate
        return Write(self, payload)
