"""End-to-end nudle smoke test.

- rocksdb-backed counter ticks once a second (asyncio worker)
- browser dashboard shows the count, a line chart of its history,
  and an input + button to set a greeting that's echoed back as the title

Run:
    make build              # produces web/dist
    nudle run examples/counter.py
    # or, with hot reload:
    nudle dev examples/counter.py

Then open http://127.0.0.1:8080 in a browser.
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

from nu import nudle


if TYPE_CHECKING:
    from collections.abc import Iterator


class Counter(nu.Shape):
    """rocksdb-backed counter."""

    value = nv.IntRef.slot()


class Dashboard(nudle.Page):
    """The single page in this app. Display Refs only."""

    heading = nudle.HeadingRef.slot()
    count = nudle.TextRef.slot()
    history = nudle.LineChart.slot()
    name = nudle.InputRef.slot()
    greet = nudle.ButtonRef.slot()


class App(nudle.Index):
    """Browser entrypoint. Structural Refs + one page at /."""

    title = nudle.TitleRef.slot()
    nav = nudle.NavRef.slot()
    pages = nudle.Pages({"/": Dashboard})


# Background: bump the counter once a second (process-scoped, no session).
bg = nv.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nv.Transaction(Counter.value.store(Counter.value + 1)) >> sleep(1.0),
)

# UI flow: tick the dashboard + react to greet clicks.
ticking = nu.ForeverDo(
    nv.Snapshot(
        Dashboard.count.store(Counter.value + 1)
        | Dashboard.history.append(Counter.value, Counter.value),
    )
    >> sleep(1.0),
)
greeting = ReactForever(
    Dashboard.greet.clicked(),
    Dashboard.heading.store(Dashboard.name),
)


app = (
    App.title.store("nudle counter")
    >> Dashboard.heading.store("counter live")
    >> (ticking | greeting)
)


@contextmanager
def context() -> Iterator[nu.Context]:
    """Open rocksdb storage and yield a bound Context."""
    with rocksdb_storage_inmemory(".dbtest") as storage:
        yield nu.Context().bind(Navigator, Navigator(storage))
