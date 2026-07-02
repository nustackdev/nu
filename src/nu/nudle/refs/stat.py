"""StatRef: big number with label, optional delta and trend. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["StatRef"]


Trend = Literal["up", "down", "flat"]


class StatRef(NudleRef):
    """Display-only stat ref. Server-owned, single `write` op carries partial updates."""

    label: ClassVar[str] = ""
    value: ClassVar[str] = ""
    delta: ClassVar[str] = ""
    trend: ClassVar[str] = "flat"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "value": cls.value,
            "delta": cls.delta,
            "trend": cls.trend,
        }

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_value(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(value=text))

    def store_delta(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(delta=text))

    def store_trend(self, name: Nu | Trend | str) -> Nu:
        return Write(self, DictForm.of(trend=name))
