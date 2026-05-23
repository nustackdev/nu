"""LineChart: time-series line chart. recharts LineChart on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["LineChart"]


XFormat = Literal["number", "time"]


class LineChart(NudleRef):
    """Display-only chart ref. `write` (partial) and `append` (one point)."""

    x_label: ClassVar[str] = ""
    y_label: ClassVar[str] = ""
    color: ClassVar[str] = "#2563eb"
    max_points: ClassVar[int] = 500
    x_format: ClassVar[str] = "number"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "x_label": cls.x_label,
            "y_label": cls.y_label,
            "color": cls.color,
            "max_points": cls.max_points,
            "x_format": cls.x_format,
        }

    def store_points(self, points: Nu | list) -> Nu:
        return Write(self, {"points": points})

    def store_x_label(self, text: Nu | str) -> Nu:
        return Write(self, {"x_label": text})

    def store_y_label(self, text: Nu | str) -> Nu:
        return Write(self, {"y_label": text})

    def store_color(self, value: Nu | str) -> Nu:
        return Write(self, {"color": value})

    def store_max_points(self, value: Nu | int) -> Nu:
        return Write(self, {"max_points": value})

    def store_x_format(self, value: Nu | XFormat | str) -> Nu:
        return Write(self, {"x_format": value})

    def clear(self) -> Nu:
        return Write(self, {"points": []})

    def store(
        self,
        points: Nu | list | dict | None = None,
        x_label: Nu | str | None = None,
        y_label: Nu | str | None = None,
        color: Nu | str | None = None,
        max_points: Nu | int | None = None,
        x_format: Nu | XFormat | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not None:
            # legacy: store({"points": [...]}) keeps working.
            if isinstance(points, dict) and "points" in points:
                payload["points"] = points["points"]
            else:
                payload["points"] = points
        if x_label is not None:
            payload["x_label"] = x_label
        if y_label is not None:
            payload["y_label"] = y_label
        if color is not None:
            payload["color"] = color
        if max_points is not None:
            payload["max_points"] = max_points
        if x_format is not None:
            payload["x_format"] = x_format
        return Write(self, payload)

    def append(self, x: Nu | float, y: Nu | float) -> Nu:
        return Append(self, x, y)
