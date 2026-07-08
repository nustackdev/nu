"""E2E bracket-tree Nu app: rocksdb preset + NudleServer + background bumper.

Same feel as ``examples/nudle/counter.py`` but assembled as one
``nu.With(...)`` tree instead of a hand-wired Context + CLI. The outer
bracket binds the rocksdb-navigator stack; ``NudleServer`` boots the ws
server on top; ``body`` is the process-scoped background loop that ticks
the counter once a second.

Run: python examples/brackets/nudle.py [--seconds N] [--host H] [--port P]

Then open http://127.0.0.1:8080 in a browser while it's up (default 10s).
"""

from __future__ import annotations

import argparse
import asyncio
import tempfile
from pathlib import Path

import nu
from nu.domains.shape import Shape


class Counter(Shape):
    """rocksdb-backed counter."""

    value: nu.v.IntRef


class Dashboard(nu.nd.Page):
    """The single page. Display Refs only."""

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


# --- Per-session UI program (one eval per ws connection) --------------------
ui = (
    App.title.store("nudle bracket counter")
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

# --- Process-scoped background: bump the counter once a second --------------
bg = nu.v.Transaction(
    nu.IfDo(Counter.value.missing(), Counter.value.store(0)),
) >> nu.ForeverDo(
    nu.v.Transaction(Counter.value.store(Counter.value + 1)) >> nu.Delay(1.0),
)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seconds", type=float, default=10.0,
                        help="how long to run before self-exit (default 10s)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "counter.db")
        tree = nu.With(
            nu.v.presets.rocksdb_navigator_inmemory(db_path),
            nu.nd.presets.server(ui, host=args.host, port=args.port),
            # Race the bumper against a bounded timer so the whole tree
            # completes cleanly. Swap `nu.Delay(args.seconds)` for
            # `nu.ForeverDo(nu.Delay(1.0))` to run indefinitely.
            body=(bg | nu.Delay(args.seconds)),
        )
        await nu.arun(tree, max_parallel=8)


if __name__ == "__main__":
    asyncio.run(main())
