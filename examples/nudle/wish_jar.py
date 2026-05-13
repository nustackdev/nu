"""Wish jar -- click the button to drop your wish into the jar.

Exercises every Ref type on both sides:

- TitleRef   server pushes the latest wish (or status)
- IntRef     server pushes the running wish count
- LineChart  server appends a point per wish
- InputRef   browser owns; server reads on every click
- ButtonRef  two of them: 'wish' and 'clear'

Server side is one ReactForever per button. The wish flow reads
`Dashboard.wish` straight from the tab (no cache), bumps a rocksdb-backed
counter, and writes the new title + tries + chart point. Clear resets
the rocksdb counter and the display state.

Run:
    make build
    cd api && uv run python ../examples/wish_jar.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import nu
import nu_virtuals as nv
import nudle
from nu.shapes.flows.react import ReactForever
from nu_virtuals.presets import rocksdb_storage_inmemory
from virtuals import Navigator


class Stats(nu.Shape):
    """Server-side state. Persistent across page reloads thanks to rocksdb."""

    count = nv.IntRef.slot()


class Dashboard(nudle.Page):
    title = nudle.TitleRef.slot()
    tries = nudle.IntRef.slot()
    history = nudle.LineChart.slot()
    wish = nudle.InputRef.slot()
    drop = nudle.ButtonRef.slot()
    clear = nudle.ButtonRef.slot()


init = nv.Transaction(
    nu.IfDo(Stats.count.missing(), Stats.count.store(0)),
)


on_drop = ReactForever(
    Dashboard.drop.clicked(),
    nv.Transaction(Stats.count.store(Stats.count + 1))
    >> nv.Snapshot(
        Dashboard.tries.store(Stats.count)
        | Dashboard.history.append(Stats.count, Stats.count)
        | Dashboard.title.store(Dashboard.wish),
    ),
)


on_clear = ReactForever(
    Dashboard.clear.clicked(),
    nv.Transaction(Stats.count.store(0))
    >> (
        Dashboard.tries.store(0)
        | Dashboard.title.store("the jar is empty")
        | Dashboard.history.store({"points": []})
    ),
)


hydrate = nv.Snapshot(
    Dashboard.title.store("drop a wish in the jar")
    | Dashboard.tries.store(Stats.count),
)


ui = init >> hydrate >> (on_drop | on_clear)


async def main() -> None:
    with rocksdb_storage_inmemory(".dbw") as storage:
        ctx = nu.Context().bind(Navigator, Navigator(storage))
        await nudle.serve(
            ui,
            ctx,
            host="127.0.0.1",
            port=8080,
            static_dir=Path(__file__).resolve().parent.parent / "web" / "dist",
        )


if __name__ == "__main__":
    asyncio.run(main())
