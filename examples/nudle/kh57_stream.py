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
    height:  nu.v.IntRef
    entries: nu.v.Kh57Ref[int]


class Dashboard(nu.nd.Page):
    heading: nu.nd.HeadingRef
    count:   nu.nd.TextRef
    chart:   nu.nd.LineChart
    n:       nu.nd.NumberInputRef


class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav:   nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})


bg = nu.v.Transaction(
    nu.IfDo(Series.height.missing(), Series.height.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(
        Series.entries.set(Series.height, nurandom.randint(0, 100))
        >> Series.height.store(Series.height + 1),
    )
    >> nu.Delay(0.001),
)

ui = (
    App.title.store("kh57 sample stream")
    >> Dashboard.heading.store("kh57 live sample")
    >> Dashboard.n.store(200, min=10, max=2000, step=10, label="sample size")
    >> nu.ForeverDo(
        nu.v.Snapshot(
            Dashboard.chart.store_points(
                nu.CollectQuery(
                    nu.SortedQuery(
                        Series.entries.sample(Dashboard.n, 0, Series.height),
                    ),
                )
            )
            | Dashboard.count.store(nu.StrQuery(Series.height)),
            
        )
        >> nu.Delay(0.1),
    )
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbtest-kh57"),
    nu.nd.presets.server(ui),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(tree))
