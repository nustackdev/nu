"""End-to-end nudle example: a kh57-backed live-sampled series.

Rocksdb-backed kh57 map grows one random int per key every 10ms. The
dashboard redraws a sorted downsample every 100ms. A numeric input controls
the sample size (browser is source of truth).
"""

from __future__ import annotations

import asyncio

import nu
import nu.std.random as nurandom


class Series(nu.Shape):
    height: nu.v.IntRef
    entries: nu.v.Kh57Ref[int]


class Dashboard(nu.ui.Page):
    heading: nu.ui.HeadingRef
    count: nu.ui.TextRef
    chart: nu.ui.LineChart
    n: nu.ui.NumberInputRef


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Dashboard})


bg = nu.v.Transaction(
    nu.IfDo(Series.height.missing(), Series.height.set(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(
        Series.entries.set_item(Series.height, nurandom.randint(0, 100))
        >> Series.height.set(Series.height + 1),
    )
    >> nu.Delay(0.001),
)

ui = (
    App.title.set("kh57 sample stream")
    >> Dashboard.heading.set("kh57 live sample")
    >> Dashboard.n.set(200, min=10, max=2000, step=10, label="sample size")
    >> nu.ForeverDo(
        nu.v.Snapshot(
            Dashboard.chart.set_points(
                nu.Collect(
                    nu.Sorted(
                        Series.entries.sample(Dashboard.n, 0, Series.height),
                    ),
                )
            )
            | Dashboard.count.set(nu.ToStr(Series.height)),
        )
        >> nu.Delay(0.1),
    )
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest-kh57"),
    nu.ui.nudle.server(nu.v.auto_flow_atomic(ui)),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
