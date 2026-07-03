"""Wish jar -- click the button to drop your wish into the jar.

Exercises every Ref type on both sides:

- TitleRef   server pushes the latest wish (or status)
- FloatRef   server pushes the running wish count (precision=0)
- LineChart  server appends a point per wish
- InputRef   browser owns; server reads on every click
- ButtonRef  two of them: 'wish' and 'clear'

Server side is one ReactForever per button. The wish flow reads
`Dashboard.wish` straight from the tab (no cache), bumps a rocksdb-backed
counter, and writes the new title + tries + chart point. Clear resets
the rocksdb counter and the display state.

Run:
    nudle run examples/wish_jar.py
    # or, with hot reload:
    nudle dev examples/wish_jar.py
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import nu
import nu.virtuals as nv
from nu import ReactForever
from nu.virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator


if TYPE_CHECKING:
    from collections.abc import Iterator

import nudle


class Stats(nu.Shape):
    """Server-side state. Persistent across page reloads thanks to rocksdb."""

    count = nv.IntRef.slot()


class Dashboard(nudle.Page):
    """Single page: title, count, history, wish input, drop + clear buttons."""

    heading = nudle.HeadingRef.slot()
    tries = nudle.TextRef.slot()
    history = nudle.LineChart.slot()
    wish = nudle.InputRef.slot()
    drop = nudle.ButtonRef.slot()
    clear = nudle.ButtonRef.slot()


class App(nudle.Index):
    """Browser entrypoint: doc title, nav, and the one dashboard page."""

    title = nudle.TitleRef.slot()
    nav = nudle.NavRef.slot()
    pages = nudle.Pages({"/": Dashboard})


init = nv.Transaction(
    nu.IfDo(Stats.count.missing(), Stats.count.store(0)),
)


on_drop = ReactForever(
    Dashboard.drop.clicked(),
    nv.Transaction(Stats.count.store(Stats.count + 1))
    >> nv.Snapshot(
        Dashboard.tries.store(Stats.count)
        | Dashboard.history.append(Stats.count, Stats.count)
        | Dashboard.heading.store(Dashboard.wish),
    ),
)


on_clear = ReactForever(
    Dashboard.clear.clicked(),
    nv.Transaction(Stats.count.store(0))
    >> (
        Dashboard.tries.store(0)
        | Dashboard.heading.store("the jar is empty")
        | Dashboard.history.store({"points": []})
    ),
)


hydrate = nv.Snapshot(
    Dashboard.heading.store("drop a wish in the jar")
    | Dashboard.tries.store(Stats.count),
)


app = init >> App.title.store("wish jar") >> hydrate >> (on_drop | on_clear)


@contextmanager
def context() -> Iterator[nu.Context]:
    """Open rocksdb storage and yield a bound Context."""
    with rocksdb_storage_inmemory(".dbw") as storage:
        yield nu.Context().bind(Navigator, Navigator(storage))
