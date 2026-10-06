"""Table sync - a spreadsheet that is its store, live across tabs.

Flow: edit, add, delete, move and sort rows, and add, rename, move, retype,
align or delete columns from a header's menu. There is no policy here: every
request is written to the store as asked (a value coerced to its column's
kind), and ``nustd.ui.table.sync`` answers it with only what changed. Open a
second tab and both stay equal: a write in either shows in the other without
a reload. The store is RocksDB under ``.dbtable_sync``, so the table survives
a restart.

Compare ``examples/table.py``, the same layout with an app's own rules in
front of the store.

Run it and open http://localhost:8093 (twice):

    .venv/bin/python examples/table_sync.py
"""

import nu
import nustd


class Sheet(nu.Shape):
    rows = nustd.kv.DictRef.slot(nustd.ui.table.Row)
    order = nustd.kv.ListRef.slot(str)
    columns = nustd.kv.ListRef.slot(object)
    sort = nustd.kv.ObjectRef.slot()


class Home(nustd.ui.Page):
    heading = nustd.ui.HeadingRef.slot(label="Sheet")
    table = nustd.ui.TableRef.slot(
        columns=[
            {"key": "task", "label": "Task"},
            {"key": "hours", "label": "Hours", "kind": "number", "align": "right"},
            {"key": "done", "label": "Done", "kind": "bool"},
        ],
        label="Sheet",
        selection="multi",
        editable=True,
        addable=True,
        deletable=True,
        draggable=True,
        columns_editable=True,
    )


class App(nustd.ui.Index):
    title: nustd.ui.TitleRef
    home = Home.slot("/")


ui = App.title.set("Sheet") >> nustd.ui.table.sync(
    App.home.table, Sheet.rows, Sheet.order, Sheet.columns, sort=Sheet.sort
)

app = nu.With(
    nustd.kv.rocksdb_navigator(".dbtable_sync"),
    body=nustd.ui.serve(App, ui, port=8093),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
