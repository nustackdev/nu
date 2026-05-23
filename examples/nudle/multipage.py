"""Multi-page nudle smoke test.

Two pages, one Index. Both pages are populated continuously by the
host. Switching between them via the buttons keeps state intact: come
back to a page and the chart / counter is exactly where you left it.

Run:
    make build         # produces web/dist
    cd api && uv run python ../examples/multipage.py

Then open http://127.0.0.1:8080.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import nu
import nu_virtuals as nv
from nu.shapes.flows.react import ReactForever
from nu.stdlib import TimeSleep
from nu.stdlib.asyncio import AsyncSleep
from nu_virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator

import nudle


WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


class Counter(nu.Shape):
    """rocksdb-backed counter."""

    value = nv.IntRef.slot()


class HomePage(nudle.Page):
    """Live counter, one button to nav to /feed."""

    heading = nudle.HeadingRef.slot()
    count = nudle.TextRef.slot()
    go_feed = nudle.ButtonRef.slot()


class FeedPage(nudle.Page):
    """Live chart, one button to nav back to /."""

    heading = nudle.HeadingRef.slot()
    history = nudle.LineChart.slot()
    go_home = nudle.ButtonRef.slot()


class App(nudle.Index):
    """Browser entrypoint: doc title, navigation, two pages."""

    title = nudle.TitleRef.slot()
    nav = nudle.NavRef.slot()
    pages = nudle.Pages({"/": HomePage, "/feed": FeedPage})


worker = nv.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nv.Transaction(Counter.value.store(Counter.value + 1)) >> TimeSleep(1.0),
)


# Both pages tick continuously. Switching between them never tears down
# state -- you come back and the chart is exactly where you left it.
tick_home = nu.ForeverDo(
    nv.Snapshot(HomePage.count.store(Counter.value)) >> AsyncSleep(1.0),
)

tick_feed = nu.ForeverDo(
    nv.Snapshot(FeedPage.history.append(Counter.value, Counter.value))
    >> AsyncSleep(1.0),
)

nav_home = ReactForever(HomePage.go_feed.clicked(), App.nav.store("/feed"))
nav_feed = ReactForever(FeedPage.go_home.clicked(), App.nav.store("/"))


ui = (
    App.title.store("nudle multipage")
    >> HomePage.heading.store("home")
    >> FeedPage.heading.store("feed")
    >> (tick_home | tick_feed | nav_home | nav_feed)
)


async def main() -> None:
    with rocksdb_storage_inmemory(".dbtest_mp") as storage:
        ctx = nu.Context().bind(Navigator, Navigator(storage))

        threading.Thread(
            target=lambda: nu.runtime.execute(worker, ctx),
            daemon=True,
        ).start()

        await nudle.serve(ui, ctx, host="127.0.0.1", port=8080, static_dir=WEB_DIST)


if __name__ == "__main__":
    asyncio.run(main())
