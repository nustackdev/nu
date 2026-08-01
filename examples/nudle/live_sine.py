"""Live-sampled sine wave: infinite sin(t) series, kh57 reservoir sample, live chart. Drag n to watch aliasing."""

import asyncio

import nu
import nu.std.math as m


class Series(nu.Shape):
    height: nu.v.IntRef
    entries: nu.v.Kh57Ref[float]


class Dashboard(nu.ui.Page):
    chart: nu.ui.LineChart
    n: nu.ui.NumberInputRef


class App(nu.ui.Index):
    pages = nu.ui.Pages({"/": Dashboard})


bg = nu.v.Transaction(nu.IfDo(Series.height.missing(), Series.height.set(0))) >> nu.ForeverDo(
    nu.v.Transaction(
        Series.entries.set_item(Series.height, m.sin(Series.height * 0.05)) >> Series.height.inc()
    )
    >> nu.Delay(0.001),
)

ui = Dashboard.n.set(200, min=10, max=2000, step=10, label="sample size") >> nu.ForeverDo(
    nu.v.Snapshot(
        Dashboard.chart.set_points(
            nu.CollectQuery(nu.SortedQuery(Series.entries.sample(Dashboard.n, 0, Series.height)))
        )
    )
    >> nu.Delay(0.1),
)

tree = nu.With(
    nu.v.presets.memory_navigator(), nu.ui.presets.server(nu.v.auto_flow_atomic(ui)), body=bg
)

asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
