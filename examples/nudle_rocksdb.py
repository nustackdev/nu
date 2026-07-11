"""RocksDB + NudleServer bracket app: browser dashboard on a live counter."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    heading: nu.ui.HeadingRef
    count: nu.ui.TextRef
    history: nu.ui.LineChart


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav: nu.ui.NavRef
    pages = nu.ui.Pages({"/": Dashboard})


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
    nu.ui.presets.server(ui),
    body=counter,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(app)))
