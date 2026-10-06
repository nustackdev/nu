"""Tables - every table the kit has, on one page, to play with.

Three cards, top to bottom:

- **Simple.** A read-only TableRef: the server sorts it when a header is
  clicked, and a row click says which planet it was. Nothing else is on.
- **Data.** An editable TableRef kept by ``nustd.ui.table.sync``: edit cells,
  select, add, delete and move rows, and add, rename, move, retype, align or
  delete columns, from the row and column handles, the right-click menu or the
  keyboard. Every change is stored as asked, and a second tab shows it live.
- **Markdown.** An editable MarkdownRef holding a table (and a fence): type
  ``| a | b |`` then Enter for a new one, or use its handles. Every commit is
  stored and drawn twice below it: as a read-only MarkdownRef, the same
  table with editing off, and as the markdown source in a read-only CodeRef.

Everything persists in RocksDB under ``.dbtables``, so the page survives a
restart. For a table with an app's own rules in front of the store
(validation, refusals, a status line), see ``examples/table.py``.

Run it and open http://localhost:8095 (twice, to see the data table sync):

    .venv/bin/python examples/tables.py
"""

import nu
import nustd


_PLANETS = [
    {"name": "Mercury", "moons": 0, "radius_km": 2440, "rings": False},
    {"name": "Venus", "moons": 0, "radius_km": 6052, "rings": False},
    {"name": "Earth", "moons": 1, "radius_km": 6371, "rings": False},
    {"name": "Mars", "moons": 2, "radius_km": 3390, "rings": False},
    {"name": "Jupiter", "moons": 95, "radius_km": 69911, "rings": True},
    {"name": "Saturn", "moons": 146, "radius_km": 58232, "rings": True},
]

_TASKS = {
    "t1": {"task": "Sketch the handles", "hours": 3, "done": True, "owner": "gor"},
    "t2": {"task": "Column requests", "hours": 5, "done": True, "owner": "sonny"},
    "t3": {"task": "Sync preset", "hours": 8, "done": False, "owner": "sonny"},
    "t4": {"task": "Table cell snippet", "hours": 2, "done": False, "owner": "gor"},
}

_NOTES = """# Release notes

| Feature | Status | Owner |
| :--- | :---: | ---: |
| Shared table handles | done | gor |
| Column requests | done | sonny |
| Table sync preset | done | sonny |

Tab through the cells, or use the handles on a row's edge and a column's header.

```python
TABLE.on_edit()  # one request, the server answers
```
"""


# ---- UI ---------------------------------------------------------------------


class SimpleBody(nustd.ui.Column):
    table = nustd.ui.TableRef.slot(
        columns=[
            {"key": "name", "label": "Planet"},
            {"key": "moons", "label": "Moons", "kind": "number", "align": "right"},
            {"key": "radius_km", "label": "Radius (km)", "kind": "number", "align": "right"},
            {"key": "rings", "label": "Rings", "kind": "bool"},
        ],
        label="Planets",
        row_key="name",
        clickable_rows=True,
    )
    status = nustd.ui.TextRef.slot(value="Click a header to sort, a row to pick it.")


class SimpleCard(nustd.ui.Card):
    body = SimpleBody.slot(gap=3)


class DataCard(nustd.ui.Card):
    table = nustd.ui.TableRef.slot(
        columns=[
            {"key": "task", "label": "Task"},
            {"key": "hours", "label": "Hours", "kind": "number", "align": "right"},
            {"key": "done", "label": "Done", "kind": "bool"},
            {"key": "owner", "label": "Owner", "kind": "select", "options": ["gor", "sonny"]},
        ],
        label="Tasks",
        selection="multi",
        editable=True,
        addable=True,
        deletable=True,
        draggable=True,
        columns_editable=True,
    )


class MarkdownBody(nustd.ui.Column):
    editor = nustd.ui.MarkdownRef.slot(
        editable=True, placeholder="Write, or type | a | b | then Enter"
    )
    preview_label = nustd.ui.TextRef.slot(value="Read-only, the same document:")
    preview = nustd.ui.MarkdownRef.slot()
    source_label = nustd.ui.TextRef.slot(value="The markdown it stores:")
    source = nustd.ui.CodeRef.slot(language="markdown")


class MarkdownCard(nustd.ui.Card):
    body = MarkdownBody.slot(gap=3)


class Home(nustd.ui.Page):
    heading = nustd.ui.HeadingRef.slot(label="Tables")
    simple = SimpleCard.slot(title="Simple: read-only, sorted by the server")
    data = DataCard.slot(title="Data: editable, stored, live across tabs")
    markdown = MarkdownCard.slot(title="Markdown: a table inside a document")


class App(nustd.ui.Index):
    title: nustd.ui.TitleRef
    home = Home.slot("/")


SIMPLE = App.home.simple.body.table
PICKED = App.home.simple.body.status
DATA = App.home.data.table
MD = App.home.markdown.body


# ---- State ------------------------------------------------------------------


class Store(nu.Shape):
    seeded = nustd.kv.BoolRef.slot()
    # Simple: the planets as one list, sorted on the way out, never stored sorted.
    planets = nustd.kv.ObjectRef.slot()
    # Data: the layout nustd.ui.table.sync keeps.
    rows = nustd.kv.DictRef.slot(nustd.ui.table.Row)
    order = nustd.kv.ListRef.slot(str)
    columns = nustd.kv.ListRef.slot(object)
    sort = nustd.kv.ObjectRef.slot()
    # Markdown: the document's source.
    notes = nustd.kv.StrRef.slot()


# Seed once per store; every connection runs it, only the first finds it empty.
init = nustd.kv.Transaction(
    nu.IfDo(
        Store.seeded.missing(),
        Store.planets.set(_PLANETS)
        >> nu.Sequential(*(Store.rows[k].cells.set(cells) for k, cells in _TASKS.items()))
        >> Store.order.set(list(_TASKS))
        >> Store.notes.set(_NOTES)
        >> Store.seeded.set(True),
    )
)


# ---- Simple -----------------------------------------------------------------


def planets_by(column: nu.Nu, direction: nu.Nu) -> nu.Nu:
    """The planets ordered by ``column``."""
    return nu.Collect(
        nu.SortBy(nu.Iter(Store.planets), lambda r: r[column], reverse=nu.Eq(direction, "desc"))
    )


simple = nustd.kv.Snapshot(SIMPLE.set_rows(Store.planets)) >> (
    nu.ReactForever(
        SIMPLE.on_sort(),
        lambda ev: nustd.kv.Snapshot(
            SIMPLE.set_rows(planets_by(ev["sort_column"], ev["sort_direction"]))
            >> SIMPLE.set_sort(ev["sort_column"], ev["sort_direction"])
        ),
    )
    | nu.ReactForever(
        SIMPLE.on_row_click(),
        lambda ev: PICKED.set("Picked " + nu.Str(ev["key"])),
    )
)


# ---- Data -------------------------------------------------------------------


data = nustd.ui.table.sync(DATA, Store.rows, Store.order, Store.columns, sort=Store.sort)


# ---- Markdown ---------------------------------------------------------------


def show(source: nu.Nu) -> nu.Nu:
    """The document drawn in all three places."""
    return MD.editor.set(source) | MD.preview.set(source) | MD.source.set(source)


markdown = nustd.kv.Snapshot(show(Store.notes)) >> nu.ReactForever(
    MD.editor.on_change(),
    lambda _: nu.let(
        nu.Str(MD.editor),
        lambda text: (
            nustd.kv.Transaction(Store.notes.set(text))
            >> (MD.preview.set(text) | MD.source.set(text))
        ),
    ),
)


# ---- Wire -------------------------------------------------------------------


ui = App.title.set("Tables") >> init >> (simple | data | markdown)

app = nu.With(
    nustd.kv.rocksdb_navigator(".dbtables"),
    body=nustd.ui.serve(App, ui, port=8096),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
