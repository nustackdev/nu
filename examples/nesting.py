"""Nesting: one page reached by descent alone, as deep as it goes.

No Shape below the page: every child is reached from its container and named
with ``.to(Kind)`` where it is used, so one container holds children of any
kind. On the page:

- a placed grid (``cols="2fr 1fr"``) of four cells
- a card holding a content table; a table cell holds a row of a button and a
  badge, and the card's ``.actions`` hold a refresh button
- a grid inside a grid cell, four stats on a 2 by 2 board
- a DataTableRef (rows are data) whose status column draws as badges
- a List of keyed jobs that buttons insert into, move and remove from
- a column capped at 180px that scrolls

Run it, then open http://localhost:8097:

    .venv/bin/python examples/nesting.py

The page needs a nudle build that knows ``Table`` and ``DataTableRef``. Until
the shipped one is rebuilt, run the SPA from source against this server:

    cd pkgs/ts/nudle && NUDLE_WS_PORT=8097 npm run dev
"""

import asyncio

import nu
import nustd
from nustd import ui


class App(nu.Shape):
    home = ui.ContainerRef.slot(max_width="dashboard", gap=4)


class Store(nu.Shape):
    jobs = nustd.kv.IntRef.slot()
    refreshes = nustd.kv.IntRef.slot()


page = App.home

PUMPS = [
    ("P-101", "Feed pump", "ok", "ok"),
    ("P-102", "Return pump", "late", "warn"),
    ("P-103", "Spare", "down", "danger"),
]


# ---- the board: a placed grid ----------------------------------------------

title = page["title"].to(ui.HeadingRef)
board = page["board"].to(ui.GridRef.slot(cols="2fr 1fr", gap=4, span={(1, 0): 2}))


# (0, 0): a card holding a content table, a row of a button and a badge per cell
pumps = board[0, 0].to(ui.CardRef.slot(title="Pumps", subtitle="a content table in a card"))
specs = pumps[0].to(ui.TableRef.slot(columns=["Pump", "Role", {"key": "State", "align": "end"}]))
refresh = pumps.actions[0].to(ui.ButtonRef.slot(variant="outline", size="sm"))
refreshed = pumps.actions[1].to(ui.BadgeRef.slot(variant="info"))


def pump_row(r: int, tag: str, role: str, state: str, tone: str) -> nu.Nu:
    """One table row: text, text, and a row of a button beside a badge."""
    actions = specs[r, 2].to(ui.RowRef.slot(gap=2, justify="end"))
    return nu.Sequential(
        specs[r, 0].to(ui.TextRef).set(tag),
        specs[r, 1].to(ui.TextRef).set(role),
        actions[0].to(ui.BadgeRef).set(state, tone),
        actions[1].to(ui.ButtonRef.slot(variant="ghost", size="sm")).set("Open"),
    )


# (0, 1): a grid inside a grid cell
stats = board[0, 1].to(ui.GridRef.slot(cols=2, gap=2))
STATS = [("Flow", "42 m3/h"), ("Head", "18 m"), ("Power", "7.5 kW"), ("Uptime", "99.2%")]


# (1, 0), two columns wide: rows that are data, a status column drawn as badges
runs = board[1, 0].to(ui.CardRef.slot(title="Runs", subtitle="DataTableRef with a badge column"))
log = runs[0].to(
    ui.DataTableRef.slot(
        columns=[
            {"key": "run", "label": "Run"},
            {"key": "pump", "label": "Pump"},
            {"key": "status", "label": "Status", "cell": ui.BadgeRef.slot(variant="info")},
            {"key": "litres", "label": "Litres", "kind": "number", "align": "end"},
        ],
        row_key="run",
        label="Runs",
    )
)
# A mapping cell merges over the column's badge spec, so each run's status
# carries its own variant; a bare string would take the spec's "info".
RUNS = [
    {"run": "r1", "pump": "P-101", "status": {"label": "done", "variant": "ok"}, "litres": 1200},
    {"run": "r2", "pump": "P-102", "status": {"label": "late", "variant": "warn"}, "litres": 640},
    {
        "run": "r3",
        "pump": "P-101",
        "status": {"label": "running", "variant": "info"},
        "litres": 310,
    },
]


# (2, 0): a keyed List the buttons rearrange
queue = board[2, 0].to(ui.CardRef.slot(title="Queue", subtitle="List ops, keys stay with items"))
controls = queue[0].to(ui.RowRef.slot(gap=2, wrap=True))
jobs = queue[1].to(ui.ListRef.slot(ui.TextRef, variant="number"))
BUTTONS = ["Add on top", "Deploy to top", "Remove lint", "Keep 3"]
add, raise_deploy, drop_lint, keep_three = (
    controls[i].to(ui.ButtonRef.slot(variant="outline", size="sm")) for i in range(len(BUTTONS))
)


# (2, 1): a column capped at 180px that scrolls
feed = board[2, 1].to(ui.CardRef.slot(title="Feed", subtitle="max_height 180, scrolls"))
lines = feed[0].to(ui.ColumnRef.slot(ui.TextRef, gap=1, max_height=180, scroll="y"))


# ---- program ----------------------------------------------------------------


seed = nu.Sequential(
    title.set("Nesting"),
    *(pump_row(r, *p) for r, p in enumerate(PUMPS)),
    refresh.set("Refresh"),
    refreshed.set("refreshed 0"),
    *(
        stats[i // 2, i % 2].to(ui.StatRef).set(value, label=label)
        for i, (label, value) in enumerate(STATS)
    ),
    log.set_rows(RUNS),
    *(
        b.set(label)
        for b, label in zip((add, raise_deploy, drop_lint, keep_three), BUTTONS, strict=True)
    ),
    *(jobs[k].set(k) for k in ("build", "lint", "test", "deploy")),
    *(lines[i].set(f"{6 + i // 4:02d}:{(i * 15) % 60:02d} reading {i}") for i in range(24)),
)


def new_job() -> nu.Nu:
    """A fresh key each click, inserted at the top with its text."""
    key = nu.Str("job") + nu.str(Store.jobs)
    return Store.jobs.inc() >> jobs.insert(jobs[key], at=0) >> jobs[key].set(key)


program = (Store.jobs.init(0) >> Store.refreshes.init(0) >> seed) >> nu.ParallelAsync(
    nu.ReactEvery(add.on_click(), new_job()),
    nu.ReactEvery(raise_deploy.on_click(), jobs.move("deploy", at=0)),
    nu.ReactEvery(drop_lint.on_click(), jobs.remove("lint")),
    nu.ReactEvery(keep_three.on_click(), jobs.truncate(3)),
    nu.ReactEvery(
        refresh.on_click(),
        Store.refreshes.inc() >> refreshed.set(nu.Str("refreshed ") + nu.str(Store.refreshes)),
    ),
)

app = nu.With(
    nustd.kv.memory_navigator(),
    body=ui.serve(ui.boot(App.home) >> nustd.kv.auto_flow_atomic(program), port=8097),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
