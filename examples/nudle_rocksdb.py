"""RocksDB + NudleServer bracket app: browser dashboard on a live counter."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.nd.Page):
    heading: nu.nd.HeadingRef
    count:   nu.nd.TextRef
    history: nu.nd.LineChart
    name:    nu.nd.InputRef
    greet:   nu.nd.ButtonRef


class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav:   nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})


ui = (
    App.title.store("nudle bracket counter")
    >> Dashboard.heading.store("counter live")
    >> (
        nu.ForeverDo(
            nu.v.Snapshot(
                Dashboard.count.store(Counter.value + 1)
                | Dashboard.history.append(Counter.value, Counter.value),
            )
            >> nu.Delay(1.0),
        )
        | nu.ReactForever(
            Dashboard.greet.clicked(),
            Dashboard.heading.store(Dashboard.name),
        )
    )
)

bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbtest"),
    nu.nd.presets.server(ui),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(tree))
