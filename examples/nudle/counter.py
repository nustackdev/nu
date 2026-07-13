"""End-to-end nudle smoke test: rocksdb counter ticks, browser dashboard shows it live."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    heading: nu.ui.HeadingRef
    count:   nu.ui.TextRef
    history: nu.ui.LineChart
    name:    nu.ui.InputRef
    greet:   nu.ui.ButtonRef


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav:   nu.ui.NavRef
    pages = nu.ui.Pages({"/": Dashboard})


ui = (
    App.title.set("nudle counter")
    >> Dashboard.heading.set("counter live")
    >> (
        nu.ForeverDo(
            nu.v.Snapshot(
                Dashboard.count.set(Counter.value + 1)
                | Dashboard.history.append(Counter.value, Counter.value),
            )
            >> nu.Delay(1.0),
        )
        | nu.ReactForever(
            Dashboard.greet.clicked(),
            Dashboard.heading.set(Dashboard.name),
        )
    )
)

bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    nu.ui.presets.server(nu.v.auto_flow_atomic(ui)),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
