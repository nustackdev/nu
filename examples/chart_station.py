"""Chart station: a solar research station's dashboard over every chart.

One page, every typed chart, each fed from Python the way an app would:
`set` seeds them, `append` streams the live ones, `merge` and `clear` act
from the toolbar, `on_click` reports the slice or bar you picked, and raw
`Chart` options draw what no builder covers: two y axes, a log axis, a
calendar heatmap, a polar bar, a streamed line with a shaded band.
"""

import asyncio
import math
import random
from datetime import date, timedelta

import nu
from nustd import ui


rng = random.Random(41)  # noqa: S311 - demo data


# --- header -------------------------------------------------------------------


class Header(ui.Row):
    title = ui.HeadingRef.slot(label="Kibo solar station")
    state = ui.StatusPillRef.slot(tone="ok", label="Live")


class Toolbar(ui.Row):
    mark = ui.ButtonRef.slot(label="Mark 80% line", icon="minus", variant="secondary")
    unmark = ui.ButtonRef.slot(label="Remove line", variant="ghost")
    wipe = ui.ButtonRef.slot(label="Clear live", icon="trash-2", variant="ghost")
    picked = ui.TextRef.slot(value="Click a slice or a bar.")


# --- live: streamed every tick ------------------------------------------------


class StatCard(ui.Card):
    stat = ui.StatRef.slot()
    spark = ui.Sparkline.slot(height=32, area=True)


class Stats(ui.Grid):
    power = StatCard.slot(title="Panel output")
    battery = StatCard.slot(title="Battery")
    load = StatCard.slot(title="Load")


class LiveCard(ui.Card):
    chart = ui.LineChart.slot(
        ["cpu", "memory"],
        smooth=True,
        x_label="seconds",
        y_format="{value}%",
        y_min=0,
        y_max=100,
        max_points=60,
    )


class GaugeCard(ui.Card):
    gauge = ui.GaugeChart.slot(name="battery", value_format="{value}%")


class PriceCard(ui.Card):
    candles = ui.CandlestickChart.slot(name="kWh price", max_points=30)


class Live(ui.Row):
    lines = LiveCard.slot(title="Controller load", subtitle="streamed, last 60 s")
    gauge = GaugeCard.slot(title="Charge")
    candles = PriceCard.slot(title="Grid price", subtitle="a candle every 5 s")


# --- energy -------------------------------------------------------------------


class EnergyCard(ui.Card):
    area = ui.AreaChart.slot(
        ["solar", "wind", "grid"], stack=True, smooth=True, x_type="category", y_label="kWh"
    )


class SplitCard(ui.Card):
    pie = ui.PieChart.slot(donut=True, total_label="kWh today", labels=False, legend=True)


class FlowCard(ui.Card):
    sankey = ui.SankeyChart.slot(height=280)


class Energy(ui.Row):
    area = EnergyCard.slot(title="Energy by source", subtitle="this week")
    split = SplitCard.slot(title="Where it went")
    flow = FlowCard.slot(title="Flow", subtitle="source to load")


# --- sensors ------------------------------------------------------------------


class BarsCard(ui.Card):
    bars = ui.BarChart.slot(["day", "night"], stack=True, labels=False, value_format="{value} kWh")


class RankCard(ui.Card):
    rank = ui.BarChart.slot(horizontal=True, labels=True)


class ScatterCard(ui.Card):
    scatter = ui.ScatterChart.slot(
        ["roof", "field"],
        x_label="temp",
        y_label="humidity",
        x_format="{value}°",
        y_format="{value}%",
    )


class HeatCard(ui.Card):
    heat = ui.HeatmapChart.slot(
        x=[f"{h:02d}" for h in range(0, 24, 2)],
        y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        value_format="{c} W",
    )


class Sensors(ui.Grid):
    bars = BarsCard.slot(title="Daily yield", subtitle="day and night, stacked")
    rank = RankCard.slot(title="Panels by output")
    scatter = ScatterCard.slot(title="Temperature against humidity")
    heat = HeatCard.slot(title="Output by hour", subtitle="last week")


# --- spread -------------------------------------------------------------------


class HistCard(ui.Card):
    hist = ui.Histogram.slot(bins=12, x_label="ms", y_label="requests")


class BoxCard(ui.Card):
    box = ui.BoxplotChart.slot(value_format="{value} V")


class RadarCard(ui.Card):
    radar = ui.RadarChart.slot(
        [("panels", 100), ("battery", 100), ("inverter", 100), ("cooling", 100), ("network", 100)]
    )


class Spread(ui.Grid):
    hist = HistCard.slot(title="Uplink latency", subtitle="binned in Python")
    box = BoxCard.slot(title="Cell voltage", subtitle="per battery bank")
    radar = RadarCard.slot(title="Health", subtitle="today against last month")


# --- storage and pipeline -----------------------------------------------------


class TreeCard(ui.Card):
    tree = ui.TreemapChart.slot(height=280)


class SunCard(ui.Card):
    sun = ui.SunburstChart.slot(height=280)


class FunnelCard(ui.Card):
    funnel = ui.FunnelChart.slot()


class Storage(ui.Grid):
    tree = TreeCard.slot(title="Disk", subtitle="treemap")
    sun = SunCard.slot(title="Disk", subtitle="sunburst, same data")
    funnel = FunnelCard.slot(title="Telemetry pipeline")


# --- raw options: `Chart` takes any ECharts option -----------------------------
#
# No builder covers these, so each is an ECharts option written out in full.
# They take the same five calls as every typed chart: `set(option=...)`,
# `merge`, `append`, `clear`, `on_click`.


class DualCard(ui.Card):
    # Two y axes: bars on the left, a line on the right. The data comes later
    # through `merge`, matched to each series by name.
    dual = ui.Chart.slot(
        option={
            "tooltip": {"trigger": "axis"},
            "legend": {},
            "xAxis": {
                "type": "category",
                "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            },
            "yAxis": [
                {"type": "value", "name": "kWh"},
                {"type": "value", "name": "°C", "position": "right", "splitLine": {"show": False}},
            ],
            "series": [
                {"type": "bar", "name": "yield", "data": []},
                {"type": "line", "name": "temp", "yAxisIndex": 1, "smooth": True, "data": []},
            ],
        }
    )


class LogCard(ui.Card):
    # A log axis, for errors that span three orders of magnitude.
    log = ui.Chart.slot(
        option={
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [f"w{w}" for w in range(1, 13)]},
            "yAxis": {"type": "log", "name": "errors"},
            "series": [
                {
                    "type": "line",
                    "name": "errors",
                    "data": [3, 8, 21, 60, 140, 410, 980, 520, 230, 90, 30, 12],
                    "markPoint": {"data": [{"type": "max", "name": "peak"}]},
                }
            ],
        }
    )


class PulseCard(ui.Card):
    # A raw option streamed with `append`: the shaded band is a markArea, the
    # points arrive one a second like any typed chart's.
    pulse = ui.Chart.slot(
        max_points=60,
        option={
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "value", "scale": True, "name": "s"},
            "yAxis": {"type": "value", "min": 40, "max": 120, "name": "bpm"},
            "series": [
                {
                    "type": "line",
                    "name": "fan",
                    "showSymbol": False,
                    "data": [],
                    "markArea": {"data": [[{"yAxis": 90}, {"yAxis": 120}]]},
                }
            ],
        },
    )


class CalendarCard(ui.Card):
    # A calendar heatmap: a whole year of daily yield, one cell a day.
    calendar = ui.Chart.slot(
        height=200,
        option={
            "tooltip": {"formatter": "{c}"},
            "visualMap": {
                "min": 0,
                "max": 60,
                "orient": "horizontal",
                "left": "center",
                "bottom": 0,
                "calculable": False,
            },
            "calendar": {
                "range": "2026",
                "cellSize": ["auto", 14],
                "top": 30,
                "left": 40,
                "right": 20,
            },
            "series": [{"type": "heatmap", "coordinateSystem": "calendar", "data": []}],
        },
    )


class PolarCard(ui.Card):
    # A polar bar, the wind rose: clicking a direction reports it.
    polar = ui.Chart.slot(
        option={
            "angleAxis": {"type": "category", "data": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]},
            "radiusAxis": {},
            "polar": {},
            "tooltip": {},
            "series": [
                {
                    "type": "bar",
                    "coordinateSystem": "polar",
                    "name": "wind",
                    "data": [4, 7, 12, 9, 5, 3, 6, 8],
                }
            ],
        }
    )


class Raw(ui.Grid):
    dual = DualCard.slot(title="Yield and temperature", subtitle="two y axes, data by merge")
    log = LogCard.slot(title="Errors", subtitle="log axis, mark point")
    pulse = PulseCard.slot(title="Fan speed", subtitle="raw option, streamed")
    polar = PolarCard.slot(title="Wind rose", subtitle="polar bar, click a direction")


# --- page ---------------------------------------------------------------------


class Home(ui.Page):
    header = Header.slot(gap=3)
    toolbar = Toolbar.slot(gap=2)
    stats = Stats.slot(columns=3, min_width=180, gap=3)
    h_live = ui.HeadingRef.slot(label="Live")
    live = Live.slot(wrap=True, min_width=300, gap=3)
    h_energy = ui.HeadingRef.slot(label="Energy")
    energy = Energy.slot(wrap=True, min_width=300, gap=3)
    h_sensors = ui.HeadingRef.slot(label="Sensors")
    sensors = Sensors.slot(columns=2, min_width=320, gap=3)
    h_spread = ui.HeadingRef.slot(label="Spread")
    spread = Spread.slot(columns=3, min_width=280, gap=3)
    h_storage = ui.HeadingRef.slot(label="Storage and pipeline")
    storage = Storage.slot(columns=3, min_width=280, gap=3)
    h_raw = ui.HeadingRef.slot(label="Raw options")
    raw = Raw.slot(columns=2, min_width=320, gap=3)
    calendar = CalendarCard.slot(title="A year of yield", subtitle="calendar heatmap")


class App(ui.Index):
    home = Home.slot("/")


h = App.home


def chain(*steps: nu.Nu) -> nu.Nu:
    """Steps in order, nested as a balanced tree so a long run stays shallow."""
    if len(steps) == 1:
        return steps[0]
    mid = len(steps) // 2
    return chain(*steps[:mid]) >> chain(*steps[mid:])


# --- seed: every chart's first `set` ------------------------------------------

week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
disk = {
    "data": {"telemetry": 420, "images": 310, "logs": 90},
    "system": {"os": 60, "packages": 45},
    "models": {"forecast": 180, "vision": 120},
}

day0 = date(2026, 1, 1)
year = []
for i in range(365):
    day = day0 + timedelta(days=i)
    sun = 30 + 25 * math.sin((day.month - 3) / 12 * 2 * math.pi)
    year.append([day.isoformat(), max(0, round(sun) + rng.randint(-8, 8))])

seed = chain(
    h.raw.dual.dual.merge(
        {
            "series": [
                {"name": "yield", "data": [rng.randint(30, 55) for _ in week]},
                {"name": "temp", "data": [rng.randint(18, 31) for _ in week]},
            ]
        }
    ),
    h.calendar.calendar.merge({"series": [{"data": year}]}),
    h.energy.area.area.set(
        {
            "solar": [[d, rng.randint(30, 60)] for d in week],
            "wind": [[d, rng.randint(5, 25)] for d in week],
            "grid": [[d, rng.randint(2, 12)] for d in week],
        }
    ),
    h.energy.split.pie.set(
        {"Cooling": 38, "Compute": 61, "Radios": 17, "Lights": 9, "Battery": 24}
    ),
    h.energy.flow.sankey.set(
        [
            ["Solar", "Battery", 30],
            ["Solar", "Compute", 25],
            ["Wind", "Battery", 12],
            ["Wind", "Cooling", 8],
            ["Grid", "Cooling", 6],
            ["Battery", "Compute", 22],
            ["Battery", "Radios", 14],
            ["Battery", "Lights", 6],
        ]
    ),
    h.sensors.bars.bars.set(
        {
            "day": [[d, rng.randint(25, 45)] for d in week],
            "night": [[d, rng.randint(2, 9)] for d in week],
        }
    ),
    h.sensors.rank.rank.set({f"Panel {c}": rng.randint(40, 95) for c in "ABCDEF"}),
    h.sensors.scatter.scatter.set(
        {
            "roof": [
                [round(rng.uniform(18, 38), 1), round(rng.uniform(20, 60))] for _ in range(40)
            ],
            "field": [
                [round(rng.uniform(14, 30), 1), round(rng.uniform(40, 90))] for _ in range(40)
            ],
        }
    ),
    h.sensors.heat.heat.set(
        [
            [x, y, max(0, round(900 * math.sin(math.pi * (x * 2 - 5) / 14)) + rng.randint(-60, 60))]
            for y in range(7)
            for x in range(12)
        ]
    ),
    h.spread.hist.hist.set([round(rng.lognormvariate(4, 0.4)) for _ in range(400)]),
    h.spread.box.box.set(
        {bank: [round(rng.gauss(3.7, 0.08), 2) for _ in range(30)] for bank in ["A", "B", "C", "D"]}
    ),
    h.spread.radar.radar.set({"today": [92, 81, 97, 70, 88], "last month": [85, 90, 93, 76, 64]}),
    h.storage.tree.tree.set(disk),
    h.storage.sun.sun.set(disk),
    h.storage.funnel.funnel.set(
        {"Sampled": 12000, "Filtered": 8400, "Compressed": 6100, "Uplinked": 5200, "Stored": 5100}
    ),
)


# --- live: a minute of ticks, then clear and go again ------------------------
#
# `append` pushes one point per series and the chart keeps the newest
# `max_points`, so the line scrolls without Python ever resending it.

ticks: list[nu.Nu] = [
    h.live.lines.chart.clear(),
    h.live.candles.candles.clear(),
    h.raw.pulse.pulse.clear(),
]
price = 0.30
battery = 64.0
for t in range(120):
    cpu = round(45 + 25 * math.sin(t / 7) + rng.uniform(-6, 6))
    mem = round(55 + 10 * math.sin(t / 19) + rng.uniform(-2, 2))
    watts = round(800 + 300 * math.sin(t / 15) + rng.uniform(-40, 40))
    battery = max(5.0, min(100.0, battery + rng.uniform(-0.6, 0.9)))
    load = round(400 + 120 * math.cos(t / 9) + rng.uniform(-30, 30))
    ticks += [
        h.live.lines.chart.append([[t, cpu]], "cpu"),
        h.live.lines.chart.append([[t, mem]], "memory"),
        h.raw.pulse.pulse.append([[t, round(75 + 20 * math.sin(t / 6) + rng.uniform(-5, 5))]]),
        h.live.gauge.gauge.set(round(battery)),
        h.stats.power.stat.set(f"{watts} W", label="now", trend="up" if watts > 800 else "down"),
        h.stats.power.spark.append([watts]),
        h.stats.battery.stat.set(f"{battery:.0f}%", label="charge", trend="flat"),
        h.stats.battery.spark.append([round(battery)]),
        h.stats.load.stat.set(f"{load} W", label="drawn", trend="flat"),
        h.stats.load.spark.append([load]),
    ]
    if t % 5 == 4:
        o = price
        c = round(o + rng.uniform(-0.04, 0.04), 3)
        ticks.append(
            h.live.candles.candles.append(
                [
                    [
                        f"{t // 60}:{t % 60:02d}",
                        o,
                        c,
                        round(min(o, c) - 0.01, 3),
                        round(max(o, c) + 0.01, 3),
                    ]
                ]
            )
        )
        price = c
    ticks.append(nu.Delay(1))


# --- toolbar: merge, clear, and clicks ----------------------------------------
#
# A mark line is not a builder setting, so it goes in through `merge`, the
# same partial option ECharts' setOption takes.

mark = h.live.lines.chart.merge(
    {"series": [{"name": "cpu", "markLine": {"symbol": "none", "data": [{"yAxis": 80}]}}]}
)
unmark = h.live.lines.chart.merge({"series": [{"name": "cpu", "markLine": {"data": []}}]})

program = seed >> nu.ParallelAsync(
    nu.ForeverDo(chain(*ticks)),
    nu.ReactForever(h.toolbar.mark.on_click(), mark),
    nu.ReactForever(h.toolbar.unmark.on_click(), unmark),
    nu.ReactForever(h.toolbar.wipe.on_click(), h.live.lines.chart.clear()),
    nu.ReactForever(
        h.energy.split.pie.on_click(),
        lambda ev: h.toolbar.picked.set("Slice: " + nu.Str(ev["name"])),
    ),
    nu.ReactForever(
        h.raw.polar.polar.on_click(),
        lambda ev: h.toolbar.picked.set("Wind from " + nu.Str(ev["name"])),
    ),
    nu.ReactForever(
        h.sensors.rank.rank.on_click(),
        lambda ev: h.toolbar.picked.set("Bar: " + nu.Str(ev["name"])),
    ),
)

app = ui.serve(App, program)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
