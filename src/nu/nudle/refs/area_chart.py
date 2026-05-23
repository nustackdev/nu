"""AreaChart: filled (optionally stacked) multi-series area chart. recharts on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu.queries.record import Record

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["AreaChart"]


XFormat = Literal["number", "time"]


class AreaChart(NudleRef):
    """Display-only area chart. `write` (partial) and `append` (one row)."""

    x_label: ClassVar[str] = ""
    y_label: ClassVar[str] = ""
    series: ClassVar[list[str]] = ["value"]
    colors: ClassVar[list[str]] = ["#2563eb"]
    stacked: ClassVar[bool] = False
    max_points: ClassVar[int] = 500
    x_format: ClassVar[str] = "number"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "x_label": cls.x_label,
            "y_label": cls.y_label,
            "series": list(cls.series),
            "colors": list(cls.colors),
            "stacked": cls.stacked,
            "max_points": cls.max_points,
            "x_format": cls.x_format,
        }

    def store_points(self, points: Nu | list) -> Nu:
        return Write(self, Record(points=points))

    def store_series(self, names: Nu | list) -> Nu:
        return Write(self, Record(series=names))

    def store_colors(self, colors: Nu | list) -> Nu:
        return Write(self, Record(colors=colors))

    def store_stacked(self, flag: Nu | bool) -> Nu:
        return Write(self, Record(stacked=flag))

    def store_x_label(self, text: Nu | str) -> Nu:
        return Write(self, Record(x_label=text))

    def store_y_label(self, text: Nu | str) -> Nu:
        return Write(self, Record(y_label=text))

    def store_max_points(self, value: Nu | int) -> Nu:
        return Write(self, Record(max_points=value))

    def store_x_format(self, value: Nu | XFormat | str) -> Nu:
        return Write(self, Record(x_format=value))

    def clear(self) -> Nu:
        return Write(self, Record(points=[]))

    def store(
        self,
        points: Nu | list | None = None,
        series: Nu | list | None = None,
        colors: Nu | list | None = None,
        stacked: Nu | bool | None = None,
        x_label: Nu | str | None = None,
        y_label: Nu | str | None = None,
        max_points: Nu | int | None = None,
        x_format: Nu | XFormat | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not None:
            payload["points"] = points
        if series is not None:
            payload["series"] = series
        if colors is not None:
            payload["colors"] = colors
        if stacked is not None:
            payload["stacked"] = stacked
        if x_label is not None:
            payload["x_label"] = x_label
        if y_label is not None:
            payload["y_label"] = y_label
        if max_points is not None:
            payload["max_points"] = max_points
        if x_format is not None:
            payload["x_format"] = x_format
        return Write(self, Record(**payload))

    def append(self, x: Nu | float, *ys: Nu | float) -> Nu:
        return Append(self, x, *ys)
