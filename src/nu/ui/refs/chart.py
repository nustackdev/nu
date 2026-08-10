"""Chart Refs -- typed visualization sinks over series payloads.

Same directionality as other output Refs (server pushes points via
`write` / `append`; browser only renders). Grouped by shape rather
than by semantics because the payload contract is chart-specific.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nu.ui.core import Append, Ref, Write


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, DictArg, FloatArg, IntArg, ListArg, StrArg


XFormat = Literal["number", "time"]


class AreaChart(Ref):
    """Display-only area chart. `write` (partial) and `append` (one row)."""

    @classmethod
    def slot(
        cls,
        *,
        x_label: str = "",
        y_label: str = "",
        series: list[str] | None = None,
        colors: list[str] | None = None,
        stacked: bool = False,
        max_points: int = 500,
        x_format: XFormat = "number",
    ) -> Self:
        return super().slot(
            x_label=x_label,
            y_label=y_label,
            series=list(series or ["value"]),
            colors=list(colors or ["#2563eb"]),
            stacked=stacked,
            max_points=max_points,
            x_format=x_format,
        )

    def set_points(self, points: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(points=points))

    def set_series(self, names: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(series=names))

    def set_colors(self, colors: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(colors=colors))

    def set_stacked(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(stacked=flag))

    def set_x_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(x_label=text))

    def set_y_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(y_label=text))

    def set_max_points(self, value: IntArg) -> Nu:
        return Write(self, Dict.of(max_points=value))

    def set_x_format(self, value: XFormat | StrArg) -> Nu:
        return Write(self, Dict.of(x_format=value))

    def clear(self) -> Nu:
        return Write(self, Dict.of(points=[]))

    def set(
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
        return Write(self, Dict.of(**payload))

    def append(self, x: FloatArg, *ys: FloatArg) -> Nu:
        return Append(self, x, *ys)


Orientation = Literal["vertical", "horizontal"]


class BarChart(Ref):
    """Display-only chart ref. `write` (partial) and `append` (one bar)."""

    @classmethod
    def slot(
        cls,
        *,
        x_label: str = "",
        y_label: str = "",
        color: str = "#2563eb",
        orientation: Orientation = "vertical",
        max_bars: int = 200,
    ) -> Self:
        return super().slot(
            x_label=x_label,
            y_label=y_label,
            color=color,
            orientation=orientation,
            max_bars=max_bars,
        )

    def set_bars(self, bars: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(bars=bars))

    def set_x_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(x_label=text))

    def set_y_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(y_label=text))

    def set_color(self, value: StrArg) -> Nu:
        return Write(self, Dict.of(color=value))

    def set_orientation(self, value: Orientation | StrArg) -> Nu:
        return Write(self, Dict.of(orientation=value))

    def set_max_bars(self, value: IntArg) -> Nu:
        return Write(self, Dict.of(max_bars=value))

    def clear(self) -> Nu:
        return Write(self, Dict.of(bars=[]))

    def set(
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
        return Write(self, Dict.of(**payload))

    def append(self, category: StrArg, value: FloatArg) -> Nu:
        return Append(self, category, value)


class LineChart(Ref):
    """Display-only chart ref. `write` (partial) and `append` (one point or one series row)."""

    @classmethod
    def slot(
        cls,
        *,
        x_label: str = "",
        y_label: str = "",
        color: str = "#2563eb",
        max_points: int = 500,
        x_format: XFormat = "number",
        show_legend: bool = False,
        show_tooltip: bool = True,
        palette: list[str] | None = None,
    ) -> Self:
        return super().slot(
            x_label=x_label,
            y_label=y_label,
            color=color,
            max_points=max_points,
            x_format=x_format,
            show_legend=show_legend,
            show_tooltip=show_tooltip,
            palette=list(palette or []),
        )

    def set_points(self, points: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(points=points))

    def set_series(self, series_list: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(series=series_list))

    def set_x_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(x_label=text))

    def set_y_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(y_label=text))

    def set_color(self, value: StrArg) -> Nu:
        return Write(self, Dict.of(color=value))

    def set_max_points(self, value: IntArg) -> Nu:
        return Write(self, Dict.of(max_points=value))

    def set_x_format(self, value: XFormat | StrArg) -> Nu:
        return Write(self, Dict.of(x_format=value))

    def set_show_legend(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(show_legend=flag))

    def set_show_tooltip(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(show_tooltip=flag))

    def set_palette(self, colors: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(palette=colors))

    def clear(self) -> Nu:
        return Write(self, Dict.of(points=[]))

    def set(
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
        return Write(self, Dict.of(**payload))

    def append(self, x: FloatArg, y: FloatArg) -> Nu:
        return Append(self, x, y)

    def append_series(self, name: StrArg, x: FloatArg, y: FloatArg) -> Nu:
        # single dict payload so the renderer can disambiguate from the single-series [x, y] form.
        return Append(self, Dict.of(name=name, x=x, y=y))


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


class PieChart(Ref):
    """Display-only pie chart ref. `write` (partial) and `append` (one slice)."""

    @classmethod
    def slot(
        cls,
        *,
        slices: list | None = None,
        colors: list[str] | None = None,
        inner_radius: float = 0.0,
        show_labels: bool = True,
        show_legend: bool = True,
        total_label: str = "",
    ) -> Self:
        return super().slot(
            slices=list(slices or []),
            colors=list(colors or DEFAULT_COLORS),
            inner_radius=inner_radius,
            show_labels=show_labels,
            show_legend=show_legend,
            total_label=total_label,
        )

    def set_slices(self, slices: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(slices=slices))

    def set_colors(self, colors: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(colors=colors))

    def set_inner_radius(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(inner_radius=value))

    def set_show_labels(self, value: BoolArg) -> Nu:
        return Write(self, Dict.of(show_labels=value))

    def set_show_legend(self, value: BoolArg) -> Nu:
        return Write(self, Dict.of(show_legend=value))

    def set_total_label(self, value: StrArg) -> Nu:
        return Write(self, Dict.of(total_label=value))

    def clear(self) -> Nu:
        return Write(self, Dict.of(slices=[]))

    def set(
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
        return Write(self, Dict.of(**payload))

    def append(self, label: StrArg, value: FloatArg) -> Nu:
        return Append(self, label, value)


class Sparkline(Ref):
    """Display-only inline trend line. `write` (partial) and `append` (one point)."""

    @classmethod
    def slot(
        cls,
        *,
        color: str = "#2563eb",
        height: int = 32,
        max_points: int = 100,
    ) -> Self:
        return super().slot(color=color, height=height, max_points=max_points)

    def set_points(self, points: ListArg[Any]) -> Nu:
        return Write(self, Dict.of(points=points))

    def set_color(self, value: StrArg) -> Nu:
        return Write(self, Dict.of(color=value))

    def set_height(self, value: IntArg) -> Nu:
        return Write(self, Dict.of(height=value))

    def set_max_points(self, value: IntArg) -> Nu:
        return Write(self, Dict.of(max_points=value))

    def clear(self) -> Nu:
        return Write(self, Dict.of(points=[]))

    def set(
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
        return Write(self, Dict.of(**payload))

    def append(self, x: FloatArg, y: FloatArg) -> Nu:
        return Append(self, x, y)


__all__ = ["AreaChart", "BarChart", "LineChart", "PieChart", "Sparkline"]
