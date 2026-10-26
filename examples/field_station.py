"""Field station: a rich nudle page over the whole UI kit.

Breadcrumb and header, a sentence built from runs, a toolbar, a grid of live
stat cards, charts beside cards, a list whose items are sentences, a gallery
of keyed cards, one per species, a folded table, a sheet the
toolbar opens, and a modal that confirms clearing the log.
"""

import asyncio
import math

import nu
from nustd import ui


SPECIES = [
    ("Lion", "Panthera leo", "VU", 1240),
    ("African elephant", "Loxodonta africana", "EN", 610),
    ("Cheetah", "Acinonyx jubatus", "VU", 88),
    ("Plains zebra", "Equus quagga", "NT", 3120),
    ("Wildebeest", "Connochaetes taurinus", "LC", 9800),
    ("Spotted hyena", "Crocuta crocuta", "LC", 470),
    ("Giraffe", "Giraffa camelopardalis", "VU", 330),
    ("Leopard", "Panthera pardus", "VU", 140),
]

TONE = {"LC": "ok", "NT": "info", "VU": "warn", "EN": "danger"}


# --- header -------------------------------------------------------------------


class Header(ui.Row):
    who = ui.AvatarRef.slot(name="Serengeti Station", size="lg")
    title = ui.HeadingRef.slot(label="Serengeti field station")
    state = ui.StatusPillRef.slot(tone="info", label="Syncing")
    busy = ui.SpinnerRef.slot(size="sm", label="Pulling sightings")


class Intro(ui.Line):
    a = ui.TextRef.slot(value="Live counts from")
    src = ui.LinkRef.slot(label="iNaturalist", href="https://www.inaturalist.org")
    b = ui.TextRef.slot(value="and four camera traps, refreshed every few seconds. Status")
    dot = ui.StatusDotRef.slot(tone="ok", label="live")
    c = ui.TextRef.slot(value=", version")
    ver = ui.BadgeRef.slot(label="0.6", variant="info")
    d = ui.TextRef.slot(value=". Press")
    key = ui.ShortcutRef.slot(keys=["mod", "K"])
    e = ui.TextRef.slot(value="to search the atlas.")


class Toolbar(ui.Row):
    back = ui.ButtonRef.slot(icon="arrow-left", tooltip="Back", variant="ghost")
    reload = ui.ButtonRef.slot(icon="refresh-cw", tooltip="Reload", variant="ghost")
    wipe = ui.ButtonRef.slot(icon="trash-2", tooltip="Clear trap log", variant="ghost")
    sep = ui.DividerRef.slot()
    night = ui.ToggleRef.slot(icon="moon", label="Night traps")
    pins = ui.ToggleRef.slot(icon="pin", pressed=True)
    sep2 = ui.DividerRef.slot()
    pick = ui.SelectRef.slot(
        options=[s[0] for s in SPECIES], placeholder="Jump to species", searchable=True
    )
    edit = ui.ButtonRef.slot(label="Log sighting", icon="plus")


# --- live stats ---------------------------------------------------------------


class StatCard(ui.Card):
    stat = ui.StatRef.slot()
    spark = ui.Sparkline.slot(height=32)


class Stats(ui.Grid):
    sightings = StatCard.slot(title="Sightings")
    species = StatCard.slot(title="Species")
    traps = StatCard.slot(title="Camera traps")
    rain = StatCard.slot(title="Rainfall")


# --- charts beside cards ------------------------------------------------------


class Tags(ui.Line):
    migration = ui.BadgeRef.slot(label="migration", variant="info")
    predators = ui.BadgeRef.slot(label="predators", variant="warn")
    rains = ui.BadgeRef.slot(label="rains", variant="ok")


class Note(ui.Card):
    body = ui.TextRef.slot(
        value="Wildebeest move north after the short rains. Lion counts follow with a lag of a few weeks."
    )
    tags = Tags.slot()


class Trend(ui.Row):
    chart = ui.LineChart.slot(["Lion", "Zebra / 2"], x_label="day")
    note = Note.slot(title="Field note", subtitle="week 41")


class Mix(ui.Row):
    pie = ui.PieChart.slot(donut=True, total_label="sightings", labels=False, legend=True)
    bars = ui.BarChart.slot()


# --- keyed children: one per species -----------------------------------------


class Entry(ui.Line):
    name = ui.LinkRef.slot()
    status = ui.BadgeRef.slot()
    rest = ui.TextRef.slot()


class Watch(ui.Card):
    entries = ui.List.slot(Entry)


class Meta(ui.Line):
    iucn = ui.BadgeRef.slot()
    note = ui.TextRef.slot()


class SpeciesCard(ui.Card):
    count = ui.StatRef.slot(label="counted")
    meta = Meta.slot()


# --- folded table and sheet ---------------------------------------------------


class Log(ui.Collapsible):
    runs = ui.TableRef.slot(columns=["time", "trap", "species", "count"], row_key="time")


class NotesField(ui.Field):
    notes = ui.TextAreaRef.slot(placeholder="Behaviour, weather, anything odd", rows=3)


class SightingForm(ui.Form):
    species = ui.InputRef.slot(label="Species", placeholder="Panthera leo")
    count = ui.NumberInputRef.slot(label="Count")
    notes = NotesField.slot(label="Notes")
    save = ui.ButtonRef.slot(label="Save sighting")


class ConfirmActions(ui.Row):
    cancel = ui.ButtonRef.slot(label="Cancel", variant="secondary")
    confirm = ui.ButtonRef.slot(label="Clear log", icon="trash-2", variant="danger")


class ConfirmClear(ui.Modal):
    body = ui.TextRef.slot(
        value="This removes every entry from the trap log. Counts and the atlas stay as they are."
    )
    actions = ConfirmActions.slot(gap=2, justify="end")


class LogSheet(ui.Sheet):
    hint = ui.TextRef.slot(value="Saved sightings land in the log below.")
    form = SightingForm.slot()


# --- page ---------------------------------------------------------------------


class Home(ui.Container):
    trail = ui.BreadcrumbRef.slot(
        items=[{"label": "Stations", "href": "/"}, {"label": "Tanzania", "href": "/"}, "Serengeti"]
    )
    header = Header.slot(gap=3)
    intro = Intro.slot()
    toolbar = Toolbar.slot(gap=1)
    h_stats = ui.HeadingRef.slot(label="Today")
    stats = Stats.slot(columns=4, min_width=140, gap=3)
    h_trend = ui.HeadingRef.slot(label="Populations")
    trend = Trend.slot(wrap=True, min_width=320)
    mix = Mix.slot(wrap=True, min_width=280)
    h_watch = ui.HeadingRef.slot(label="Watch list")
    watch = Watch.slot(title="Species to watch", subtitle="IUCN status from the atlas")
    h_gallery = ui.HeadingRef.slot(label="Atlas")
    atlas = ui.Grid.slot(SpeciesCard, min_width=220, gap=3)
    log = Log.slot(title="Trap log")
    sheet = LogSheet.slot(title="Log a sighting", side="right")
    confirm = ConfirmClear.slot(title="Clear the trap log?")


class App(nu.Shape):
    home = Home.slot(size="dashboard")


h = App.home


def chain(*steps: nu.Nu) -> nu.Nu:
    out = steps[0]
    for step in steps[1:]:
        out = out >> step
    return out


def slug(name: str) -> str:
    return name.lower().replace(" ", "_")


atlas = []
for name, latin, status, count in SPECIES:
    card = h.atlas[slug(name)]
    atlas += [
        card.set_title(name),
        card.set_subtitle(latin),
        card.count.set(f"{count:,}", label="counted"),
        card.meta.iucn.set(status, variant=TONE[status]),
        card.meta.note.set("on the IUCN red list" if status != "LC" else "least concern"),
    ]

watch = []
for i, (name, _, status, count) in enumerate([s for s in SPECIES if s[2] != "LC"][:4]):
    entry = h.watch.entries[i]
    watch += [
        entry.name.set(href="https://www.iucnredlist.org", label=name),
        entry.status.set(status, variant=TONE[status]),
        entry.rest.set(f"{count:,} counted this season, down from last year."),
    ]

days = list(range(1, 31))
lions = [[d, round(1100 + 140 * math.sin(d / 5) + d * 3)] for d in days]
zebra = [[d, round(2900 + 260 * math.cos(d / 6) + d * 6)] for d in days]

seed = chain(
    *atlas,
    *watch,
    h.trend.chart.set({"Lion": lions, "Zebra / 2": [[x, y // 2] for x, y in zebra]}),
    h.mix.pie.set([["Mammals", 62], ["Birds", 24], ["Reptiles", 9], ["Insects", 5]]),
    h.mix.bars.set([["Trap A", 41], ["Trap B", 28], ["Trap C", 35], ["Trap D", 17]]),
    h.log.runs.set_rows(
        [
            {"time": "06:12", "trap": "A", "species": "Lion", "count": 3},
            {"time": "06:40", "trap": "C", "species": "Cheetah", "count": 1},
            {"time": "07:05", "trap": "B", "species": "Plains zebra", "count": 22},
        ]
    ),
)

# A day of ticks, replayed forever: stats move, sparklines grow, the pill settles.
ticks = []
for t in range(24):
    seen = 400 + t * 17 + (t % 5) * 9
    ticks += [
        h.stats.sightings.stat.set(f"{seen:,}", label="today", delta=f"+ {9 + t % 7}%", trend="up"),
        h.stats.sightings.spark.set([420 + k * 17 + (k % 5) * 9 for k in range(t + 2)]),
        h.stats.species.stat.set(str(31 + t // 4), label="seen", delta=f"+ {t // 4}", trend="up"),
        h.stats.species.spark.set([31 + k // 4 for k in range(t + 2)]),
        h.stats.traps.stat.set("4 / 4" if t % 9 else "3 / 4", label="online", trend="flat"),
        h.stats.traps.spark.set([4 if k % 9 else 3 for k in range(t + 2)]),
        h.stats.rain.stat.set(
            f"{t * 0.4:.1f} mm", label="since dawn", delta="- 2 mm", trend="down"
        ),
        h.stats.rain.spark.set([round(k * 0.4, 1) for k in range(t + 2)]),
        h.header.state.set("Live" if t > 2 else "Syncing", tone="ok" if t > 2 else "info"),
        h.header.busy.set("Refreshing" if t > 2 else "Pulling sightings"),
        nu.Delay(1.5),
    ]

program = seed >> nu.ParallelAsync(
    nu.ForeverDo(chain(*ticks)),
    nu.ReactForever(h.toolbar.edit.on_click(), h.sheet.set_open(True)),
    nu.ReactForever(h.sheet.form.save.on_click(), h.sheet.set_open(False)),
    nu.ReactForever(h.toolbar.wipe.on_click(), h.confirm.set_open(True)),
    nu.ReactForever(h.confirm.actions.cancel.on_click(), h.confirm.set_open(False)),
    nu.ReactForever(
        h.confirm.actions.confirm.on_click(),
        h.log.runs.set_rows([]) >> h.confirm.set_open(False),
    ),
)

app = ui.serve(ui.boot(App.home) >> program)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
