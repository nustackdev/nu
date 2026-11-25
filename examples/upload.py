"""Upload - search a csv the person picks, and list a few picked files.

Picking a file moves no bytes. The csv block reads the first 4 KiB the moment
a file is picked (`slice`), shows its header row and makes the columns of
the table from it, then pulls the whole file to the server in the background.
Typing a query and pressing Enter (or leaving the field) reads the file
(`bytes`, from the server's copy once it landed) and shows the rows that
contain the query. The files block takes several files and lists their names
and sizes straight from the value: it never reads a byte.

The bytes go over http from the browser to the server's temp area, never over
the ws; the temp files go when the tab closes or the server stops.

Run it and open http://localhost:8094:

    .venv/bin/python examples/upload.py
"""

import nu
import nustd


# ---- UI ---------------------------------------------------------------------


class CsvColumn(nustd.ui.Column):
    file = nustd.ui.UploadFileRef.slot(
        accept=".csv", label="CSV file", prompt="Drop a csv here, or click to pick one"
    )
    header = nustd.ui.TextRef.slot(value="No file yet")
    status = nustd.ui.TextRef.slot(value="")
    query = nustd.ui.InputRef.slot(label="Search", placeholder="Text in a row, then Enter")
    rows = nustd.ui.DataTableRef.slot(label="Matches", density="compact")


class CsvCard(nustd.ui.Card):
    body = CsvColumn.slot(gap=3)


class FilesColumn(nustd.ui.Column):
    files = nustd.ui.UploadFilesRef.slot(label="Files", max_files=10)
    listing = nustd.ui.DataTableRef.slot(
        label="Picked",
        density="compact",
        columns=["name", {"key": "size", "label": "bytes", "kind": "number"}],
    )


class FilesCard(nustd.ui.Card):
    body = FilesColumn.slot(gap=3)


class Upload(nustd.ui.Container):
    heading = nustd.ui.HeadingRef.slot(label="Upload")
    csv = CsvCard.slot(title="Search a csv")
    many = FilesCard.slot(title="Several files")


class App(nu.Shape):
    title = nustd.ui.TitleRef.slot(default="Upload")
    home = Upload.slot(max_width="main", gap=4)


CSV = App.home.csv.body
FILES = App.home.many.body


# ---- csv --------------------------------------------------------------------


def _columns(head: nu.Nu) -> nu.Nu:
    """The header row of a csv's first bytes, split at the commas."""
    first = nu.Bytes(nu.Bytes(head).partition(b"\n")[0]).decode()
    return nu.Str(first).strip().split(",")


def show_header(head: nu.Nu) -> nu.Nu:
    """Name the columns and make them the table's, before any search."""
    cols = _columns(head)
    return (
        CSV.header.set("Columns: " + nu.Str(", ").join(cols))
        >> CSV.rows.set(nu.Dict.of(columns=cols, rows=[]))
        >> CSV.status.set("Pulling the file to the server...")
    )


def picked() -> nu.Nu:
    """A new file: its header at once, then the whole of it in the background."""
    return nu.IfDo(
        nu.IsNull(CSV.file),
        CSV.header.set("No file yet") >> CSV.status.set("") >> CSV.rows.clear(),
        nu.let(CSV.file.slice(0, 4096), show_header) >> CSV.file.pull(),
    )


def landed(ev: nu.Nu) -> nu.Nu:
    """A pull ended: say how it went."""
    return nu.IfDo(
        nu.Eq(ev["state"], "landed"),
        CSV.status.set("On the server, " + nu.str(ev["size"]) + " bytes. Search away."),
        CSV.status.set("The pull did not finish: " + nu.Str(ev["error"])),
    )


def search(raw: nu.Nu) -> nu.Nu:
    """The rows (below the header) that contain the query, cells split at commas."""
    query = nu.Str(CSV.query).lower()
    lines = nu.Bytes(raw).decode().splitlines().slice(1, None)
    hits = nu.Filter(nu.Iter(lines), lambda line: nu.Str(line).lower().contains(query))
    rows = nu.Collect(nu.Map(hits, lambda line: nu.Str(line).split(",")))
    return nu.let(
        rows,
        lambda found: (
            CSV.rows.set_rows(nu.List(found).slice(0, 200))
            >> CSV.status.set(nu.str(nu.List(found).len()) + " rows match")
        ),
    )


csv = (
    nu.ReactEvery(CSV.file.on_change(), lambda _: picked())
    | nu.ReactEvery(CSV.file.on_upload(), landed)
    | nu.ReactEvery(
        CSV.query.on_change(),
        lambda _: nu.IfDo(nu.IsNull(CSV.file), nu.Noop(), nu.let(CSV.file.bytes(), search)),
    )
)


# ---- files ------------------------------------------------------------------


def listing() -> nu.Nu:
    """One row per picked file, from the value alone: no bytes read."""
    rows = nu.Map(nu.Iter(FILES.files), lambda f: nu.Dict.of(name=f["name"], size=f["size"]))
    return FILES.listing.set_rows(nu.Collect(rows))


files = nu.ReactEvery(FILES.files.on_change(), lambda _: listing())


app = nustd.ui.serve(nustd.ui.boot(App.title, App.home) >> (csv | files), port=8094)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
