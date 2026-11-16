"""Gallery - drop images, videos and sound; they stream into a blob store and show in a grid.

A drop shows a tile per file with a progress bar and pulls each file to the
server. As each lands it streams from the upload intake into the blob store
(``put_stream`` over ``open``): no step holds the whole file, so a large
video goes through in pieces. Its id and mime go into a kv log and the file
leaves the selection.

The log is what the grid shows: one arm per item, kept in step with the log
(``ReconcileLatestEach``). An arm draws its tile, the image, video or player
with a download link, and a delete button it listens to. A click drops the
blob and the log entry; the log moving ends the arm, and the tile goes with
it. The browser reads each tile from the blob mount, a video in ranges as it
plays.

Run it and open http://localhost:8095:

    .venv/bin/python examples/gallery.py
"""

import nu
import nustd
from nustd import ui


# ---- UI ---------------------------------------------------------------------


class Page(ui.Container):
    heading = ui.HeadingRef.slot(label="Gallery")
    drop = ui.UploadFilesRef.slot(
        accept="image/*,video/*,audio/*", prompt="Drop images, videos or sound"
    )
    grid = ui.GridRef.slot(min_cell_width=280, gap=3)


class Pending(ui.Column):
    """A file on its way: its name and how much of it the server has."""

    name = ui.TextRef.slot(value="")
    bar = ui.ProgressRef.slot(caption="Uploading")


class App(nu.Shape):
    title = ui.TitleRef.slot(default="Gallery")
    home = Page.slot(max_width="dashboard", gap=4)


PAGE = App.home


# ---- Stores -----------------------------------------------------------------


Media = nustd.blob.StoreRef("media")
MOUNT = nustd.blob.http.BlobMount("/media")
SPEC = nustd.blob.files(Media, ".dbgallery/gallery/blobs")


class State(nu.Shape):
    media = nustd.kv.LogDictRef.slot(str)  # blob id -> mime, oldest first


# ---- Items ------------------------------------------------------------------


def media(cell: ui.ItemRef, bid: nu.Nu, mime: nu.Nu) -> nu.Nu:
    """The blob in ``cell``, drawn by the kind its mime names."""
    src, saved = MOUNT.url(bid), MOUNT.url(bid, download=True)
    kind = nu.Str(mime).split("/")[0]
    image = cell.to(ui.ImageRef.slot(fit="cover", aspect="4/3", radius="md", zoom=True))
    video = cell.to(ui.VideoRef.slot(aspect="16/9", radius="md"))
    sound = cell.to(ui.AudioRef)
    return nu.IfDo(
        nu.Eq(kind, "image"),
        image.init() >> image.set_src(src) >> image.set_download(saved),
        nu.IfDo(
            nu.Eq(kind, "video"),
            video.init() >> video.set_src(src) >> video.set_download(saved),
            sound.init() >> sound.set_src(src) >> sound.set_download(saved),
        ),
    )


def item(bid: nu.Nu) -> nu.Nu:
    """One item's arm: its tile up while it lives, its delete button heard."""
    card = PAGE.grid[bid].to(ui.ColumnRef.slot(gap=2))
    delete = card[1].to(ui.ButtonRef.slot(label="Delete", variant="ghost", size="sm"))
    draw = (
        PAGE.grid.insert(card, at=0)
        >> nu.let(nustd.kv.atomic(State.media[bid]), lambda mime: media(card[0], bid, mime))
        >> delete.init()
    )
    # The blob first: the log moving cancels this arm, so the entry goes last.
    gone = Media.delete(bid) >> nustd.kv.atomic(State.media.del_item(bid))
    live = draw >> nu.ReactEvery(delete.on_click(), lambda _: gone)
    leave = nu.TryCatch(PAGE.grid.remove(bid), catch=lambda _: nu.Noop())
    return nu.TryCatch(live, finally_=leave)


items = nu.ReconcileLatestEach(
    nustd.kv.atomic(nu.If(State.media.exists(), nu.Collect(nu.Iter(State.media)), [])),
    nustd.kv.atomic(State.media.on_children_change()),
    item,
)


# ---- Uploads ----------------------------------------------------------------


def pending(key: nu.Nu) -> Pending:
    """The progress tile of the upload ``key``."""
    return PAGE.grid[key].to(Pending.slot(gap=2))


def picked() -> nu.Nu:
    """A progress tile and a pull for every newly picked file."""

    def start(i: nu.Nu, entry: nu.Nu) -> nu.Nu:
        f: nu.Dict[str, str] = nu.Dict(entry)
        card = pending(f["key"])
        return nu.IfDo(
            nu.Eq(f["state"], "picked"),
            PAGE.grid.insert(card, at=0) >> card.name.set(f["name"]) >> PAGE.drop.file(i).pull(),
        )

    return nu.ForEachDo(nu.Enumerate(nu.Iter(PAGE.drop)), lambda e: start(e[0], e[1]))


def moved(event: nu.Nu) -> nu.Nu:
    """A pull moving: its bar to the share sent."""
    ev: nu.Dict[str, object] = nu.Dict(event)
    return pending(ev["key"]).bar.set_value(nu.Float(ev["sent"]) / nu.Float(ev["size"]))


def landed(event: nu.Nu) -> nu.Nu:
    """A pull ended: a landed file streamed into the store, logged and let go."""
    ev: nu.Dict[str, object] = nu.Dict(event)
    key, bar = ev["key"], pending(ev["key"]).bar

    def find(selection: nu.Nu) -> nu.Nu:
        sel: nu.List[dict] = nu.List(selection)
        keys: nu.List[str] = nu.List(nu.Collect(nu.Map(nu.Iter(sel), lambda f: f["key"])))
        # ``open`` pulls too, and its landing is heard here after the first one
        # stored the file and let it go: only a file still picked is stored.
        return nu.IfDo(keys.contains(key), nu.let(keys.index(key), lambda i: store(i, sel[i])))

    def store(i: nu.Nu, entry: nu.Nu) -> nu.Nu:
        f: nu.Dict[str, str] = nu.Dict(entry)
        file = PAGE.drop.file(i)
        piped = Media.put_stream(file.open(), mime=f["mime"], name=f["name"])
        return bar.set(1.0, caption="Storing", indeterminate=True) >> nu.let(
            piped,
            lambda bid: (
                nustd.kv.atomic(State.media.set_item(bid, f["mime"]))
                >> PAGE.grid.remove(key)
                >> file.discard()
                >> PAGE.drop.remove(i)
            ),
        )

    return nu.IfDo(
        nu.Eq(ev["state"], "landed"),
        nu.let(PAGE.drop, find),
        bar.set(0.0, caption="Failed: " + nu.Str(ev["error"])),
    )


uploads = (
    nu.ReactEvery(PAGE.drop.on_change(), lambda _: picked())
    | nu.ReactEvery(PAGE.drop.on_progress(), moved)
    | nu.ReactEvery(PAGE.drop.on_upload(), landed)
)


app = nu.With(
    nustd.kv.rocksdb_navigator(".dbgallery/gallery/kv"),
    SPEC,
    body=ui.serve(
        ui.boot(App.title, App.home) >> (items | uploads),
        blobs={MOUNT: SPEC},
        port=8095,
    ),
)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
