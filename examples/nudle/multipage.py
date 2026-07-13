"""Multi-page nudle smoke test: two pages sharing one live counter, state persists across nav."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class HomePage(nu.ui.Page):
    heading:  nu.ui.HeadingRef
    count:    nu.ui.TextRef
    go_feed:  nu.ui.ButtonRef


class FeedPage(nu.ui.Page):
    heading:  nu.ui.HeadingRef
    history:  nu.ui.LineChart
    go_home:  nu.ui.ButtonRef


class App(nu.ui.Index):
    title: nu.ui.TitleRef
    nav:   nu.ui.NavRef
    pages = nu.ui.Pages({"/": HomePage, "/feed": FeedPage})


bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)

# Both pages tick continuously so nav never tears down state.
tick_home = nu.ForeverDo(
    nu.v.Snapshot(HomePage.count.set(Counter.value)) >> nu.Delay(1.0),
)
tick_feed = nu.ForeverDo(
    nu.v.Snapshot(FeedPage.history.append(Counter.value, Counter.value)) >> nu.Delay(1.0),
)
nav_home = nu.ReactForever(HomePage.go_feed.clicked(), App.nav.set("/feed"))
nav_feed = nu.ReactForever(FeedPage.go_home.clicked(), App.nav.set("/"))

ui = (
    App.title.set("nudle multipage")
    >> HomePage.heading.set("home")
    >> FeedPage.heading.set("feed")
    >> (tick_home | tick_feed | nav_home | nav_feed)
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest_mp"),
    nu.ui.presets.server(nu.v.auto_flow_atomic(ui)),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(nu.v.auto_flow_atomic(tree)))
