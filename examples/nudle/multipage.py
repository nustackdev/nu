"""Multi-page nudle smoke test: two pages sharing one live counter, state persists across nav."""

from __future__ import annotations

import asyncio

import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class HomePage(nu.nd.Page):
    heading:  nu.nd.HeadingRef
    count:    nu.nd.TextRef
    go_feed:  nu.nd.ButtonRef


class FeedPage(nu.nd.Page):
    heading:  nu.nd.HeadingRef
    history:  nu.nd.LineChart
    go_home:  nu.nd.ButtonRef


class App(nu.nd.Index):
    title: nu.nd.TitleRef
    nav:   nu.nd.NavRef
    pages = nu.nd.Pages({"/": HomePage, "/feed": FeedPage})


bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)

# Both pages tick continuously so nav never tears down state.
tick_home = nu.ForeverDo(
    nu.v.Snapshot(HomePage.count.store(Counter.value)) >> nu.Delay(1.0),
)
tick_feed = nu.ForeverDo(
    nu.v.Snapshot(FeedPage.history.append(Counter.value, Counter.value)) >> nu.Delay(1.0),
)
nav_home = nu.ReactForever(HomePage.go_feed.clicked(), App.nav.store("/feed"))
nav_feed = nu.ReactForever(FeedPage.go_home.clicked(), App.nav.store("/"))

ui = (
    App.title.store("nudle multipage")
    >> HomePage.heading.store("home")
    >> FeedPage.heading.store("feed")
    >> (tick_home | tick_feed | nav_home | nav_feed)
)

tree = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory(".dbtest_mp"),
    nu.nd.presets.server(ui),
    body=bg,
)


if __name__ == "__main__":
    asyncio.run(nu.arun(tree))
