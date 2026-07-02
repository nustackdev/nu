"""BarChart: categorical bar chart. recharts BarChart on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["BarChart"]


Orientation = Literal["vertical", "horizontal"]


class BarChart(NudleRef):
    """Display-only chart ref. `write` (partial) and `append` (one bar)."""

    x_label: ClassVar[str] = ""
    y_label: ClassVar[str] = ""
    color: ClassVar[str] = "#2563eb"
    orientation: ClassVar[str] = "vertical"
    max_bars: ClassVar[int] = 200

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "x_label": cls.x_label,
            "y_label": cls.y_label,
            "color": cls.color,
            "orientation": cls.orientation,
            "max_bars": cls.max_bars,
        }

    def store_bars(self, bars: Nu | list) -> Nu:
        return Write(self, DictForm.of(bars=bars))

    def store_x_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(x_label=text))

    def store_y_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(y_label=text))

    def store_color(self, value: Nu | str) -> Nu:
        return Write(self, DictForm.of(color=value))

    def store_orientation(self, value: Nu | Orientation | str) -> Nu:
        return Write(self, DictForm.of(orientation=value))

    def store_max_bars(self, value: Nu | int) -> Nu:
        return Write(self, DictForm.of(max_bars=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(bars=[]))

    def store(
        self,
        bars: Nu | list | dict | None = None,
        x_label: Nu | str | None = None,
        y_label: Nu | str | None = None,
        color: Nu | str | None = None,
        orientation: Nu | Orientation | str | None = None,
        max_bars: Nu | int | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if bars is not None:
            if isinstance(bars, dict) and "bars" in bars:
                payload["bars"] = bars["bars"]
            else:
                payload["bars"] = bars
        if x_label is not None:
            payload["x_label"] = x_label
        if y_label is not None:
            payload["y_label"] = y_label
        if color is not None:
            payload["color"] = color
        if orientation is not None:
            payload["orientation"] = orientation
        if max_bars is not None:
            payload["max_bars"] = max_bars
        return Write(self, DictForm.of(**payload))

    def append(self, category: Nu | str, value: Nu | float) -> Nu:
        return Append(self, category, value)
