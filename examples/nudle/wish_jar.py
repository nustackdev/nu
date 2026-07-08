"""Wish jar -- click the button to drop your wish into the jar.

Exercises every Ref type on both sides:

- TitleRef   server pushes the latest wish (or status)
- TextRef    server pushes the running wish count
- LineChart  server appends a point per wish
- InputRef   browser owns; server reads on every click
- ButtonRef  two of them: 'wish' and 'clear'
"""

from __future__ import annotations

import asyncio

import nu


class Stats(nu.Shape):
    count: nu.v.IntRef


class Dashboard(nu.nd.Page):
    heading: nu.nd.HeadingRef
    tries:   nu.nd.TextRef
    history: nu.nd.LineChart
    wish:    nu.nd.InputRef
    drop:    nu.nd.ButtonRef
    clear:   nu.nd.ButtonRef


class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav:   nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})


init = nu.v.Transaction(nu.IfDo(Stats.count.missing(), Stats.count.store(0)))

on_drop = nu.ReactForever(
    Dashboard.drop.clicked(),
    nu.v.Transaction(Stats.count.store(Stats.count + 1))
    >> nu.v.Snapshot(
        Dashboard.tries.store(Stats.count)
        | Dashboard.history.append(Stats.count, Stats.count)
        | Dashboard.heading.store(Dashboard.wish),
    ),
)

on_clear = nu.ReactForever(
    Dashboard.clear.clicked(),
    nu.v.Transaction(Stats.count.store(0))
    >> (
        Dashboard.tries.store(0)
        | Dashboard.heading.store("the jar is empty")
        | Dashboard.history.store({"points": []})
    ),
)

hydrate = nu.v.Snapshot(
    Dashboard.heading.store("drop a wish in the jar")
    | Dashboard.tries.store(Stats.count),
)

ui = init >> App.title.store("wish jar") >> hydrate >> (on_drop | on_clear)

tree = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbw"),
    nu.nd.presets.server(ui),
    body=nu.ForeverDo(nu.Delay(3600)),  # keep the server bracket open; jar is click-driven, no bg loop
)


if __name__ == "__main__":
    asyncio.run(nu.arun(tree))
