"""End-to-end nudle smoke test.

- rocksdb-backed counter ticks once a second (asyncio worker)
- browser dashboard shows the count, a line chart of its history,
  and an input + button to set a greeting that's echoed back as the title

Run: nudle dev examples/counter.py
Then open http://127.0.0.1:8080 in a browser.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import nu
from virtuals import Navigator


if TYPE_CHECKING:
    from collections.abc import Iterator


class Counter(nu.Shape):
    """rocksdb-backed counter."""

    value: nu.v.IntRef


class Dashboard(nu.nd.Page):
    """The single page in this app. Display Refs only."""

    heading: nu.nd.HeadingRef
    count:   nu.nd.TextRef
    history: nu.nd.LineChart
    name:    nu.nd.InputRef
    greet:   nu.nd.ButtonRef


class App(nu.nd.Index):
    """Browser entrypoint. Structural Refs + one page at /."""

    title: nu.nd.TitleRef
    nav:   nu.nd.NavRef
    pages = nu.nd.Pages({"/": Dashboard})


# Background: bump the counter once a second (process-scoped, no session).
bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)

# UI flow: tick the dashboard + react to greet clicks.
app = (
    App.title.store("nudle counter")
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


@contextmanager
def context() -> Iterator[nu.Context]:
    """Open rocksdb storage and yield a bound Context."""
    with nu.v.presets.rocksdb_storage_inmemory(".dbtest") as storage:
        yield nu.Context().bind(Navigator, Navigator(storage))
