"""Chart Refs -- typed visualization sinks over series payloads.

Same directionality as other output Refs (server pushes points via
`write` / `append`; browser only renders). Grouped by shape rather
than by semantics because the payload contract is chart-specific.
See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


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
        return Write(self, DictForm.of(points=points))

    def store_series(self, names: Nu | list) -> Nu:
        return Write(self, DictForm.of(series=names))

    def store_colors(self, colors: Nu | list) -> Nu:
        return Write(self, DictForm.of(colors=colors))

    def store_stacked(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(stacked=flag))

    def store_x_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(x_label=text))

    def store_y_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(y_label=text))

    def store_max_points(self, value: Nu | int) -> Nu:
        return Write(self, DictForm.of(max_points=value))

    def store_x_format(self, value: Nu | XFormat | str) -> Nu:
        return Write(self, DictForm.of(x_format=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(points=[]))

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
        return Write(self, DictForm.of(**payload))

    def append(self, x: Nu | float, *ys: Nu | float) -> Nu:
        return Append(self, x, *ys)


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


DEFAULT_COLORS: list[str] = [
    "#2563eb",
    "#16a34a",
    "#f59e0b",
    "#dc2626",
    "#7c3aed",
    "#0891b2",
    "#db2777",
    "#65a30d",
]


class PieChart(NudleRef):
    """Display-only pie chart ref. `write` (partial) and `append` (one slice)."""

    slices: ClassVar[list] = []
    colors: ClassVar[list[str]] = DEFAULT_COLORS
    inner_radius: ClassVar[float] = 0.0
    show_labels: ClassVar[bool] = True
    show_legend: ClassVar[bool] = True
    total_label: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "slices": list(cls.slices),
            "colors": list(cls.colors),
            "inner_radius": cls.inner_radius,
            "show_labels": cls.show_labels,
            "show_legend": cls.show_legend,
            "total_label": cls.total_label,
        }

    def store_slices(self, slices: Nu | list) -> Nu:
        return Write(self, DictForm.of(slices=slices))

    def store_colors(self, colors: Nu | list) -> Nu:
        return Write(self, DictForm.of(colors=colors))

    def store_inner_radius(self, value: Nu | float) -> Nu:
        return Write(self, DictForm.of(inner_radius=value))

    def store_show_labels(self, value: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_labels=value))

    def store_show_legend(self, value: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_legend=value))

    def store_total_label(self, value: Nu | str) -> Nu:
        return Write(self, DictForm.of(total_label=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(slices=[]))

    def store(
        self,
        slices: Nu | list | dict | None = None,
        colors: Nu | list | None = None,
        inner_radius: Nu | float | None = None,
        show_labels: Nu | bool | None = None,
        show_legend: Nu | bool | None = None,
        total_label: Nu | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if slices is not None:
            # legacy: store({"slices": [...]}) keeps working.
            if isinstance(slices, dict) and "slices" in slices:
                payload["slices"] = slices["slices"]
            else:
                payload["slices"] = slices
        if colors is not None:
            payload["colors"] = colors
        if inner_radius is not None:
            payload["inner_radius"] = inner_radius
        if show_labels is not None:
            payload["show_labels"] = show_labels
        if show_legend is not None:
            payload["show_legend"] = show_legend
        if total_label is not None:
            payload["total_label"] = total_label
        return Write(self, DictForm.of(**payload))

    def append(self, label: Nu | str, value: Nu | float) -> Nu:
        return Append(self, label, value)


class Sparkline(NudleRef):
    """Display-only inline trend line. `write` (partial) and `append` (one point)."""

    color: ClassVar[str] = "#2563eb"
    height: ClassVar[int] = 32
    max_points: ClassVar[int] = 100

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "color": cls.color,
            "height": cls.height,
            "max_points": cls.max_points,
        }

    def store_points(self, points: Nu | list) -> Nu:
        return Write(self, DictForm.of(points=points))

    def store_color(self, value: Nu | str) -> Nu:
        return Write(self, DictForm.of(color=value))

    def store_height(self, value: Nu | int) -> Nu:
        return Write(self, DictForm.of(height=value))

    def store_max_points(self, value: Nu | int) -> Nu:
        return Write(self, DictForm.of(max_points=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(points=[]))

    def store(
        self,
        points: Nu | list | dict | None = None,
        color: Nu | str | None = None,
        height: Nu | int | None = None,
        max_points: Nu | int | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not None:
            if isinstance(points, dict) and "points" in points:
                payload["points"] = points["points"]
            else:
                payload["points"] = points
        if color is not None:
            payload["color"] = color
        if height is not None:
            payload["height"] = height
        if max_points is not None:
            payload["max_points"] = max_points
        return Write(self, DictForm.of(**payload))

    def append(self, x: Nu | float, y: Nu | float) -> Nu:
        return Append(self, x, y)


__all__ = ["AreaChart", "BarChart", "LineChart", "PieChart", "Sparkline"]
