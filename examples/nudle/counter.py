"""End-to-end nudle smoke test: rocksdb-backed counter ticking on a worker
thread, browser tab showing the live count and a line chart of its history.

Run:
    make build         # produces web/dist
    cd api && uv run python ../examples/counter.py

Then open http://127.0.0.1:8080 in a browser.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import nu
import nu_virtuals as nv
import nudle
from nu.stdlib import TimeSleep
from nu.stdlib.asyncio import AsyncSleep
from nu_virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator


WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


class Counter(nu.Shape):
    """rocksdb-backed counter."""

    value = nv.IntRef.slot()


class Dashboard(nudle.Page):
    """nudle page rendered in a browser tab."""

    title = nudle.TitleRef.slot()
    count = nudle.IntRef.slot()
    history = nudle.LineChart.slot()


worker = nv.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nv.Transaction(Counter.value.store(Counter.value + 1)) >> TimeSleep(1.0),
)


ui = Dashboard.title.store("counter live") >> nu.ForeverDo(
    nv.Snapshot(
        Dashboard.count.store(Counter.value)
        | Dashboard.history.append(Counter.value, Counter.value),
    )
    >> AsyncSleep(1.0),
)
# Wall-clock x is what we want here, but nu has no Now() term yet, so we
# plot (counter, counter) for the smoke test. Chart line will be linear.


async def main() -> None:
    with rocksdb_storage_inmemory(".dbtest") as storage:
        ctx = nu.Context().bind(Navigator, Navigator(storage))

        threading.Thread(
            target=lambda: nu.runtime.execute(worker, ctx),
            daemon=True,
        ).start()

        await nudle.serve(ui, ctx, host="127.0.0.1", port=8080, static_dir=WEB_DIST)


if __name__ == "__main__":
    asyncio.run(main())
