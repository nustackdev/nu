"""Dashboard: an ops board for a small service fleet, display only.

The data is made up and nothing is live; the page is here to read the ui
access model end to end. Two styles meet on it:

- declared: a Shape names its children as slots (``Header``, ``Tile``,
  ``Home``) and code reaches them as attributes, ``home.header.state``
- descended: a container reaches a child by key and names its kind where it
  is used, ``board[2, 0].to(ui.CardRef)``. Flow containers take ``[i]`` and
  ``["k"]``, a placed grid and a content table take ``[r, c]``, tabs and
  accordions take their ids, a card has ``.media``, ``.actions`` and
  ``.footer`` besides its body

Run it, then open http://localhost:8098:

    .venv/bin/python examples/dashboard.py
"""

import asyncio
import time

import nu
from nustd import ui


NOW = time.time() * 1000
MINUTE = 60_000


# ---- declared parts ---------------------------------------------------------


class Header(ui.Row):
    title = ui.HeadingRef.slot(
        label="Harbor",
        eyebrow="Production, eu-west",
        subtitle="Service fleet over the last 24 hours",
    )
    state = ui.StatusPillRef.slot(tone="warn", label="1 degraded, 1 down")
    docs = ui.ButtonRef.slot(label="Runbook", icon="book-open", variant="outline")


class Tile(ui.Card):
    # A slot named after a card part draws in that part: the trend line sits
    # in the card's media place, the stat in its body.
    media = ui.Sparkline.slot(area=True, height=40)
    stat = ui.StatRef.slot()


class Home(ui.Container):
    header = Header.slot(gap=3, grow={"title": 1})
    notice = ui.AlertRef.slot(
        variant="warn",
        title="billing p95 above 400 ms since 09:40",
        body="The autoscaler is at its cap. Follow the runbook before paging payments.",
        dismissible=True,
    )
    overview = ui.PageSectionRef.slot(title="Overview", description="Traffic, health, budget")
    services = ui.PageSectionRef.slot(title="Services", description="What runs and what shipped")
    activity = ui.PageSectionRef.slot(title="Activity", description="Queue and event stream")
    runbook = ui.ModalRef.slot(title="Runbook: billing degraded", size="lg")


class App(nu.Shape):
    home = Home.slot(size="dashboard", gap=8)


home = App.home


# ---- data -------------------------------------------------------------------

TILES = [
    ("Requests", "1.28M", "+4.2%", "up", [31, 34, 33, 38, 41, 39, 44, 47, 45, 52]),
    ("Error rate", "0.41%", "+0.12 pt", "up", [2, 2, 3, 2, 4, 3, 5, 6, 5, 7]),
    ("p95 latency", "212 ms", "-8 ms", "down", [240, 236, 228, 231, 222, 219, 215, 214, 210, 212]),
    ("Saturation", "63%", "+3%", "up", [52, 55, 54, 58, 57, 60, 61, 59, 62, 63]),
]

REGIONS = [
    ("eu-west-1", "ok", "38 ms", "ok"),
    ("eu-central-1", "ok", "44 ms", "ok"),
    ("us-east-1", "warn", "171 ms", "warn"),
    ("ap-south-1", "danger", "timeout", "danger"),
]

HOURS = [f"{h:02d}:00" for h in range(0, 24, 2)]
TRAFFIC = {
    "2xx": [
        [h, v]
        for h, v in zip(
            HOURS, [410, 380, 350, 420, 610, 820, 940, 910, 870, 800, 690, 520], strict=True
        )
    ],
    "4xx": [
        [h, v] for h, v in zip(HOURS, [22, 20, 18, 25, 31, 44, 52, 49, 47, 40, 35, 28], strict=True)
    ],
    "5xx": [[h, v] for h, v in zip(HOURS, [2, 1, 1, 3, 4, 9, 21, 18, 7, 5, 3, 2], strict=True)],
}

# name, owner, version, status, tone, p95 ms, pods
SERVICES = [
    ("api-gateway", "edge", "v2.14.1", "healthy", "ok", 84, 6),
    ("auth", "identity", "v1.9.0", "healthy", "ok", 41, 3),
    ("billing", "payments", "v3.2.0-rc1", "degraded", "warn", 431, 4),
    ("search", "discovery", "v0.18.4", "healthy", "ok", 118, 5),
    ("media-worker", "media", "v5.0.2", "down", "danger", 0, 0),
    ("notifier", "growth", "v1.3.7", "healthy", "ok", 66, 2),
]

DEPLOYS = [
    {
        "id": "d-4821",
        "service": "billing",
        "env": {"label": "canary", "variant": "brand"},
        "state": {"label": "rolling", "tone": "info"},
        "progress": 0.4,
        "started": NOW - 6 * MINUTE,
        "by": "mara",
    },
    {
        "id": "d-4820",
        "service": "search",
        "env": "prod",
        "state": {"label": "done", "tone": "ok"},
        "progress": 1.0,
        "started": NOW - 52 * MINUTE,
        "by": "ci",
    },
    {
        "id": "d-4819",
        "service": "media-worker",
        "env": "prod",
        "state": {"label": "rolled back", "tone": "danger"},
        "progress": 0.75,
        "started": NOW - 3 * 60 * MINUTE,
        "by": "lev",
    },
    {
        "id": "d-4818",
        "service": "auth",
        "env": {"label": "staging", "variant": "secondary"},
        "state": {"label": "waiting", "tone": "neutral"},
        "progress": 0.0,
        "started": NOW - 5 * 60 * MINUTE,
        "by": "ci",
    },
]

INCIDENTS = [
    (
        "inc-212",
        "INC-212 billing latency",
        "open",
        "warn",
        "Write lock on invoices since the 09:40 deploy.",
    ),
    (
        "inc-211",
        "INC-211 media-worker crash loop",
        "open",
        "danger",
        "OOM on 4K transcodes after v5.0.2.",
    ),
    (
        "inc-207",
        "INC-207 auth token skew",
        "resolved",
        "ok",
        "NTP drift on two nodes, fixed by resync.",
    ),
]

JOBS = {
    "backfill": "Backfill orders, March",
    "rotate": "Rotate signing keys",
    "reindex": "Reindex search (failed, retry)",
    "vacuum": "Vacuum analytics db",
}

EVENTS = [
    (2, "warn", "billing p95 crossed 400 ms"),
    (6, "info", "d-4821 canary started at 10%"),
    (11, "danger", "media-worker exited 137, restart 14"),
    (18, "info", "autoscaler billing 3 -> 4 pods"),
    (25, "ok", "search d-4820 promoted to prod"),
    (34, "info", "cache hit ratio back to 0.94"),
    (47, "danger", "ap-south-1 probe timeout"),
    (58, "ok", "auth INC-207 resolved"),
    (73, "info", "nightly export finished, 4.1 GB"),
    (96, "info", "cert renewal scheduled for Friday"),
]

RUNBOOK = """\
## billing degraded

1. Check the canary: **Deploys** tab, `d-4821`. Roll it back if p95 is still above 400 ms.
2. Look for long write locks on `invoices`.
3. Page payments only if the rollback does not bring p95 under 250 ms in 10 minutes.

| step | owner | budget |
|---|---|---|
| rollback | on call | 5 min |
| lock check | on call | 10 min |
| page | payments | - |
"""


# ---- overview: a placed board -----------------------------------------------
#
#   [ tiles   ][ regions ]
#   [ traffic ][ regions ]   regions spans two rows
#   [ latency ][ budget  ]

board = home.overview[0].to(
    ui.GridRef.slot(
        cols="2fr 1fr",
        rows=["auto", "minmax(280px, auto)", "auto"],
        spans={(0, 1): (1, 2)},
        gap=4,
        stack_below=800,
    )
)
export = home.overview.actions[0].to(ui.ButtonRef.slot(variant="ghost", size="sm", icon="download"))

# A flowing grid inside a placed one: tiles wrap by width, no places.
tiles = board[0, 0].to(ui.GridRef.slot(max_columns=4, min_width=160, gap=3))


def tile(i: int, label: str, value: str, delta: str, trend: str, points: list[int]) -> nu.Nu:
    t = tiles[i].to(Tile.slot(size="sm"))
    return nu.Sequential(
        t.stat.set(value, label=label, delta=delta, trend=trend), t.media.set(points)
    )


regions = board[0, 1].to(ui.CardRef.slot(title="Regions", subtitle="synthetic probes"))
probe_lines = regions[0].to(ui.ColumnRef.slot(ui.LineRef, gap=3))
probes = regions[1].to(
    ui.StatusSquaresRef.slot(max_items=24, labels={"danger": "failed", "warn": "slow"})
)
regions_note = regions.footer[0].to(ui.TextRef.slot(tone="muted", size="sm"))


def region(i: int, name: str, tone: str, latency: str, variant: str) -> nu.Nu:
    line = probe_lines[i]  # a LineRef already: the column's item= names the kind
    return nu.Sequential(
        line[0].to(ui.StatusDotRef).set(tone, label=name),
        line[1].to(ui.TextRef).set(name),
        line[2].to(ui.BadgeRef.slot(size="sm")).set(latency, variant),
    )


traffic = board[1, 0].to(ui.CardRef.slot(title="Traffic", subtitle="requests per second, by class"))
traffic_chart = traffic[0].to(
    ui.AreaChart.slot(["2xx", "4xx", "5xx"], x_type="category", stack=True, smooth=True, height=240)
)
RANGES = ["1h", "24h", "7d"]
ranges = [
    traffic.actions[i].to(
        ui.ButtonRef.slot(variant="secondary" if r == "24h" else "ghost", size="xs")
    )
    for i, r in enumerate(RANGES)
]

latency = board[2, 0].to(ui.CardRef.slot(title="p95 by service"))
latency_chart = latency[0].to(
    ui.BarChart.slot(horizontal=True, labels=True, value_format="{value} ms", height=220)
)

budget = board[2, 1].to(ui.CardRef.slot(title="Error budget", subtitle="30 day SLO, 99.9%"))
budget_gauge = budget[0].to(ui.GaugeRef.slot(variant="warn"))
budget_spent = budget[1].to(ui.ProgressRef)


# ---- services: tabs ---------------------------------------------------------

views = home.services[0].to(
    ui.TabsRef.slot(
        tabs=[
            {"id": "fleet", "label": "Fleet"},
            {"id": "deploys", "label": "Deploys"},
            {"id": "incidents", "label": "Incidents"},
        ],
        active="fleet",
    )
)
new_deploy = home.services.actions[0].to(ui.ButtonRef.slot(icon="rocket", size="sm"))

# Fleet: a content table, every cell a place that holds any kind.
fleet = views["fleet"].to(
    ui.TableRef.slot(
        header=["Service", "Version", "Status", "p95", ""],
        align=["left", "left", "left", "right", "right"],
        label="Fleet",
    )
)
fleet_title = fleet.header[0].to(ui.LineRef)
RESTART = ui.ButtonRef.slot(label="Restart", icon="rotate-ccw", variant="ghost", size="xs")


def service_row(
    r: int, name: str, owner: str, version: str, status: str, tone: str, p95: int, pods: int
) -> nu.Nu:
    who = fleet[r, 0].to(ui.ColumnRef.slot(gap=0))
    actions = fleet[r, 4].to(ui.RowRef.slot(gap=2, justify="end"))
    return nu.Sequential(
        who[0].to(ui.TextRef.slot(weight="medium")).set(name),
        who[1].to(ui.TextRef.slot(tone="muted", size="sm")).set(owner),
        fleet[r, 1].to(ui.TextRef.slot(mono=True, size="sm")).set(version),
        fleet[r, 2].to(ui.StatusPillRef).set(status, tone=tone),
        fleet[r, 3].to(ui.TextRef.slot(mono=True)).set(f"{p95} ms" if p95 else "-"),
        actions[0].to(ui.BadgeRef.slot(variant="neutral", size="sm")).set(f"{pods} pods"),
        actions[1].to(RESTART).init(),
    )


# The same address reached again from the top is the same ref: this is the
# Restart button service_row put in billing's row (2) last cell (4).
restart_billing = (
    home.services[0].to(ui.TabsRef)["fleet"].to(ui.TableRef)[2, 4].to(ui.RowRef)[1].to(ui.ButtonRef)
)
billing_status = fleet[2, 2].to(ui.StatusPillRef)

# Deploys: a data table, rows are values; each column's cell spec draws them.
deploys = views["deploys"].to(
    ui.DataTableRef.slot(
        columns=[
            {"key": "id", "label": "Deploy"},
            {"key": "service", "label": "Service"},
            {"key": "env", "label": "Env", "cell": ui.BadgeRef.slot(variant="neutral", size="sm")},
            {"key": "state", "label": "State", "cell": ui.StatusPillRef},
            {"key": "progress", "label": "Progress", "cell": ui.ProgressRef},
            {"key": "started", "label": "Started", "cell": ui.RelativeTimeRef},
            {"key": "by", "label": "By"},
        ],
        row_key="id",
        label="Deploys",
    )
)

# Incidents: an accordion, each section a column of text and tags.
incidents = views["incidents"].to(
    ui.AccordionRef.slot(
        ui.ColumnRef.slot(gap=2),
        sections=[{"id": key, "label": label} for key, label, *_ in INCIDENTS],
        open=["inc-212"],
    )
)


def incident(key: str, state: str, variant: str, note: str) -> nu.Nu:
    body = incidents[key]
    tags = body[1].to(ui.LineRef)
    return nu.Sequential(
        body[0].to(ui.TextRef).set(note),
        tags[0].to(ui.BadgeRef.slot(size="sm")).set(state, variant),
        tags[1].to(ui.BadgeRef.slot(variant="dashed", size="sm")).set("no postmortem"),
    )


# ---- activity: a row of two cards, the feed grows twice as fast -------------

lanes = home.activity[0].to(ui.RowRef.slot(gap=4, align="stretch", grow={0: 1, 1: 2}, wrap=True))

queue_card = lanes[0].to(ui.CardRef.slot(title="Job queue", subtitle="next up first"))
queue = queue_card[0].to(ui.ListRef.slot(ui.TextRef, variant="number"))
retry = queue_card.actions[0].to(
    ui.ButtonRef.slot(label="Retry reindex", variant="outline", size="xs")
)
workers = queue_card.footer[0].to(ui.TextRef.slot(tone="muted", size="sm"))

feed_card = lanes[1].to(ui.CardRef.slot(title="Events", subtitle="newest first"))
feed = feed_card[0].to(ui.ColumnRef.slot(ui.LineRef, gap=2, max_height=220, scroll="y"))


def event(i: int, minutes_ago: int, level: str, text: str) -> nu.Nu:
    line = feed[i]
    return nu.Sequential(
        line[0].to(ui.RelativeTimeRef).set(NOW - minutes_ago * MINUTE),
        line[1].to(ui.BadgeRef.slot(size="sm")).set(level, level),
        line[2].to(ui.TextRef).set(text),
    )


notes = home.activity[1].to(ui.CollapsibleRef.slot(title="On-call notes"))
notes_body = notes[0].to(ui.MarkdownRef)


# ---- program ----------------------------------------------------------------

seed = nu.Sequential(
    # overview
    export.set("Export"),
    *(tile(i, *t) for i, t in enumerate(TILES)),
    *(region(i, *r) for i, r in enumerate(REGIONS)),
    probes.set({"ok": 33, "warn": 4, "danger": 3}),
    regions_note.set("Probes every 30 s from 6 sites"),
    traffic_chart.set(TRAFFIC),
    *(b.set(r) for b, r in zip(ranges, RANGES, strict=True)),
    latency_chart.set({name: p95 for name, *_, p95, _ in reversed(SERVICES)}),
    budget_gauge.set_value(0.62),
    budget_spent.set(0.38, caption="38% spent, 17 days left"),
    # services
    new_deploy.set("New deploy"),
    fleet_title[0].to(ui.TextRef).set("Service"),
    fleet_title[1].to(ui.BadgeRef.slot(size="sm")).set(str(len(SERVICES))),
    *(service_row(r, *s) for r, s in enumerate(SERVICES)),
    deploys.set_rows(DEPLOYS),
    *(incident(key, state, variant, note) for key, _, state, variant, note in INCIDENTS),
    # activity
    *(queue[key].set(text) for key, text in JOBS.items()),
    retry.init(),
    workers.set("4 workers, 1 busy"),
    *(event(i, *e) for i, e in enumerate(EVENTS)),
    notes_body.set(
        "- **mara** on call until 18:00, then **lev**\n- payments wants a heads up before any billing rollback"
    ),
    home.runbook[0].to(ui.MarkdownRef).set(RUNBOOK),
)

program = seed >> nu.ParallelAsync(
    nu.ReactEvery(home.header.docs.on_click(), home.runbook.set_open(True)),
    nu.ReactEvery(retry.on_click(), queue.move("reindex", at=0)),
    nu.ReactEvery(
        restart_billing.on_click(),
        billing_status.set("restarting", tone="info") >> restart_billing.set_disabled(True),
    ),
)

app = ui.serve(ui.boot(App.home) >> program, port=8098)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
