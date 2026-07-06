"""Chart Refs -- typed visualization sinks over series payloads.

Same directionality as other output Refs (server pushes points via
`write` / `append`; browser only renders). Grouped by shape rather
than by semantics because the payload contract is chart-specific.
See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from nu import DictForm
from nu.lang.args import BoolArg, DictArg, FloatArg, IntArg, ListArg, StrArg
from nu.lang.sentinels import UNSET

from ..interactions import Append, Write
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
    def _mount_props(cls) -> dict[str, object]:
        return {
            "x_label": cls.x_label,
            "y_label": cls.y_label,
            "series": list(cls.series),
            "colors": list(cls.colors),
            "stacked": cls.stacked,
            "max_points": cls.max_points,
            "x_format": cls.x_format,
        }

    def store_points(self, points: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(points=points))

    def store_series(self, names: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(series=names))

    def store_colors(self, colors: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(colors=colors))

    def store_stacked(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(stacked=flag))

    def store_x_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(x_label=text))

    def store_y_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(y_label=text))

    def store_max_points(self, value: IntArg) -> Nu:
        return Write(self, DictForm.of(max_points=value))

    def store_x_format(self, value: XFormat | StrArg) -> Nu:
        return Write(self, DictForm.of(x_format=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(points=[]))

    def store(
        self,
        points: ListArg[Any] = UNSET,
        series: ListArg[Any] = UNSET,
        colors: ListArg[Any] = UNSET,
        stacked: BoolArg = UNSET,
        x_label: StrArg = UNSET,
        y_label: StrArg = UNSET,
        max_points: IntArg = UNSET,
        x_format: XFormat | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not UNSET:
            payload["points"] = points
        if series is not UNSET:
            payload["series"] = series
        if colors is not UNSET:
            payload["colors"] = colors
        if stacked is not UNSET:
            payload["stacked"] = stacked
        if x_label is not UNSET:
            payload["x_label"] = x_label
        if y_label is not UNSET:
            payload["y_label"] = y_label
        if max_points is not UNSET:
            payload["max_points"] = max_points
        if x_format is not UNSET:
            payload["x_format"] = x_format
        return Write(self, DictForm.of(**payload))

    def append(self, x: FloatArg, *ys: FloatArg) -> Nu:
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
    def _mount_props(cls) -> dict[str, object]:
        return {
            "x_label": cls.x_label,
            "y_label": cls.y_label,
            "color": cls.color,
            "orientation": cls.orientation,
            "max_bars": cls.max_bars,
        }

    def store_bars(self, bars: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(bars=bars))

    def store_x_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(x_label=text))

    def store_y_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(y_label=text))

    def store_color(self, value: StrArg) -> Nu:
        return Write(self, DictForm.of(color=value))

    def store_orientation(self, value: Orientation | StrArg) -> Nu:
        return Write(self, DictForm.of(orientation=value))

    def store_max_bars(self, value: IntArg) -> Nu:
        return Write(self, DictForm.of(max_bars=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(bars=[]))

    def store(
        self,
        bars: ListArg[Any] | DictArg[Any, Any] = UNSET,
        x_label: StrArg = UNSET,
        y_label: StrArg = UNSET,
        color: StrArg = UNSET,
        orientation: Orientation | StrArg = UNSET,
        max_bars: IntArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {}
        if bars is not UNSET:
            if isinstance(bars, dict) and "bars" in bars:
                payload["bars"] = bars["bars"]
            else:
                payload["bars"] = bars
        if x_label is not UNSET:
            payload["x_label"] = x_label
        if y_label is not UNSET:
            payload["y_label"] = y_label
        if color is not UNSET:
            payload["color"] = color
        if orientation is not UNSET:
            payload["orientation"] = orientation
        if max_bars is not UNSET:
            payload["max_bars"] = max_bars
        return Write(self, DictForm.of(**payload))

    def append(self, category: StrArg, value: FloatArg) -> Nu:
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
    def _mount_props(cls) -> dict[str, object]:
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

    def store_points(self, points: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(points=points))

    def store_series(self, series_list: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(series=series_list))

    def store_x_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(x_label=text))

    def store_y_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(y_label=text))

    def store_color(self, value: StrArg) -> Nu:
        return Write(self, DictForm.of(color=value))

    def store_max_points(self, value: IntArg) -> Nu:
        return Write(self, DictForm.of(max_points=value))

    def store_x_format(self, value: XFormat | StrArg) -> Nu:
        return Write(self, DictForm.of(x_format=value))

    def store_show_legend(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(show_legend=flag))

    def store_show_tooltip(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(show_tooltip=flag))

    def store_palette(self, colors: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(palette=colors))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(points=[]))

    def store(
        self,
        points: ListArg[Any] | DictArg[Any, Any] = UNSET,
        series: ListArg[Any] = UNSET,
        x_label: StrArg = UNSET,
        y_label: StrArg = UNSET,
        color: StrArg = UNSET,
        max_points: IntArg = UNSET,
        x_format: XFormat | StrArg = UNSET,
        show_legend: BoolArg = UNSET,
        show_tooltip: BoolArg = UNSET,
        palette: ListArg[Any] = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not UNSET:
            # legacy: store({"points": [...]}) keeps working.
            if isinstance(points, dict) and "points" in points:
                payload["points"] = points["points"]
            else:
                payload["points"] = points
        if series is not UNSET:
            payload["series"] = series
        if x_label is not UNSET:
            payload["x_label"] = x_label
        if y_label is not UNSET:
            payload["y_label"] = y_label
        if color is not UNSET:
            payload["color"] = color
        if max_points is not UNSET:
            payload["max_points"] = max_points
        if x_format is not UNSET:
            payload["x_format"] = x_format
        if show_legend is not UNSET:
            payload["show_legend"] = show_legend
        if show_tooltip is not UNSET:
            payload["show_tooltip"] = show_tooltip
        if palette is not UNSET:
            payload["palette"] = palette
        return Write(self, DictForm.of(**payload))

    def append(self, x: FloatArg, y: FloatArg) -> Nu:
        return Append(self, x, y)

    def append_series(self, name: StrArg, x: FloatArg, y: FloatArg) -> Nu:
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
    def _mount_props(cls) -> dict[str, object]:
        return {
            "slices": list(cls.slices),
            "colors": list(cls.colors),
            "inner_radius": cls.inner_radius,
            "show_labels": cls.show_labels,
            "show_legend": cls.show_legend,
            "total_label": cls.total_label,
        }

    def store_slices(self, slices: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(slices=slices))

    def store_colors(self, colors: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(colors=colors))

    def store_inner_radius(self, value: FloatArg) -> Nu:
        return Write(self, DictForm.of(inner_radius=value))

    def store_show_labels(self, value: BoolArg) -> Nu:
        return Write(self, DictForm.of(show_labels=value))

    def store_show_legend(self, value: BoolArg) -> Nu:
        return Write(self, DictForm.of(show_legend=value))

    def store_total_label(self, value: StrArg) -> Nu:
        return Write(self, DictForm.of(total_label=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(slices=[]))

    def store(
        self,
        slices: ListArg[Any] | DictArg[Any, Any] = UNSET,
        colors: ListArg[Any] = UNSET,
        inner_radius: FloatArg = UNSET,
        show_labels: BoolArg = UNSET,
        show_legend: BoolArg = UNSET,
        total_label: StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {}
        if slices is not UNSET:
            # legacy: store({"slices": [...]}) keeps working.
            if isinstance(slices, dict) and "slices" in slices:
                payload["slices"] = slices["slices"]
            else:
                payload["slices"] = slices
        if colors is not UNSET:
            payload["colors"] = colors
        if inner_radius is not UNSET:
            payload["inner_radius"] = inner_radius
        if show_labels is not UNSET:
            payload["show_labels"] = show_labels
        if show_legend is not UNSET:
            payload["show_legend"] = show_legend
        if total_label is not UNSET:
            payload["total_label"] = total_label
        return Write(self, DictForm.of(**payload))

    def append(self, label: StrArg, value: FloatArg) -> Nu:
        return Append(self, label, value)


class Sparkline(NudleRef):
    """Display-only inline trend line. `write` (partial) and `append` (one point)."""

    color: ClassVar[str] = "#2563eb"
    height: ClassVar[int] = 32
    max_points: ClassVar[int] = 100

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "color": cls.color,
            "height": cls.height,
            "max_points": cls.max_points,
        }

    def store_points(self, points: ListArg[Any]) -> Nu:
        return Write(self, DictForm.of(points=points))

    def store_color(self, value: StrArg) -> Nu:
        return Write(self, DictForm.of(color=value))

    def store_height(self, value: IntArg) -> Nu:
        return Write(self, DictForm.of(height=value))

    def store_max_points(self, value: IntArg) -> Nu:
        return Write(self, DictForm.of(max_points=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(points=[]))

    def store(
        self,
        points: ListArg[Any] | DictArg[Any, Any] = UNSET,
        color: StrArg = UNSET,
        height: IntArg = UNSET,
        max_points: IntArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not UNSET:
            if isinstance(points, dict) and "points" in points:
                payload["points"] = points["points"]
            else:
                payload["points"] = points
        if color is not UNSET:
            payload["color"] = color
        if height is not UNSET:
            payload["height"] = height
        if max_points is not UNSET:
            payload["max_points"] = max_points
        return Write(self, DictForm.of(**payload))

    def append(self, x: FloatArg, y: FloatArg) -> Nu:
        return Append(self, x, y)


__all__ = ["AreaChart", "BarChart", "LineChart", "PieChart", "Sparkline"]
