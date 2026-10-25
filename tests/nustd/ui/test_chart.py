"""Chart Refs: one ``Chart`` node, typed builders over it, and the frames they ship.

No browser. A builder's slot is checked for the option it declares, and its
``set`` for the merge patch its data hook makes. The samples at the bottom
are also what the ui-kit's chart stories draw: they read the same props and
patches from ``chart-samples.json``, so the stories show exactly what Python
ships. ``UPDATE_CHART_SAMPLES=1`` rewrites that file.
"""

from __future__ import annotations

import asyncio
import json
import math

import pytest
from _support.stories import STORIES, check_fixture

import nu
import nustd.ui as ui
from nu import Context
from nustd.ui import Session
from nustd.ui.core import Changed
from nustd.ui.refs import ColumnRef
from nustd.ui.refs.leaves import chart
from nustd.ui.refs.leaves.chart import merge_option


class _Recording:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _run(term: nu.Nu) -> list:
    sess = _Recording()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _built(slot):
    """The Ref a slot makes, under a column, carrying the slot's props."""
    ref = slot.ref_cls("chart", parent_ref=ColumnRef("c"))
    ref._payload["props"] = dict(slot.props)
    return ref


def _patch(slot, data):
    (frame,) = _run(_built(slot).set(data))
    assert frame.op == "merge"
    return frame.payload


# --- the base and its interactions -----------------------------------------------


def test_every_chart_is_one_wire_type():
    for name in chart.__all__:
        cls = getattr(chart, name)
        if isinstance(cls, type):
            assert cls._wire_type == "Chart"
            assert getattr(ui, name) is cls


def test_raw_option_slot():
    option = {"series": [{"type": "line", "data": [1, 2]}]}
    slot = ui.Chart.slot(option=option, height=180)
    assert slot.props == {"option": option, "height": 180, "max_points": 500}


def test_chart_built_alone_carries_its_option_on_the_chain():
    ref = ui.LineChart("trend", parent_ref=ColumnRef("c"))
    (frame,) = _run(ref.clear())
    seg, typ, props = frame.chain[-1]
    assert (seg, typ) == ("trend", "Chart")
    assert props["option"]["series"][0]["type"] == "line"


def test_set_option_replaces_the_whole_option():
    option = {"series": [{"type": "bar", "data": [3]}]}
    (frame,) = _run(_built(ui.Chart.slot()).set(option=option))
    assert frame.op == "write"
    assert frame.payload == {"option": option}


def test_set_takes_data_or_option_not_both():
    ref = _built(ui.Chart.slot())
    with pytest.raises(TypeError):
        ref.set()
    with pytest.raises(TypeError):
        ref.set([1], option={})


def test_merge_ships_the_partial_option():
    (frame,) = _run(_built(ui.Chart.slot()).merge({"title": {"text": "Hi"}}))
    assert (frame.op, frame.payload) == ("merge", {"title": {"text": "Hi"}})


def test_append_ships_points_and_series():
    ref = _built(ui.LineChart.slot(["cpu"]))
    (frame,) = _run(ref.append([[1, 2], [2, 3]], "cpu"))
    assert (frame.op, frame.payload) == ("append", {"points": [[1, 2], [2, 3]], "series": "cpu"})
    (frame,) = _run(ref.append([[3, 4]]))
    assert frame.payload == {"points": [[3, 4]], "series": 0}


def test_clear_ships_the_series_or_none():
    ref = _built(ui.LineChart.slot())
    assert _run(ref.clear())[0].payload == {"series": None}
    assert _run(ref.clear("value"))[0].payload == {"series": "value"}
    assert _run(ref.clear())[0].op == "clear"


def test_on_click_takes_click_events_only():
    sub = _built(ui.PieChart.slot()).on_click()
    assert isinstance(sub, Changed)
    assert len(sub._children) == 2


def test_base_set_data():
    assert _patch(ui.Chart.slot(), [1, 2]) == {"series": [{"data": [1, 2]}]}


# --- merge rules ------------------------------------------------------------------


def test_merge_option_matches_by_id_then_name_then_position():
    base = {"series": [{"id": "a", "v": 1}, {"name": "b", "v": 2}, {"v": 3}]}
    out = merge_option(base, {"series": [{"id": "a", "w": 1}, {"name": "b", "w": 2}]})
    assert out["series"] == [{"id": "a", "v": 1, "w": 1}, {"name": "b", "v": 2, "w": 2}, {"v": 3}]
    out = merge_option(base, {"series": [{"x": 1}]})
    assert out["series"][0] == {"id": "a", "v": 1, "x": 1}


def test_merge_option_appends_only_past_the_free_slots_and_replaces_values():
    base = {"color": ["#000"], "series": [{"name": "a", "data": [1, 2]}]}
    patch = {"color": ["#fff"], "series": [{"name": "a", "data": [3]}, {"name": "z", "data": [9]}]}
    out = merge_option(base, patch)
    assert out["color"] == ["#fff"]
    assert out["series"] == [{"name": "a", "data": [3]}, {"name": "z", "data": [9]}]
    assert base["series"] == [{"name": "a", "data": [1, 2]}]
    # An unmatched name takes the first unclaimed slot, as ECharts does.
    assert merge_option(base, {"series": [{"name": "z"}]})["series"] == [
        {"name": "z", "data": [1, 2]}
    ]
    # An unmatched id never overwrites another.
    assert len(merge_option(base, {"series": [{"id": "q"}]})["series"]) == 2


def test_merge_option_treats_an_object_and_a_list_as_one_component():
    out = merge_option({"xAxis": [{"type": "time"}]}, {"xAxis": {"name": "t"}})
    assert out["xAxis"] == [{"type": "time", "name": "t"}]
    out = merge_option({"xAxis": {"type": "time"}}, {"xAxis": {"name": "t"}})
    assert out["xAxis"] == {"type": "time", "name": "t"}


def test_slot_option_overrides_merge_over_the_built_option():
    slot = ui.LineChart.slot(
        option={"yAxis": {"type": "log"}, "series": [{"lineStyle": {"width": 1}}]}
    )
    option = slot.props["option"]
    assert option["yAxis"]["type"] == "log"
    assert option["series"][0]["type"] == "line"
    assert option["series"][0]["lineStyle"] == {"width": 1}


# --- builders ---------------------------------------------------------------------


def test_line_slot_declares_one_series_per_name():
    option = ui.LineChart.slot(["cpu", "mem"], smooth=True, x_type="time").props["option"]
    assert [s["name"] for s in option["series"]] == ["cpu", "mem"]
    assert all(s["smooth"] and s["type"] == "line" for s in option["series"])
    assert option["xAxis"]["type"] == "time"
    assert option["legend"]["type"] == "scroll"
    assert "legend" not in ui.LineChart.slot().props["option"]


def test_area_chart_fills_and_stacks():
    option = ui.AreaChart.slot(["a", "b"], stack=True).props["option"]
    assert all("areaStyle" in s and s["stack"] == "total" for s in option["series"])


def test_cartesian_set_by_name_fills_left_out_series_and_adds_new_ones():
    patch = _patch(
        ui.LineChart.slot(["cpu", "mem"], smooth=True), {"cpu": [[0, 1]], "gpu": [[0, 2]]}
    )
    by_name = {s["name"]: s for s in patch["series"]}
    assert by_name["cpu"] == {"name": "cpu", "data": [[0, 1]]}
    assert by_name["mem"] == {"name": "mem", "data": []}
    assert by_name["gpu"]["type"] == "line" and by_name["gpu"]["smooth"] is True


def test_cartesian_wide_rows_spread_across_series():
    patch = _patch(ui.AreaChart.slot(["a", "b"]), [["Jan", 1, 2], ["Feb", 3, 4]])
    assert patch == {
        "series": [{"data": [["Jan", 1], ["Feb", 3]]}, {"data": [["Jan", 2], ["Feb", 4]]}]
    }


def test_bar_horizontal_keeps_category_first_and_takes_a_mapping():
    slot = ui.BarChart.slot(horizontal=True)
    option = slot.props["option"]
    assert option["yAxis"]["type"] == "category"
    assert option["series"][0]["encode"] == {"x": 1, "y": 0}
    assert _patch(slot, {"A": 3, "B": 1}) == {"series": [{"data": [["A", 3], ["B", 1]]}]}
    assert _patch(slot, [5, 6]) == {"series": [{"data": [["0", 5], ["1", 6]]}]}


def test_histogram_bins_in_python():
    patch = _patch(ui.Histogram.slot(bins=4, range=(0, 8)), [0, 1, 2, 3, 4, 5, 6, 7, 8, 100])
    assert patch["series"] == [{"data": [2, 2, 2, 3]}]
    assert patch["xAxis"]["data"][0] == f"0.0{chr(0x2013)}2.0"


def test_boxplot_works_out_the_five_numbers():
    patch = _patch(ui.BoxplotChart.slot(), {"a": [1, 2, 3, 4, 5]})
    assert patch == {"xAxis": {"data": ["a"]}, "series": [{"data": [[1, 2, 3, 4, 5]]}]}


def test_heatmap_adds_labels_and_fits_the_scale():
    patch = _patch(ui.HeatmapChart.slot(x=["Mon"]), [["Mon", "am", 1], ["Tue", "pm", 5]])
    assert patch["xAxis"] == {"data": ["Mon", "Tue"]}
    assert patch["yAxis"] == {"data": ["am", "pm"]}
    assert patch["series"] == [{"data": [[0, 0, 1], [1, 1, 5]]}]
    assert patch["visualMap"] == {"min": 1, "max": 5}


def test_heatmap_takes_a_matrix():
    patch = _patch(ui.HeatmapChart.slot(), [[1, 2], [3, 4]])
    assert patch["series"] == [{"data": [[0, 0, 1], [1, 0, 2], [0, 1, 3], [1, 1, 4]]}]
    assert patch["xAxis"] == {"data": ["0", "1"]}


def test_pie_donut_total_in_the_middle():
    slot = ui.PieChart.slot(donut=True, total_label="animals")
    assert slot.props["option"]["series"][0]["radius"][0] == "52%"
    patch = _patch(slot, {"a": 2, "b": 3})
    assert patch["title"] == [{"id": "total", "text": "5"}]


def test_sankey_derives_nodes_from_links():
    patch = _patch(
        ui.SankeyChart.slot(), [["a", "b", 2], {"source": "b", "target": "c", "value": 1}]
    )
    (series,) = patch["series"]
    assert series["data"] == [{"name": "a"}, {"name": "b"}, {"name": "c"}]
    assert series["links"][1] == {"source": "b", "target": "c", "value": 1}


def test_tree_data_nests_by_key():
    patch = _patch(ui.TreemapChart.slot(), {"src": {"ui": 3}, "docs": 1})
    assert patch == {
        "series": [
            {
                "data": [
                    {"name": "src", "children": [{"name": "ui", "value": 3}]},
                    {"name": "docs", "value": 1},
                ]
            }
        ]
    }


def test_radar_items_by_name():
    slot = ui.RadarChart.slot(["speed", ("power", 10)])
    assert slot.props["option"]["radar"]["indicator"] == [
        {"name": "speed"},
        {"name": "power", "max": 10},
    ]
    assert _patch(slot, {"A": [1, 2]}) == {"series": [{"data": [{"name": "A", "value": [1, 2]}]}]}


def test_gauge_takes_a_number():
    assert _patch(ui.GaugeChart.slot(name="CPU"), 72) == {
        "series": [{"data": [{"name": "CPU", "value": 72}]}]
    }


def test_sparkline_has_no_chrome():
    option = ui.Sparkline.slot(color="var(--chart-2)").props["option"]
    assert option["xAxis"]["show"] is False and option["yAxis"]["show"] is False
    assert option["color"] == ["var(--chart-2)"]
    assert ui.Sparkline.slot().props["max_points"] == 100


# --- the samples the kit stories draw ------------------------------------------------

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
_EIGHT = [f"Series {i + 1}" for i in range(8)]
_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_TREE = {"src": {"nu": 120, "nustd": {"ui": 80, "kv": 40}}, "tests": 60, "docs": 30}


def _wig(i: int, m: int) -> int:
    return 10 + i * 4 + ((m * (i + 3)) % 9)


def _samples() -> dict:
    t0 = 1_700_000_000_000
    return {
        "line": (
            ui.LineChart.slot(_EIGHT, title="Requests", x_type="category", y_label="req/s"),
            {n: [[m, _wig(i, k)] for k, m in enumerate(_MONTHS)] for i, n in enumerate(_EIGHT)},
        ),
        "line-time": (
            ui.LineChart.slot(
                ["cpu", "mem"],
                x_type="time",
                smooth=True,
                x_format="{HH}:{mm}",
                y_format="{value}%",
                y_min=0,
                y_max=100,
            ),
            {
                "cpu": [[t0 + k * 60000, round(40 + 20 * math.sin(k / 3), 2)] for k in range(40)],
                "mem": [[t0 + k * 60000, round(60 + 10 * math.cos(k / 4), 2)] for k in range(40)],
            },
        ),
        "area-stacked": (
            ui.AreaChart.slot(["a", "b", "c"], stack=True, x_type="category"),
            [[m, _wig(0, k), _wig(1, k), _wig(2, k)] for k, m in enumerate(_MONTHS)],
        ),
        "bar": (
            ui.BarChart.slot(_EIGHT[:4], title="Sightings"),
            {
                n: [[m, _wig(i, k)] for k, m in enumerate(_MONTHS[:6])]
                for i, n in enumerate(_EIGHT[:4])
            },
        ),
        "bar-stacked": (
            ui.BarChart.slot(["ok", "warn", "fail"], stack=True),
            {
                n: [[m, _wig(i, k)] for k, m in enumerate(_MONTHS[:6])]
                for i, n in enumerate(["ok", "warn", "fail"])
            },
        ),
        "bar-horizontal": (
            ui.BarChart.slot(horizontal=True, labels=True),
            {"Trap A": 41, "Trap B": 28, "Trap C": 35, "Trap D": 17},
        ),
        "scatter": (
            ui.ScatterChart.slot(["north", "south", "east"], x_label="weight", y_label="length"),
            {
                n: [[20 + i * 7 + (k * 13) % 17, 5 + i * 3 + (k * 7) % 11] for k in range(24)]
                for i, n in enumerate(["north", "south", "east"])
            },
        ),
        "histogram": (
            ui.Histogram.slot(bins=12, x_label="latency ms"),
            [round(abs(math.sin(k) * 50 + (k % 7) * 8), 2) for k in range(300)],
        ),
        "pie": (
            ui.PieChart.slot(label_format="{b}: {d}%"),
            {f"Slot {i + 1}": 8 + ((i * 5) % 11) for i in range(8)},
        ),
        "donut": (
            ui.PieChart.slot(donut=True, total_label="animals", legend=True, labels=False),
            [["Mammals", 62], ["Birds", 24], ["Reptiles", 9], ["Insects", 5]],
        ),
        "funnel": (
            ui.FunnelChart.slot(label_format="{b}: {c}"),
            {"Visited": 1000, "Signed up": 420, "Activated": 260, "Paid": 90},
        ),
        "heatmap": (
            ui.HeatmapChart.slot(_DAYS, [f"{h}h" for h in range(0, 24, 3)]),
            [[d, f"{h}h", (i * 7 + h) % 23] for i, d in enumerate(_DAYS) for h in range(0, 24, 3)],
        ),
        "radar": (
            ui.RadarChart.slot([(n, 100) for n in ("speed", "power", "range", "cost", "comfort")]),
            {"Model A": [80, 60, 70, 40, 90], "Model B": [50, 90, 60, 80, 40]},
        ),
        "treemap": (ui.TreemapChart.slot(), _TREE),
        "sunburst": (ui.SunburstChart.slot(), _TREE),
        "sankey": (
            ui.SankeyChart.slot(),
            [
                ["visit", "signup", 420],
                ["visit", "bounce", 580],
                ["signup", "active", 260],
                ["signup", "churn", 160],
                ["active", "paid", 90],
            ],
        ),
        "gauge": (ui.GaugeChart.slot(name="CPU", value_format="{value}%"), 72),
        "boxplot": (
            ui.BoxplotChart.slot(),
            {f"G{i}": [10 + i * 3 + ((k * (i + 5)) % 17) for k in range(30)] for i in range(5)},
        ),
        "candlestick": (
            ui.CandlestickChart.slot(),
            [[f"D{k}", 20 + k % 5, 22 + (k * 3) % 6, 18 + k % 4, 26 + k % 5] for k in range(20)],
        ),
        "sparkline": (ui.Sparkline.slot(area=True), [4, 7, 5, 9, 6, 11, 8, 12, 10, 14]),
    }


_FIXTURE = STORIES / "refs/chart-samples.json"


def _rendered() -> dict:
    return {
        name: {"props": slot.props, "patch": _patch(slot, data)}
        for name, (slot, data) in _samples().items()
    }


def test_story_samples_match_the_builders():
    current = json.loads(json.dumps(_rendered()))
    check_fixture(
        _FIXTURE, current, test="tests/nustd/ui/test_chart.py", flags=("UPDATE_CHART_SAMPLES",)
    )
