"""Multi-page nudle smoke test.

Two pages, one Index. Both pages are populated continuously by the
host. Switching between them via the buttons keeps state intact: come
back to a page and the chart / counter is exactly where you left it.

Run:
    nudle run examples/multipage.py
    # or, with hot reload:
    nudle dev examples/multipage.py

Then open http://127.0.0.1:8080.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import nu
import nu.virtuals as nv
from nu import ReactForever
from nu.std.asyncio import sleep
from nu.virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator

import nudle


if TYPE_CHECKING:
    from collections.abc import Iterator


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


bg = nv.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nv.Transaction(Counter.value.store(Counter.value + 1)) >> sleep(1.0),
)


# Both pages tick continuously. Switching between them never tears down
# state -- you come back and the chart is exactly where you left it.
tick_home = nu.ForeverDo(
    nv.Snapshot(HomePage.count.store(Counter.value)) >> sleep(1.0),
)

tick_feed = nu.ForeverDo(
    nv.Snapshot(FeedPage.history.append(Counter.value, Counter.value))
    >> sleep(1.0),
)

nav_home = ReactForever(HomePage.go_feed.clicked(), App.nav.store("/feed"))
nav_feed = ReactForever(FeedPage.go_home.clicked(), App.nav.store("/"))


app = (
    App.title.store("nudle multipage")
    >> HomePage.heading.store("home")
    >> FeedPage.heading.store("feed")
    >> (tick_home | tick_feed | nav_home | nav_feed)
)


@contextmanager
def context() -> Iterator[nu.Context]:
    """Open rocksdb storage and yield a bound Context."""
    with rocksdb_storage_inmemory(".dbtest_mp") as storage:
        yield nu.Context().bind(Navigator, Navigator(storage))
