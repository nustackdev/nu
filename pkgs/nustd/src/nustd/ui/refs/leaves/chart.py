"""Chart Refs -- one browser node, an ECharts option, and typed builders over it.

The browser has a single chart node, ``Chart``, that draws whatever ECharts
option it holds. Every chart type here is a Python builder: its ``slot``
turns a few common settings into an option, and its data hook turns the data
you hand ``set`` into the part of the option that holds it. A new chart type
is a new builder, never new browser code.

Every chart shares one small set of interactions, defined once on ``Chart``:

- ``set(data)``          replace the data (the builder decides its shape)
- ``set(option=...)``    replace the whole option, drawn from scratch
- ``merge(option)``      a partial option, merged the way ECharts merges
- ``append(points, series=0)``  push points onto one series, keeping the
                         newest ``max_points``. A series is a position or a
                         name; an unknown name adds a series styled like the
                         last one. Points are ECharts data items as the
                         chart's series takes them ([x, y], a bare y,
                         {name, value}, ...).
- ``clear(series=None)`` empty one series, or all of them
- ``on_click()``         a data item clicked: ``{event, series,
                         series_index, name, index, value}``

Anything a builder does not expose (a log axis, a second y axis, mark lines,
a geo map) goes through the raw option: ``option=`` on any builder's slot is
merged over what it builds, ``merge`` changes it live, and ``Chart.slot(
option=...)`` takes an option whole. Formatters are ECharts template strings
(``"{value} ms"``, ``"{b}: {d}%"``, ``"{HH}:{mm}"`` on a time axis), never
code. A color may be a kit token, ``"var(--chart-3)"``, resolved in the
browser per theme.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Changed, Send, Write

from .base import LeafRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import Arg, DictArg, IntArg, ListArg, StrArg


__all__ = [
    "AreaChart",
    "BarChart",
    "BoxplotChart",
    "CandlestickChart",
    "Chart",
    "FunnelChart",
    "GaugeChart",
    "HeatmapChart",
    "Histogram",
    "LineChart",
    "PieChart",
    "RadarChart",
    "SankeyChart",
    "ScatterChart",
    "Sparkline",
    "SunburstChart",
    "TreemapChart",
    "merge_option",
]


Option = dict[str, Any]
XType = Literal["category", "value", "time"]


# --- option merge -------------------------------------------------------------
#
# The same rules the browser applies to a `merge` (ui-kit lib/chart/option):
# objects merge key by key, a list of components merges item by item (same
# id, else same name, else the first slot not yet claimed), any other value
# is replaced.


def _is_components(v: object) -> bool:
    return isinstance(v, list) and len(v) > 0 and all(isinstance(e, Mapping) for e in v)


def _placements(items: list, patch: list) -> list[int]:
    """Where each patch item lands: same id, then same name, then the first unclaimed slot. -1 appends."""
    at = [-1] * len(patch)
    taken: set[int] = set()

    def first(pred: Any) -> int:
        return next((i for i, e in enumerate(items) if i not in taken and pred(e)), -1)

    passes = (
        lambda p: p.get("id") is not None,
        lambda p: p.get("id") is None and p.get("name") is not None,
        lambda p: p.get("id") is None,
    )
    keys = (
        lambda p: lambda e: isinstance(e, Mapping) and e.get("id") == p["id"],
        lambda p: lambda e: isinstance(e, Mapping) and e.get("name") == p["name"],
        lambda p: lambda e: True,
    )
    for applies, key in zip(passes, keys, strict=True):
        for k, item in enumerate(patch):
            if at[k] < 0 and applies(item):
                i = first(key(item))
                if i >= 0:
                    at[k] = i
                    taken.add(i)
    return at


def _merge_value(base: object, patch: object) -> object:
    if isinstance(base, Mapping) and isinstance(patch, Mapping):
        return {**base, **{k: _merge_value(base.get(k), v) for k, v in patch.items()}}
    return patch


def _merge_list(base: list, patch: list) -> list:
    out = list(base)
    for item, at in zip(patch, _placements(base, patch), strict=True):
        if at >= 0:
            out[at] = _merge_value(out[at], item)
        else:
            out.append(item)
    return out


def merge_option(base: Mapping[str, Any], patch: Mapping[str, Any]) -> Option:
    """``patch`` over ``base`` with ECharts setOption merge rules. Neither is changed."""
    out: Option = dict(base)
    for key, value in patch.items():
        cur = base.get(key)
        cur_list = cur if _is_components(cur) else [cur] if isinstance(cur, Mapping) else None
        if _is_components(value) and cur_list is not None:
            out[key] = _merge_list(cur_list, value)
        elif isinstance(value, Mapping) and _is_components(cur):
            out[key] = _merge_list(cur, [value])
        else:
            out[key] = _merge_value(cur, value)
    return out


# --- the interactions ---------------------------------------------------------


class _Merge(Send):
    """A partial option, merged in the browser."""

    def _frame_op(self) -> object:
        return "merge"

    def _frame_payload(self, values: list[object]) -> object:
        return values[0]


class _SetData(Send):
    """New data, turned into an option patch by the chart's own data hook."""

    def _frame_op(self) -> object:
        return "merge"

    def _frame_payload(self, values: list[object]) -> object:
        ref = self._children[0]
        return type(ref)._data(values[0], ref._declared())


class _Append(Send):
    _payload_fields = ("points", "series")

    def _frame_op(self) -> object:
        return "append"


class _Clear(Send):
    _payload_fields = ("series",)

    def _frame_op(self) -> object:
        return "clear"


# --- data shapes ----------------------------------------------------------------


def _series_list(option: Mapping[str, Any]) -> list[Option]:
    s = option.get("series")
    if isinstance(s, Mapping):
        return [dict(s)]
    return [dict(e) for e in s or () if isinstance(e, Mapping)]


def _like_last(option: Mapping[str, Any], name: str) -> Option:
    """A new series named ``name``, styled like the option's last one."""
    series = _series_list(option)
    style = {
        k: v
        for k, v in (series[-1] if series else {"type": "line"}).items()
        if k not in ("data", "id", "name")
    }
    return {**style, "name": name}


def _by_name(
    data: Mapping[str, Any], option: Mapping[str, Any], convert: Any = list
) -> list[Option]:
    """One patch item per series a mapping names, and an empty one per declared series it leaves out."""
    declared = [s.get("name") for s in _series_list(option)]
    items: list[Option] = []
    for name, points in data.items():
        item = {"name": str(name), "data": convert(points)}
        items.append(item if str(name) in declared else {**_like_last(option, str(name)), **item})
    items.extend(
        {"name": n, "data": []}
        for n in declared
        if n is not None and n not in {str(k) for k in data}
    )
    return items


def _rows(data: Any) -> list:
    return list(data) if isinstance(data, Sequence) and not isinstance(data, str) else []


def _cartesian(data: Any, option: Mapping[str, Any]) -> Option:
    """Line, area, bar and scatter data.

    A mapping is ``{series name: points}``. A list of rows each one longer
    than the series count, ``[x, y1, y2, ...]``, fills the declared series in
    order. Anything else is the first series' data: ``[x, y]`` pairs or bare
    y values.
    """
    if isinstance(data, Mapping):
        return {"series": _by_name(data, option)}
    rows = _rows(data)
    series = _series_list(option)
    wide = len(series) > 1 and all(
        isinstance(r, Sequence) and not isinstance(r, str) and len(r) == len(series) + 1
        for r in rows
    )
    if rows and wide:
        return {"series": [{"data": [[r[0], r[k + 1]] for r in rows]} for k in range(len(series))]}
    return {"series": [{"data": rows}]}


def _named_values(data: Any) -> list[Option]:
    """Pie and funnel slices: ``{name: value}``, ``[name, value]`` pairs, ``{name, value}`` maps, or bare values."""
    if isinstance(data, Mapping):
        return [{"name": str(k), "value": v} for k, v in data.items()]
    out: list[Option] = []
    for i, d in enumerate(_rows(data)):
        if isinstance(d, Mapping):
            item = dict(d)
            if "name" not in item and "label" in item:
                item["name"] = str(item.pop("label"))
            out.append(item)
        elif isinstance(d, Sequence) and not isinstance(d, str) and len(d) == 2:
            out.append({"name": str(d[0]), "value": d[1]})
        else:
            out.append({"name": str(i), "value": d})
    return out


def _tree(data: Any) -> list[Option]:
    """Treemap and sunburst nodes. ``{"A": {"a1": 3}, "B": 5}`` nests by key; a list is nodes as is."""
    if isinstance(data, Mapping):
        return [
            {"name": str(k), "children": _tree(v)}
            if isinstance(v, Mapping)
            else {"name": str(k), "value": v}
            for k, v in data.items()
        ]
    return [dict(d) if isinstance(d, Mapping) else d for d in _rows(data)]


def _num(v: object) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


# Bin ranges read "0-10" with an en dash: an en dash, spelled out so the source stays ASCII.
_DASH = chr(0x2013)


def _label(x: float, step: float = 0.0) -> str:
    # As many decimals as the step between labels needs, and no more.
    places = max(0, 1 - math.floor(math.log10(step))) if step > 0 else 0
    return f"{x:.{min(places, 6)}f}" if step > 0 else f"{x:.4g}"


def _quantile(sorted_vals: list[float], q: float) -> float:
    pos = (len(sorted_vals) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


# --- the base -------------------------------------------------------------------


class Chart(LeafRef):
    """A chart drawn from an ECharts option. The base every typed chart builds on.

    ``Chart.slot(option={...})`` draws the option as given: any series,
    component or setting ECharts has. The typed charts below build the option
    for you.

    Args:
        option: The ECharts option.
        height: Height in px.
        max_points: How many points a series keeps under ``append``.
    """

    _wire_type: ClassVar[str] = "Chart"

    def __init__(
        self,
        address: object,
        *,
        parent_ref: Any = None,
        owner_shape: Any = None,
        props: Mapping[str, object] | None = None,
    ) -> None:
        # A chart built alone still carries its slot's option on the chain: the
        # browser has nothing else to draw it from.
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, props=props or {})

    @classmethod
    def slot(
        cls, *, option: Mapping[str, Any] | None = None, height: int = 256, max_points: int = 500
    ) -> Self:
        return cls._slot(dict(option or {}), height=height, max_points=max_points)

    @classmethod
    def _slot(cls, option: Option, *, height: int, max_points: int, **spec: Any) -> Self:
        # `spec` is what the data hook needs that the option does not say (a
        # histogram's bin count). The browser ignores it.
        props: dict[str, object] = {"option": option, "height": height, "max_points": max_points}
        if spec:
            props["spec"] = spec
        return LeafRef.slot.__func__(cls, **props)  # type: ignore[attr-defined]

    def _declared(self) -> dict[str, Any]:
        """The props this chart's slot declared."""
        props = self._payload.get("props")
        return dict(props) if props is not None else dict(type(self).slot().props)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        """The option patch ``set(data)`` ships. Here: a list is the first series' data, a mapping is series by name."""
        option = props.get("option") or {}
        if isinstance(data, Mapping):
            return {"series": _by_name(data, option)}
        return {"series": [{"data": _rows(data)}]}

    # --- server -> browser ---------------------------------------------------

    def set(self, data: Arg = UNSET, *, option: DictArg[str, Any] = UNSET) -> Nu:
        """Replace the data, or with ``option=`` the whole option (drawn from scratch)."""
        if (data is UNSET) == (option is UNSET):
            raise TypeError("Chart.set takes data or option=, exactly one")
        if option is not UNSET:
            return Write(self, Dict.of(option=option))
        return _SetData(self, data)

    def merge(self, option: DictArg[str, Any]) -> Nu:
        """Merge a partial option, the way ECharts' setOption merges."""
        return _Merge(self, option)

    def append(self, points: ListArg[Any], series: StrArg | IntArg = 0) -> Nu:
        """Push points onto one series, keeping the newest ``max_points``."""
        return _Append(self, points, series)

    def clear(self, series: StrArg | IntArg | None = None) -> Nu:
        """Empty one series' data (a position or a name), or every series'."""
        return _Clear(self, series)

    # --- browser -> server ---------------------------------------------------

    def on_click(self) -> Changed:
        """``{event, series, series_index, name, index, value}``: a data item clicked."""
        return Changed(self, "click")


# --- shared option parts ----------------------------------------------------------


def _common(
    *,
    title: str,
    tooltip: bool,
    trigger: str,
    legend: bool,
    colors: Sequence[str] | None,
    tooltip_format: str = "",
) -> Option:
    o: Option = {"tooltip": {"show": tooltip, "trigger": trigger, "confine": True}}
    if tooltip_format:
        o["tooltip"]["formatter"] = tooltip_format
    if trigger == "axis":
        o["tooltip"]["axisPointer"] = {"type": "line"}
    if title:
        o["title"] = [{"id": "title", "text": title}]
    if legend:
        # Under the title when there is one, so a long legend never runs into it.
        o["legend"] = {"type": "scroll", "top": 30 if title else 0, "left": 0}
    if colors:
        o["color"] = list(colors)
    return o


def _grid(*, title: str, legend: bool, x_label: str, y_label: str) -> Option:
    # Axis labels and names stay inside the chart on their own (ECharts 6
    # shrinks the grid to its outer bounds), so only the header is reserved.
    top = 12 + (30 if title else 0) + (24 if legend else 0) + (12 if y_label else 0)
    return {"left": 4, "right": 16, "top": top, "bottom": 4 if not x_label else 8}


def _axis(
    kind: str, *, label: str, fmt: str, lo: float | None = None, hi: float | None = None
) -> Option:
    a: Option = {"type": kind}
    if kind != "category":
        a["scale"] = True
    if label:
        a["name"] = label
    if fmt:
        a["axisLabel"] = {"formatter": fmt}
    if lo is not None:
        a["min"] = lo
    if hi is not None:
        a["max"] = hi
    return a


def _x_name(axis: Option) -> Option:
    if "name" in axis:
        axis.update(nameLocation="middle", nameGap=28)
    return axis


def _finish(
    cls: type[Chart], option: Option, overrides: Mapping[str, Any] | None, **slot: Any
) -> Any:
    return cls._slot(merge_option(option, overrides or {}), **slot)


def _auto_legend(legend: bool | None, n: int) -> bool:
    return n > 1 if legend is None else legend


# --- cartesian ------------------------------------------------------------------


class LineChart(Chart):
    """Lines over an x axis, one per series name.

    ``set`` takes ``{name: [[x, y], ...]}``, ``[[x, y], ...]`` for the first
    series, bare y values, or rows ``[x, y1, y2, ...]`` across the series in
    order. ``append([[x, y]], "cpu")`` streams a point.

    Args:
        series: Series names, in palette order.
        x_type: ``"value"`` (numbers), ``"time"`` (epoch ms or ISO strings) or
            ``"category"`` (labels).
        smooth: Curved lines.
        area: Fill under each line.
        stack: Stack the series.
        step: Step lines.
        symbols: Show a dot per point.
        x_format, y_format: Axis label templates, eg ``"{HH}:{mm}"``, ``"{value} ms"``.
        y_min, y_max: Fix the y range; otherwise it fits the data.
        legend: Show the legend. Default: when there is more than one series.
        tooltip_format: A tooltip template; otherwise the default list.
        colors: Palette override, in series order.
        option: Raw ECharts option merged over the built one.
    """

    _area: ClassVar[bool] = False

    @classmethod
    def slot(
        cls,
        series: Sequence[str] = ("value",),
        *,
        title: str = "",
        x_type: XType = "value",
        smooth: bool = False,
        area: bool | None = None,
        stack: bool = False,
        step: bool = False,
        symbols: bool = False,
        x_label: str = "",
        y_label: str = "",
        x_format: str = "",
        y_format: str = "",
        y_min: float | None = None,
        y_max: float | None = None,
        legend: bool | None = None,
        tooltip: bool = True,
        tooltip_format: str = "",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        fill = cls._area if area is None else area
        show_legend = _auto_legend(legend, len(series))
        line: Option = {"type": "line", "showSymbol": symbols, "smooth": smooth}
        if fill:
            line["areaStyle"] = {"opacity": 0.18 if not stack else 0.6}
        if stack:
            line["stack"] = "total"
        if step:
            line["step"] = "end"
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="axis",
            legend=show_legend,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        o.update(
            grid=_grid(title=title, legend=show_legend, x_label=x_label, y_label=y_label),
            xAxis=_x_name(
                _axis(x_type, label=x_label, fmt=x_format)
                | ({"boundaryGap": False} if x_type == "category" else {})
            ),
            yAxis=_axis("value", label=y_label, fmt=y_format, lo=y_min, hi=y_max),
            series=[{**line, "name": name, "data": []} for name in series],
        )
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        return _cartesian(data, props.get("option") or {})


class AreaChart(LineChart):
    """A line chart filled underneath. ``stack=True`` for a stacked area. Same data as ``LineChart``."""

    _area: ClassVar[bool] = True


class BarChart(Chart):
    """Bars per category, one bar series per name.

    ``set`` takes ``{name: [[category, value], ...]}``, ``[[category, value],
    ...]`` for the first series, ``{category: value}`` for a single series, or
    rows ``[category, v1, v2, ...]`` across the series. ``append([["Mon",
    3]])`` adds a bar.

    Args:
        series: Series names.
        stack: Stack the series.
        horizontal: Bars run left to right, categories down the side.
        x_type: The category side's axis type; ``"time"`` or ``"value"`` for
            bars over a continuous axis.
        value_format: Value axis label template.
        labels: Print each bar's value on it.
    """

    @classmethod
    def slot(
        cls,
        series: Sequence[str] = ("value",),
        *,
        title: str = "",
        stack: bool = False,
        horizontal: bool = False,
        x_type: XType = "category",
        labels: bool = False,
        x_label: str = "",
        y_label: str = "",
        value_format: str = "",
        y_min: float | None = None,
        y_max: float | None = None,
        legend: bool | None = None,
        tooltip: bool = True,
        tooltip_format: str = "",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        show_legend = _auto_legend(legend, len(series))
        bar: Option = {"type": "bar"}
        if stack:
            bar["stack"] = "total"
        if labels:
            bar["label"] = {"show": True, "position": "right" if horizontal else "top"}
            if stack:
                # Inside a fill: the ground color reads on every slot, both themes.
                bar["label"] = {"show": True, "position": "inside", "color": "var(--bg-canvas)"}
        if horizontal:
            # Data stays [category, value] either way round: encode says
            # which dimension each axis reads, so append needs no swap.
            bar["encode"] = {"x": 1, "y": 0}
        radius = [0, 2, 2, 0] if horizontal else [2, 2, 0, 0]
        if not stack:
            bar["itemStyle"] = {"borderRadius": radius}
        cat = _axis(x_type, label=x_label, fmt="")
        val = _axis("value", label=y_label, fmt=value_format, lo=y_min, hi=y_max)
        val.pop("scale", None)
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="axis",
            legend=show_legend,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        o["tooltip"]["axisPointer"] = {"type": "shadow"}
        o.update(
            grid=_grid(title=title, legend=show_legend, x_label=x_label, y_label=y_label),
            xAxis=val if horizontal else _x_name(cat),
            yAxis=cat if horizontal else val,
            series=[{**bar, "name": name, "data": []} for name in series],
        )
        if horizontal:
            o["yAxis"]["inverse"] = True
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        option = props.get("option") or {}
        if isinstance(data, Mapping) and not any(
            isinstance(v, (list, tuple)) for v in data.values()
        ):
            data = [[k, v] for k, v in data.items()]
        rows = _rows(data)
        if rows and all(_num(r) is not None for r in rows):
            # Bare values: label them by position, so a horizontal chart (which
            # reads [category, value]) draws them too.
            rows = [[str(i), r] for i, r in enumerate(rows)]
            data = rows
        return _cartesian(data, option)


class ScatterChart(Chart):
    """Points on two value axes, one color per series name.

    ``set`` takes ``{name: [[x, y], ...]}`` or ``[[x, y], ...]`` for the first
    series. A third value, ``[x, y, size]``, sets the dot size when ``sized``.

    Args:
        symbol_size: Dot size in px.
        sized: Read each point's third value as its dot size.
    """

    @classmethod
    def slot(
        cls,
        series: Sequence[str] = ("value",),
        *,
        title: str = "",
        symbol_size: float = 8,
        sized: bool = False,
        x_type: XType = "value",
        x_label: str = "",
        y_label: str = "",
        x_format: str = "",
        y_format: str = "",
        legend: bool | None = None,
        tooltip: bool = True,
        tooltip_format: str = "",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        show_legend = _auto_legend(legend, len(series))
        dot: Option = {"type": "scatter", "symbolSize": symbol_size}
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="item",
            legend=show_legend,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        o.update(
            grid=_grid(title=title, legend=show_legend, x_label=x_label, y_label=y_label),
            xAxis=_x_name(_axis(x_type, label=x_label, fmt=x_format)),
            yAxis=_axis("value", label=y_label, fmt=y_format),
            series=[{**dot, "name": name, "data": []} for name in series],
        )
        if sized:
            # Point size from the data: a visual map over the third value, no
            # color channel, so the palette still tells the series apart.
            o["visualMap"] = {
                "show": False,
                "dimension": 2,
                "min": 0,
                "max": 1,
                "inRange": {"symbolSize": [symbol_size / 2, symbol_size * 4]},
            }
        return _finish(cls, o, option, height=height, max_points=max_points, sized=sized)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        patch = _cartesian(data, props.get("option") or {})
        if (props.get("spec") or {}).get("sized"):
            sizes = [
                _num(p[2])
                for s in patch["series"]
                for p in s.get("data", [])
                if isinstance(p, Sequence) and len(p) > 2
            ]
            sizes = [v for v in sizes if v is not None]
            if sizes:
                patch["visualMap"] = {"min": min(sizes), "max": max(sizes)}
        return patch


class Histogram(Chart):
    """How values spread: counts per bin, binned in Python on ``set``.

    ``set`` takes a list of numbers, or ``{name: numbers}`` for overlaid
    series sharing one set of bins. ``append`` adds pre-binned bars only; to
    re-bin, ``set`` again.

    Args:
        bins: How many bins.
        range: ``(low, high)`` for the bins; otherwise the data's extent.
    """

    @classmethod
    def slot(
        cls,
        series: Sequence[str] = ("count",),
        *,
        title: str = "",
        bins: int = 10,
        range: tuple[float, float] | None = None,
        x_label: str = "",
        y_label: str = "",
        legend: bool | None = None,
        tooltip: bool = True,
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        show_legend = _auto_legend(legend, len(series))
        o = _common(title=title, tooltip=tooltip, trigger="axis", legend=show_legend, colors=colors)
        o["tooltip"]["axisPointer"] = {"type": "shadow"}
        val = _axis("value", label=y_label, fmt="")
        val.pop("scale", None)
        o.update(
            grid=_grid(title=title, legend=show_legend, x_label=x_label, y_label=y_label),
            xAxis=_x_name(_axis("category", label=x_label, fmt="") | {"data": []}),
            yAxis=val,
            series=[{"type": "bar", "name": n, "barCategoryGap": "4%", "data": []} for n in series],
        )
        spec = {"bins": max(1, int(bins)), "range": list(range) if range else None}
        return _finish(cls, o, option, height=height, max_points=max_points, **spec)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        option = props.get("option") or {}
        spec = props.get("spec") or {}
        bins = int(spec.get("bins") or 10)
        named = data if isinstance(data, Mapping) else {None: data}
        values = {k: [x for x in map(_num, _rows(v)) if x is not None] for k, v in named.items()}
        everything = [x for vs in values.values() for x in vs]
        rng = spec.get("range")
        lo = float(rng[0]) if rng else min(everything, default=0.0)
        hi = float(rng[1]) if rng else max(everything, default=1.0)
        if hi <= lo:
            hi = lo + 1
        width = (hi - lo) / bins
        labels = [
            f"{_label(lo + i * width, width)}{_DASH}{_label(lo + (i + 1) * width, width)}"
            for i in range(bins)
        ]

        def counts(vs: list[float]) -> list[int]:
            out = [0] * bins
            for v in vs:
                if lo <= v <= hi:
                    out[min(int((v - lo) / width), bins - 1)] += 1
            return out

        if None in values:
            series: list[Option] = [{"data": counts(values[None])}]
        else:
            series = _by_name(
                {k: counts(v) for k, v in values.items()}, option, convert=lambda c: c
            )
        return {"xAxis": {"data": labels}, "series": series}


class CandlestickChart(Chart):
    """Open, close, low and high per period.

    ``set`` takes rows ``[x, open, close, low, high]``; ``append`` takes the
    same rows. Up periods draw in the ok tone, down in the danger tone.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        name: str = "price",
        x_type: XType = "category",
        x_label: str = "",
        y_label: str = "",
        x_format: str = "",
        y_format: str = "",
        tooltip: bool = True,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(title=title, tooltip=tooltip, trigger="axis", legend=False, colors=None)
        o.update(
            grid=_grid(title=title, legend=False, x_label=x_label, y_label=y_label),
            xAxis=_x_name(_axis(x_type, label=x_label, fmt=x_format)),
            yAxis=_axis("value", label=y_label, fmt=y_format),
            # Rows stay [x, open, close, low, high] on the wire: encode names
            # the dimensions, so set and append take the same row.
            series=[
                {
                    "type": "candlestick",
                    "name": name,
                    "encode": {"x": 0, "y": [1, 2, 3, 4]},
                    "data": [],
                }
            ],
        )
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        return {"series": [{"data": [list(r) for r in _rows(data)]}]}


class BoxplotChart(Chart):
    """The spread of each category's samples: whiskers at min and max, box at the quartiles.

    ``set`` takes ``{category: samples}``; the five numbers are worked out in
    Python. Precomputed ``[min, q1, median, q3, max]`` rows go through
    ``merge``.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        name: str = "spread",
        horizontal: bool = False,
        x_label: str = "",
        y_label: str = "",
        value_format: str = "",
        tooltip: bool = True,
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(title=title, tooltip=tooltip, trigger="item", legend=False, colors=colors)
        cat = _axis("category", label=x_label, fmt="") | {"data": []}
        val = _axis("value", label=y_label, fmt=value_format)
        o.update(
            grid=_grid(title=title, legend=False, x_label=x_label, y_label=y_label),
            xAxis=val if horizontal else _x_name(cat),
            yAxis=cat if horizontal else val,
            series=[{"type": "boxplot", "name": name, "data": []}],
        )
        return _finish(cls, o, option, height=height, max_points=max_points, horizontal=horizontal)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        named = (
            data if isinstance(data, Mapping) else {str(i): v for i, v in enumerate(_rows(data))}
        )
        cats: list[str] = []
        boxes: list[list[float]] = []
        for k, samples in named.items():
            vals = sorted(x for x in map(_num, _rows(samples)) if x is not None)
            if not vals:
                continue
            cats.append(str(k))
            boxes.append(
                [
                    vals[0],
                    _quantile(vals, 0.25),
                    _quantile(vals, 0.5),
                    _quantile(vals, 0.75),
                    vals[-1],
                ]
            )
        axis = "yAxis" if (props.get("spec") or {}).get("horizontal") else "xAxis"
        return {axis: {"data": cats}, "series": [{"data": boxes}]}


class HeatmapChart(Chart):
    """A grid of cells colored by value, on the sequential ramp.

    ``set`` takes ``[[x, y, value], ...]`` (x and y as labels or positions) or
    a matrix, rows along y. Labels not declared are added in the order they
    come. The color scale fits the data on every ``set``.

    Args:
        x, y: The labels along each axis.
        labels: Print each cell's value.
        legend: Show the color scale.
        value_format: Cell label and tooltip value template.
    """

    @classmethod
    def slot(
        cls,
        x: Sequence[str] = (),
        y: Sequence[str] = (),
        *,
        title: str = "",
        labels: bool = False,
        legend: bool = True,
        x_label: str = "",
        y_label: str = "",
        value_format: str = "",
        tooltip: bool = True,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(title=title, tooltip=tooltip, trigger="item", legend=False, colors=None)
        grid = _grid(title=title, legend=False, x_label=x_label, y_label=y_label)
        if legend:
            grid["bottom"] = 44
        cell: Option = {"type": "heatmap", "name": title or "value", "data": []}
        if labels:
            cell["label"] = {"show": True, **({"formatter": value_format} if value_format else {})}
        o.update(
            grid=grid,
            xAxis=_x_name(
                _axis("category", label=x_label, fmt="")
                | {"data": list(x), "splitArea": {"show": False}}
            ),
            yAxis=_axis("category", label=y_label, fmt="") | {"data": list(y)},
            visualMap={
                "show": legend,
                "min": 0,
                "max": 1,
                "calculable": False,
                "orient": "horizontal",
                "left": "center",
                "bottom": 0,
                "itemHeight": 120,
                "itemWidth": 10,
            },
            series=[cell],
        )
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        option = props.get("option") or {}
        xs = list((option.get("xAxis") or {}).get("data") or [])
        ys = list((option.get("yAxis") or {}).get("data") or [])
        rows = _rows(data)
        cells: list[list[Any]] = []
        matrix = (
            rows
            and all(
                isinstance(r, Sequence)
                and not isinstance(r, str)
                and all(_num(v) is not None for v in r)
                for r in rows
            )
            and not all(len(r) == 3 for r in rows)
        )
        if matrix:
            cells = [[i, j, v] for j, r in enumerate(rows) for i, v in enumerate(r)]
        else:
            for r in rows:
                if not (isinstance(r, Sequence) and len(r) == 3):
                    continue
                cx, cy, v = r
                if isinstance(cx, str):
                    if cx not in xs:
                        xs.append(cx)
                    cx = xs.index(cx)
                if isinstance(cy, str):
                    if cy not in ys:
                        ys.append(cy)
                    cy = ys.index(cy)
                cells.append([cx, cy, v])
        need_x = max((c[0] for c in cells), default=-1) + 1
        need_y = max((c[1] for c in cells), default=-1) + 1
        xs += [str(i) for i in range(len(xs), need_x)]
        ys += [str(i) for i in range(len(ys), need_y)]
        values = [v for v in (_num(c[2]) for c in cells) if v is not None]
        lo, hi = (min(values), max(values)) if values else (0.0, 1.0)
        return {
            "xAxis": {"data": xs},
            "yAxis": {"data": ys},
            "visualMap": {"min": lo, "max": hi if hi > lo else lo + 1},
            "series": [{"data": cells}],
        }


# --- part of a whole ----------------------------------------------------------------


class PieChart(Chart):
    """Slices of a whole.

    ``set`` takes ``{name: value}``, ``[[name, value], ...]``, ``[{name,
    value}, ...]`` or bare values. ``append([{"name": "Fish", "value": 3}])``
    adds a slice.

    Args:
        donut: Cut out the middle.
        total_label: With a donut, the total goes in the middle under this
            caption (worked out on every ``set``).
        labels: Label each slice.
        label_format: Slice label template, eg ``"{b}: {d}%"``.
        legend: Show the legend.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        donut: bool = False,
        total_label: str = "",
        labels: bool = True,
        label_format: str = "{b}",
        legend: bool = False,
        tooltip: bool = True,
        tooltip_format: str = "{b}: {c} ({d}%)",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="item",
            legend=legend,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        if legend:
            o["legend"] = {"type": "scroll", "bottom": 0, "left": "center"}
        # Room for a title above and a legend below, the pie centered between.
        cy = 50 + (6 if title else 0) - (6 if legend else 0)
        outer = "72%" if title or legend else "78%"
        pie: Option = {
            "type": "pie",
            "name": title or "share",
            "radius": ["52%", outer] if donut else [0, outer],
            "center": ["50%", f"{cy}%"],
            "avoidLabelOverlap": True,
            "label": {"show": labels, "formatter": label_format},
            "data": [],
        }
        o["series"] = [pie]
        if donut and total_label:
            o.setdefault("title", [])
            o["title"].append(
                {
                    "id": "total",
                    "text": "",
                    "subtext": total_label,
                    # The anchor, not "center": a centered box whose text is
                    # centered on its left edge again lands half a width left.
                    "left": "50%",
                    "top": f"{cy - 7}%",
                    "itemGap": 2,
                    "textStyle": {"fontSize": 18},
                    "textAlign": "center",
                }
            )
        return _finish(
            cls, o, option, height=height, max_points=max_points, total=bool(donut and total_label)
        )

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        slices = _named_values(data)
        patch: Option = {"series": [{"data": slices}]}
        if (props.get("spec") or {}).get("total"):
            total = sum(v for v in (_num(s.get("value")) for s in slices) if v is not None)
            patch["title"] = [{"id": "total", "text": _label(total)}]
        return patch


class FunnelChart(Chart):
    """Stages narrowing down. Same data as ``PieChart``.

    Args:
        sort: ``"descending"`` (widest first), ``"ascending"`` or ``"none"`` (as given).
        label_format: Stage label template.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        sort: Literal["descending", "ascending", "none"] = "descending",
        labels: bool = True,
        label_format: str = "{b}",
        legend: bool = False,
        tooltip: bool = True,
        tooltip_format: str = "{b}: {c}",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="item",
            legend=legend,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        o["series"] = [
            {
                "type": "funnel",
                "name": title or "stages",
                "sort": sort,
                "top": 36 if title or legend else 8,
                "bottom": 8,
                "left": "10%",
                "width": "80%",
                "gap": 2,
                "label": {"show": labels, "position": "inside", "formatter": label_format},
                "data": [],
            }
        ]
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        return {"series": [{"data": _named_values(data)}]}


class TreemapChart(Chart):
    """Nested rectangles sized by value.

    ``set`` takes nested ``{name: value or {child: ...}}`` or ECharts nodes
    ``[{name, value, children}]``.

    Args:
        breadcrumb: Show the path when drilled in.
        labels: Label each tile.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        breadcrumb: bool = False,
        labels: bool = True,
        tooltip: bool = True,
        tooltip_format: str = "{b}: {c}",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="item",
            legend=False,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        o["series"] = [
            {
                "type": "treemap",
                "name": title or "all",
                "top": 32 if title else 0,
                "left": 0,
                "right": 0,
                "bottom": 28 if breadcrumb else 0,
                "roam": False,
                "nodeClick": "zoomToNode" if breadcrumb else False,
                "breadcrumb": {"show": breadcrumb},
                "label": {"show": labels},
                "data": [],
            }
        ]
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        return {"series": [{"data": _tree(data)}]}


class SunburstChart(Chart):
    """Nested rings sized by value. Same data as ``TreemapChart``."""

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        labels: bool = True,
        tooltip: bool = True,
        tooltip_format: str = "{b}: {c}",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(
            title=title,
            tooltip=tooltip,
            trigger="item",
            legend=False,
            colors=colors,
            tooltip_format=tooltip_format,
        )
        o["series"] = [
            {
                "type": "sunburst",
                "name": title or "all",
                "radius": ["14%", "92%"],
                "center": ["50%", "54%" if title else "50%"],
                "label": {"show": labels, "rotate": "radial", "minAngle": 12},
                "data": [],
            }
        ]
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        return {"series": [{"data": _tree(data)}]}


# --- flows and measures ----------------------------------------------------------------


class SankeyChart(Chart):
    """Flows between nodes, widths by value.

    ``set`` takes links ``[[source, target, value], ...]`` (or ``{source,
    target, value}`` maps); the nodes are the names they mention. ``append``
    does not apply; ``set`` again.

    Args:
        vertical: Flow top to bottom instead of left to right.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        vertical: bool = False,
        labels: bool = True,
        tooltip: bool = True,
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(title=title, tooltip=tooltip, trigger="item", legend=False, colors=colors)
        o["series"] = [
            {
                "type": "sankey",
                "name": title or "flow",
                "orient": "vertical" if vertical else "horizontal",
                "top": 36 if title else 8,
                "bottom": 8,
                "left": 8,
                "right": 8 if vertical else 80,
                "nodeGap": 10,
                "nodeWidth": 12,
                "emphasis": {"focus": "adjacency"},
                "label": {"show": labels},
                "data": [],
                "links": [],
            }
        ]
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        links: list[Option] = []
        for r in _rows(data):
            if isinstance(r, Mapping):
                links.append(
                    {
                        "source": str(r["source"]),
                        "target": str(r["target"]),
                        "value": r.get("value", 1),
                    }
                )
            elif isinstance(r, Sequence) and len(r) >= 2:
                links.append(
                    {"source": str(r[0]), "target": str(r[1]), "value": r[2] if len(r) > 2 else 1}
                )
        names: list[str] = []
        for link in links:
            for end in (link["source"], link["target"]):
                if end not in names:
                    names.append(end)
        return {"series": [{"data": [{"name": n} for n in names], "links": links}]}


class RadarChart(Chart):
    """Several measures around a circle, one shape per item.

    ``set`` takes ``{item name: [one value per indicator]}`` or a single list
    of values.

    Args:
        indicators: The measures, as names or ``(name, max)`` pairs.
        area: Fill each shape.
        circle: A round grid instead of a polygon.
    """

    @classmethod
    def slot(
        cls,
        indicators: Sequence[str | tuple[str, float]] = (),
        *,
        title: str = "",
        area: bool = True,
        circle: bool = False,
        legend: bool = True,
        tooltip: bool = True,
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(title=title, tooltip=tooltip, trigger="item", legend=legend, colors=colors)
        if legend:
            o["legend"] = {"type": "scroll", "bottom": 0, "left": "center"}
        o["radar"] = {
            "indicator": [
                {"name": i} if isinstance(i, str) else {"name": str(i[0]), "max": i[1]}
                for i in indicators
            ],
            "shape": "circle" if circle else "polygon",
            "radius": "66%",
            "center": ["50%", "50%"],
        }
        line: Option = {"type": "radar", "name": title or "measures", "symbolSize": 4, "data": []}
        if area:
            line["areaStyle"] = {"opacity": 0.15}
        o["series"] = [line]
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        if isinstance(data, Mapping):
            items = [{"name": str(k), "value": list(v)} for k, v in data.items()]
        else:
            items = [{"name": "value", "value": _rows(data)}]
        return {"series": [{"data": items}]}


class GaugeChart(Chart):
    """One value on an arc, between ``min`` and ``max``.

    ``set`` takes a number (or ``{name: value}`` for several needles).
    For the small inline gauge use ``GaugeRef``; this is the ECharts one.

    Args:
        name: The caption under the value.
        value_format: The value's template, eg ``"{value}%"``.
    """

    @classmethod
    def slot(
        cls,
        *,
        title: str = "",
        name: str = "",
        min: float = 0,
        max: float = 100,
        value_format: str = "{value}",
        colors: Sequence[str] | None = None,
        height: int = 256,
        max_points: int = 500,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        o = _common(title=title, tooltip=False, trigger="item", legend=False, colors=colors)
        o["series"] = [
            {
                "type": "gauge",
                "name": name or title or "value",
                "min": min,
                "max": max,
                "center": ["50%", "60%"],
                "radius": "90%",
                "startAngle": 210,
                "endAngle": -30,
                "progress": {"show": True, "width": 10, "roundCap": True},
                "axisLine": {"roundCap": True, "lineStyle": {"width": 10}},
                "pointer": {"show": False},
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "anchor": {"show": False},
                "title": {"show": bool(name), "offsetCenter": [0, "32%"]},
                "detail": {
                    "valueAnimation": True,
                    "offsetCenter": [0, 0],
                    "fontSize": 24,
                    "formatter": value_format,
                },
                "data": [{"value": min, "name": name}],
            }
        ]
        return _finish(cls, o, option, height=height, max_points=max_points, name=name)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        if isinstance(data, Mapping):
            items = [{"name": str(k), "value": v} for k, v in data.items()]
        else:
            items = [{"name": (props.get("spec") or {}).get("name", ""), "value": data}]
        return {"series": [{"data": items}]}


class Sparkline(Chart):
    """A small trend line: no axes, no grid, no tooltip. For stat cards and table cells.

    ``set`` takes bare y values or ``[[x, y], ...]``; ``append([y])`` streams.

    Args:
        area: Fill under the line.
        color: Line color; otherwise the first chart slot.
    """

    @classmethod
    def slot(
        cls,
        *,
        area: bool = False,
        color: str = "",
        height: int = 32,
        max_points: int = 100,
        option: Mapping[str, Any] | None = None,
    ) -> Self:
        line: Option = {
            "type": "line",
            "name": "value",
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 1.5},
            "data": [],
        }
        if area:
            line["areaStyle"] = {"opacity": 0.15}
        o: Option = {
            "animation": False,
            "tooltip": {"show": False},
            "grid": {"left": 1, "right": 1, "top": 2, "bottom": 2, "outerBoundsMode": "none"},
            "xAxis": {"type": "category", "show": False, "boundaryGap": False},
            "yAxis": {"type": "value", "show": False, "scale": True},
            "series": [line],
        }
        if color:
            o["color"] = [color]
        return _finish(cls, o, option, height=height, max_points=max_points)

    @classmethod
    def _data(cls, data: Any, props: Mapping[str, Any]) -> Option:
        return {"series": [{"data": _rows(data)}]}
