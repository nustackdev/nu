"""Files - a project tree on TreeRef.

Flow: the tree is a flat list of nodes in the store. Click a row to select
it, Enter or double click to open it, F2 or right-click to rename it, drag it
to move it. The tree never edits itself: each rename or move lands here, is
applied to the store, and the tree is shipped again. Every event also lands
in the activity list, through the one catch-all subscription.

Run it and open http://localhost:8080:

    .venv/bin/python examples/files.py
"""

import nu
import nustd


# ---- UI ---------------------------------------------------------------------


class TreeCard(nustd.ui.Card):
    tree = nustd.ui.TreeRef.slot(label="Files", editable=True, draggable=True)


class ActivityColumn(nustd.ui.Column):
    status = nustd.ui.TextRef.slot(value="Nothing selected")
    log = nustd.ui.ListRef.slot()


class ActivityCard(nustd.ui.Card):
    body = ActivityColumn.slot(gap=3)


class Panes(nustd.ui.Row):
    files = TreeCard.slot(title="Project")
    activity = ActivityCard.slot(title="Activity")


class Files(nustd.ui.Page):
    heading = nustd.ui.HeadingRef.slot(label="Files")
    intro = nustd.ui.TextRef.slot(
        value="Click to select, Enter to open, F2 to rename, drag to move.",
    )
    panes = Panes.slot(gap=4, align="start")


class App(nustd.ui.Index):
    title: nustd.ui.TitleRef
    files = Files.slot("/")


TREE = App.files.panes.files.tree
STATUS = App.files.panes.activity.body.status
LOG = App.files.panes.activity.body.log


# ---- State ------------------------------------------------------------------


class State(nu.Shape):
    # The tree as TreeRef ships it: {key, parent, label, icon}, siblings in
    # list order. Keys are paths, so they stay unique; labels are what shows.
    nodes = nustd.kv.ObjectRef.slot()


_SEED: list[dict] = [
    {"key": "src", "parent": "", "label": "src", "icon": "📁"},
    {"key": "src/app.py", "parent": "src", "label": "app.py", "icon": "🐍"},
    {"key": "src/lib", "parent": "src", "label": "lib", "icon": "📁"},
    {"key": "src/lib/tree.py", "parent": "src/lib", "label": "tree.py", "icon": "🐍"},
    {"key": "src/lib/store.py", "parent": "src/lib", "label": "store.py", "icon": "🐍"},
    {"key": "docs", "parent": "", "label": "docs", "icon": "📁"},
    {"key": "docs/intro.md", "parent": "docs", "label": "intro.md", "icon": "📝"},
    {"key": "README.md", "parent": "", "label": "README.md", "icon": "📝"},
    {"key": "pyproject.toml", "parent": "", "label": "pyproject.toml", "icon": "⚙️"},
]


# ---- Ops --------------------------------------------------------------------


def _node(n: nu.Nu, *, parent: nu.Nu | None = None, label: nu.Nu | None = None) -> nu.Nu:
    """A node rebuilt, with a new parent or label where given."""
    return nu.Dict.of(
        key=n["key"],
        parent=n["parent"] if parent is None else parent,
        label=n["label"] if label is None else label,
        icon=n["icon"],
    )


def renamed(key: nu.Nu, title: nu.Nu) -> nu.Nu:
    """Every node, the one at ``key`` with its new label."""
    return nu.Collect(
        nu.Map(
            nu.Iter(State.nodes),
            lambda n: nu.If(nu.Eq(n["key"], key), _node(n, label=title), n),
        )
    )


def moved(key: nu.Nu, parent: nu.Nu, index: nu.Nu) -> nu.Nu:
    """Every node, the one at ``key`` under ``parent`` at ``index`` among its siblings.

    ``index`` counts the new siblings without the moved node, so it lands
    before the sibling at that index, or after the last one.
    """

    def place(rest: nu.ObjectRef) -> nu.Nu:
        others = nu.List(rest)
        sibs = nu.List(nu.Collect(nu.Filter(nu.Iter(rest), lambda n: nu.Eq(n["parent"], parent))))
        keys = nu.List(nu.Collect(nu.Map(nu.Iter(rest), lambda n: n["key"])))
        i = nu.Int(index)
        at = nu.If(i < sibs.len(), keys.index(sibs[i]["key"]), others.len())
        node = nu.List(nu.Collect(nu.Filter(nu.Iter(State.nodes), lambda n: nu.Eq(n["key"], key))))
        return State.nodes.set(
            others.slice(0, at) + nu.List.of(_node(node[0], parent=parent)) + others.slice(at, None)
        )

    rest = nu.Collect(nu.Filter(nu.Iter(State.nodes), lambda n: nu.Ne(n["key"], key)))
    return nu.let(rest, place)


# ---- Wire -------------------------------------------------------------------


# Seed once per store; every connection runs it first, and only the first finds
# the store empty.
init = nustd.kv.Transaction(nu.IfDo(State.nodes.missing(), State.nodes.set(_SEED)))

ship = nustd.kv.Snapshot(TREE.set(State.nodes))


on_select = nu.ReactForever(
    TREE.on_select(),
    lambda ev: STATUS.set("Selected " + nu.Str(ev["key"])),
)

on_open = nu.ReactForever(
    TREE.on_open(),
    lambda ev: STATUS.set("Opened " + nu.Str(ev["key"])),
)

on_rename = nu.ReactForever(
    TREE.on_rename(),
    lambda ev: nustd.kv.Transaction(State.nodes.set(renamed(ev["key"], ev["title"]))) >> ship,
)

on_move = nu.ReactForever(
    TREE.on_move(),
    lambda ev: nustd.kv.Transaction(moved(ev["key"], ev["parent"], ev["index"])) >> ship,
)

# The catch-all: every event, whatever it is, into the activity list.
on_any = nu.ReactForever(
    TREE.on_change(),
    lambda ev: LOG.append(nu.Str(ev["event"]) + "  " + nu.Str(ev["key"])),
)


ui = App.title.set("Files") >> init >> ship >> (on_select | on_open | on_rename | on_move | on_any)


app = nu.With(
    nustd.kv.memory_navigator(),
    body=nustd.ui.serve(App, nustd.kv.auto_flow_atomic(ui), port=8081),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
