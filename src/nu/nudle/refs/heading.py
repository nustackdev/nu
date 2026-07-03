"""HeadingRef: in-body heading with selectable level and alignment. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["HeadingRef"]


Align = Literal["left", "center", "right"]


class HeadingRef(NudleRef):
    """Display-only heading ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    level: ClassVar[int] = 1
    align: ClassVar[str] = "left"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "level": cls.level, "align": cls.align}

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_level(self, n: Nu | int) -> Nu:
        return Write(self, DictForm.of(level=n))

    def store_align(self, side: Nu | Align | str) -> Nu:
        return Write(self, DictForm.of(align=side))

    def store(
        self,
        label: Nu | str,
        level: Nu | int | None = None,
        align: Nu | Align | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if level is not None:
            payload["level"] = level
        if align is not None:
            payload["align"] = align
        return Write(self, DictForm.of(**payload))
