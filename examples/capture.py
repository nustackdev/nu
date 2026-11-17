"""Capture - a voice memo, a photo and a short video, recorded in the browser.

Each take is a file the browser made, held in the tab like a picked upload:
the value names it (name, mime, size, duration, width, height) and no byte
moves until the program asks. Here every kept take is pulled to the server
at once, and the card says where the device and the take are: the status
line hears `on_status` (asking, live, recording, blocked ...), the take line
reads the value, and the last line follows the pull.

The microphone and the camera open on the first click and close as soon as
the take is kept. Browsers give devices only to https or localhost.

Run it and open http://localhost:8100:

    .venv/bin/python examples/capture.py
"""

import nu
import nustd


# ---- UI ---------------------------------------------------------------------


class MemoColumn(nustd.ui.Column):
    take = nustd.ui.MicCaptureRef.slot(label="Voice memo", max_duration=120)
    status = nustd.ui.TextRef.slot(value="Microphone: idle")
    about = nustd.ui.TextRef.slot(value="No recording yet")
    stored = nustd.ui.TextRef.slot(value="")


class PhotoColumn(nustd.ui.Column):
    take = nustd.ui.CameraCaptureRef.slot(label="Photo", format="webp", aspect="4/3")
    status = nustd.ui.TextRef.slot(value="Camera: idle")
    about = nustd.ui.TextRef.slot(value="No photo yet")
    stored = nustd.ui.TextRef.slot(value="")


class VideoColumn(nustd.ui.Column):
    take = nustd.ui.CameraCaptureRef.slot(
        label="Video", mode="video", max_duration=30, resolution="sd"
    )
    status = nustd.ui.TextRef.slot(value="Camera: idle")
    about = nustd.ui.TextRef.slot(value="No video yet")
    stored = nustd.ui.TextRef.slot(value="")


class MemoCard(nustd.ui.Card):
    body = MemoColumn.slot(gap=3)


class PhotoCard(nustd.ui.Card):
    body = PhotoColumn.slot(gap=3)


class VideoCard(nustd.ui.Card):
    body = VideoColumn.slot(gap=3)


class Capture(nustd.ui.Container):
    heading = nustd.ui.HeadingRef.slot(label="Capture")
    memo = MemoCard.slot(title="Voice memo, up to 2 minutes")
    photo = PhotoCard.slot(title="Photo")
    video = VideoCard.slot(title="Video, up to 30 seconds")


class App(nu.Shape):
    title = nustd.ui.TitleRef.slot(default="Capture")
    home = Capture.slot(max_width="main", gap=4)


MEMO = App.home.memo.body
PHOTO = App.home.photo.body
VIDEO = App.home.video.body


# ---- one card ---------------------------------------------------------------


def _status(device: str, ev: nu.Nu) -> nu.Nu:
    """`Microphone: recording`, or `Camera: blocked (denied)`."""
    head = device + ": " + nu.Str(ev["status"])
    return nu.If(nu.Eq(ev["error"], ""), head, head + " (" + nu.Str(ev["error"]) + ")")


def _about(take: nu.Nu, empty: str) -> nu.Nu:
    """The take as the value names it: name, size, and duration or size in pixels."""
    line = nu.Str(take["name"]) + ", " + nu.str(take["size"]) + " bytes"
    shape = nu.If(
        nu.Eq(take["width"], 0),
        ", " + nu.str(nu.Round(take["duration"], 1)) + " s",
        ", " + nu.str(take["width"]) + "x" + nu.str(take["height"]),
    )
    return nu.If(nu.IsNull(take), empty, line + shape)


def card(col, device: str, empty: str) -> nu.Nu:
    """Status, the take, and its pull to the server, for one capture column."""

    def kept(take: nu.Nu) -> nu.Nu:
        return col.about.set(_about(take, empty)) >> nu.IfDo(
            nu.IsNull(take),
            col.stored.set(""),
            col.stored.set("Sending to the server...") >> col.take.pull(),
        )

    def landed(ev: nu.Nu) -> nu.Nu:
        return nu.IfDo(
            nu.Eq(ev["state"], "landed"),
            col.stored.set("On the server, " + nu.str(ev["size"]) + " bytes."),
            col.stored.set("The pull did not finish: " + nu.Str(ev["error"])),
        )

    return (
        nu.ReactEvery(col.take.on_status(), lambda ev: col.status.set(_status(device, ev)))
        | nu.ReactEvery(col.take.on_change(), lambda _: nu.let(col.take, kept))
        | nu.ReactEvery(col.take.on_upload(), landed)
    )


cards = (
    card(MEMO, "Microphone", "No recording yet")
    | card(PHOTO, "Camera", "No photo yet")
    | card(VIDEO, "Camera", "No video yet")
)


app = nustd.ui.serve(nustd.ui.boot(App.title, App.home) >> cards, port=8100)


if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(app))
