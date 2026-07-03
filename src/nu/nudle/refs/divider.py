"""DividerRef: horizontal rule with optional inline label. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["DividerRef"]


Align = Literal["left", "center", "right"]


class DividerRef(NudleRef):
    """Display-only divider ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    align: ClassVar[str] = "center"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "align": cls.align}

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_align(self, side: Nu | Align | str) -> Nu:
        return Write(self, DictForm.of(align=side))

    def store(
        self,
        label: Nu | str,
        align: Nu | Align | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if align is not None:
            payload["align"] = align
        return Write(self, DictForm.of(**payload))
