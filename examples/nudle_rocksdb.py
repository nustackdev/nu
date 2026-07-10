"""RocksDB + NudleServer bracket app: browser dashboard on a live counter."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.nd.Page):
    heading: nu.nd.HeadingRef
    count: nu.nd.TextRef
    history: nu.nd.LineChart


class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav: nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})


counter = nu.IfDo(Counter.value.missing(), Counter.value.store(0)) >> nu.ForeverDo(
    Counter.value.inc() >> nu.Delay(1.0)
)

ui = (
    App.title.store("nudle bracket counter")
    >> Dashboard.heading.store("counter live")
    >> (
        nu.ReactForever(
            Counter.value.on_change(),
            Dashboard.count.store(Counter.value)
            | Dashboard.history.append(Counter.value, Counter.value),
        )
    )
)

app = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbtest"),
    nu.nd.presets.server(ui),
    body=counter,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(app)))
