"""LineChart: time-series line chart. recharts LineChart on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["LineChart"]


XFormat = Literal["number", "time"]


class LineChart(NudleRef):
    """Display-only chart ref. `write` (partial) and `append` (one point or one series row)."""

    x_label: ClassVar[str] = ""
    y_label: ClassVar[str] = ""
    color: ClassVar[str] = "#2563eb"
    max_points: ClassVar[int] = 500
    x_format: ClassVar[str] = "number"
    show_legend: ClassVar[bool] = False
    show_tooltip: ClassVar[bool] = True
    palette: ClassVar[list[str]] = []

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "x_label": cls.x_label,
            "y_label": cls.y_label,
            "color": cls.color,
            "max_points": cls.max_points,
            "x_format": cls.x_format,
            "show_legend": cls.show_legend,
            "show_tooltip": cls.show_tooltip,
            "palette": list(cls.palette),
        }

    def store_points(self, points: Nu | list) -> Nu:
        return Write(self, DictForm.of(points=points))

    def store_series(self, series_list: Nu | list) -> Nu:
        return Write(self, DictForm.of(series=series_list))

    def store_x_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(x_label=text))

    def store_y_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(y_label=text))

    def store_color(self, value: Nu | str) -> Nu:
        return Write(self, DictForm.of(color=value))

    def store_max_points(self, value: Nu | int) -> Nu:
        return Write(self, DictForm.of(max_points=value))

    def store_x_format(self, value: Nu | XFormat | str) -> Nu:
        return Write(self, DictForm.of(x_format=value))

    def store_show_legend(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_legend=flag))

    def store_show_tooltip(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_tooltip=flag))

    def store_palette(self, colors: Nu | list) -> Nu:
        return Write(self, DictForm.of(palette=colors))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(points=[]))

    def store(
        self,
        points: Nu | list | dict | None = None,
        series: Nu | list | None = None,
        x_label: Nu | str | None = None,
        y_label: Nu | str | None = None,
        color: Nu | str | None = None,
        max_points: Nu | int | None = None,
        x_format: Nu | XFormat | str | None = None,
        show_legend: Nu | bool | None = None,
        show_tooltip: Nu | bool | None = None,
        palette: Nu | list | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not None:
            # legacy: store({"points": [...]}) keeps working.
            if isinstance(points, dict) and "points" in points:
                payload["points"] = points["points"]
            else:
                payload["points"] = points
        if series is not None:
            payload["series"] = series
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
        if show_legend is not None:
            payload["show_legend"] = show_legend
        if show_tooltip is not None:
            payload["show_tooltip"] = show_tooltip
        if palette is not None:
            payload["palette"] = palette
        return Write(self, DictForm.of(**payload))

    def append(self, x: Nu | float, y: Nu | float) -> Nu:
        return Append(self, x, y)

    def append_series(self, name: Nu | str, x: Nu | float, y: Nu | float) -> Nu:
        # single dict payload so the renderer can disambiguate from the single-series [x, y] form.
        return Append(self, DictForm.of(name=name, x=x, y=y))
