"""End-to-end nudle example: a kh57-backed live-sampled series.

- rocksdb-backed kh57 map grows one random int per key every 10 ms.
- The dashboard redraws a sorted downsample every 100 ms.
- A numeric input controls the sample size (browser is source of truth).

Run:
    nudle run examples/nudle/kh57_stream.py
Then open http://127.0.0.1:8080 in a browser.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import nu
import nu.std.random as nurandom
from virtuals import Navigator


if TYPE_CHECKING:
    from collections.abc import Iterator


class Series(nu.Shape):
    """Growing kh57 int series with a monotonic height counter."""

    height = nu.v.IntRef.slot()
    entries = nu.v.Kh57Ref.slot(int)


class Dashboard(nu.nd.Page):
    """One page: heading + count + chart + sample-size input."""

    heading = nu.nd.HeadingRef.slot()
    count = nu.nd.TextRef.slot()
    chart = nu.nd.LineChart.slot()
    n = nu.nd.NumberInputRef.slot()


class App(nu.nd.Index):
    """Browser entrypoint."""

    title = nu.nd.TitleRef.slot()
    nav = nu.nd.NavRef.slot()
    pages = nu.nd.Pages({"/": Dashboard})


# Background: seed height=0, then push one random int per tick every 10 ms.
bg = nu.v.Transaction(
    nu.IfDo(Series.height.missing(), Series.height.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(
        Series.entries.set(Series.height, nurandom.randint(0, 100))
        >> Series.height.store(Series.height + 1),
    )
    >> nu.Delay(0.001),
)


# UI: seed labels + input, then every 100 ms redraw a sorted downsample.
app = (
    App.title.store("kh57 sample stream")
    >> Dashboard.heading.store("kh57 live sample")
    >> Dashboard.n.store(200, min=10, max=2000, step=10, label="sample size")
    >> nu.ForeverDo(
        nu.v.Snapshot(
            Dashboard.chart.store_points(
                nu.CollectQuery(
                    nu.SortedQuery(
                        Series.entries.sample(Dashboard.n, 0, Series.height),
                    ),
                )
            )
            | Dashboard.count.store(nu.StrQuery(Series.height)),
        )
        >> nu.Delay(0.1),
    )
)


@contextmanager
def context() -> Iterator[nu.Context]:
    """Open an in-memory rocksdb store and yield a bound Context."""
    with nu.v.presets.rocksdb_storage_inmemory(".dbtest-kh57") as storage:
        yield nu.Context().bind(Navigator, Navigator(storage))
