"""TreeRef and event-filtered subscriptions -- frames out, notifies in, no browser.

Frames go to a recording session. Notifies come from a fake subscription that
fires a list of payloads the moment a reaction binds to it, which is all
``ReactOnce`` needs to run its body once on the first one that gets through.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Session, TreeRef
from nustd.ui.refs import TextRef


if TYPE_CHECKING:
    from nustd.ui.core import Changed


class FilesPage(Column):
    tree = TreeRef.slot(label="Files", editable=True, draggable=True)
    out = TextRef.slot()


class FilesApp(Shape):
    files = FilesPage.slot()


class _Sub:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = payloads
        self.bound: list = []
        self.closed = False

    def bind(self, cb) -> None:
        self.bound.append(cb)
        for p in self.payloads:
            cb(p)

    def unbind(self, cb) -> None:
        self.bound = [b for b in self.bound if b is not cb]

    def close(self) -> None:
        self.closed = True


class _Session:
    """Records frames; every subscription fires ``payloads`` on bind."""

    def __init__(self, *payloads: object) -> None:
        self.frames: list = []
        self.subscribed: list[tuple[str, ...]] = []
        self.subs: list[_Sub] = []
        self.payloads = list(payloads)

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    def subscribe(self, path: tuple[str, ...], event: str | None = None) -> _Sub:
        self.subscribed.append(path)
        sub = _Sub(self.payloads)
        self.subs.append(sub)
        return sub


def _run(term: nu.Nu, sess: _Session) -> None:
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))


def _echo(change: Changed) -> nu.Nu:
    """React once, writing the event's ``event`` field to ``out``."""
    return nu.ReactOnce(change, lambda ev: FilesApp.files.out.set(nu.Str(ev["event"])))


# --- frames out ---------------------------------------------------------------


def test_slot_seeds_the_chrome():
    props = FilesPage.tree._props
    assert props == {"label": "Files", "nodes": [], "editable": True, "draggable": True}


@pytest.mark.parametrize(
    ("term", "payload"),
    [
        (
            FilesApp.files.tree.set([{"key": "a", "label": "A"}]),
            {"nodes": [{"key": "a", "label": "A"}]},
        ),
        (FilesApp.files.tree.set_selected("a"), {"selected": "a"}),
        (FilesApp.files.tree.set_expanded(["a"]), {"expanded": ["a"]}),
    ],
)
def test_writes_merge_on_the_tree_path(term, payload):
    sess = _Session()
    _run(term, sess)
    (frame,) = sess.frames
    assert (frame.op, frame.ref, frame.payload) == ("write", ("files", "tree"), payload)


# --- notifies in --------------------------------------------------------------


@pytest.mark.parametrize("name", ["select", "open", "toggle", "rename", "move"])
def test_each_on_takes_only_its_own_event(name):
    others = [{"event": e} for e in ("select", "open", "toggle", "rename", "move") if e != name]
    sess = _Session(*others, {"event": name, "key": "a"})
    _run(_echo(getattr(FilesApp.files.tree, f"on_{name}")()), sess)
    assert sess.subscribed == [("files", "tree")]
    assert [f.payload for f in sess.frames] == [{"value": name}]


def test_on_event_takes_every_event():
    sess = _Session({"event": "move", "key": "a"})
    _run(_echo(FilesApp.files.tree.on_event()), sess)
    assert sess.frames[0].payload == {"value": "move"}


# --- reads --------------------------------------------------------------------


class _Reads(_Session):
    """Answers a read per field from ``answers``, recording each ``(path, field)``."""

    def __init__(self, answers: dict) -> None:
        super().__init__()
        self.answers = answers
        self.reads: list = []

    async def aread(self, path: tuple[str, ...], field: str | None = None) -> object:
        self.reads.append((path, field))
        return self.answers.get(field)


def _read(term: nu.Nu, sess: _Reads) -> object:
    value, _ = asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return value


@pytest.mark.parametrize(("raw", "want"), [("a", "a"), ("", None), (None, None)])
def test_reading_the_tree_gives_the_selected_key(raw, want):
    sess = _Reads({None: raw})
    assert _read(FilesApp.files.tree, sess) == want
    assert sess.reads == [(("files", "tree"), None)]


@pytest.mark.parametrize(("raw", "want"), [(["a", 1], ["a", "1"]), ([], []), (None, [])])
def test_expanded_reads_the_open_keys(raw, want):
    sess = _Reads({"expanded": raw})
    assert _read(FilesApp.files.tree.expanded(), sess) == want
    assert sess.reads == [(("files", "tree"), "expanded")]


def test_expanded_moves_on_toggle():
    assert TreeRef._reader_events == {"expanded": "toggle"}
    assert FilesApp.files.tree.on_toggle()._children[1].value == "toggle"


def test_a_filtered_subscription_skips_what_is_not_an_event():
    sess = _Session("raw", None, ["x"], {"key": "no event"}, {"event": "open", "key": "a"})
    _run(_echo(FilesApp.files.tree.on_open()), sess)
    assert [f.payload for f in sess.frames] == [{"value": "open"}]


def test_a_reaction_reads_the_event_fields():
    sess = _Session({"event": "rename", "key": "a", "title": "B"})
    _run(
        nu.ReactOnce(
            FilesApp.files.tree.on_rename(),
            lambda ev: FilesApp.files.out.set(nu.Str(ev["key"]) + "=" + nu.Str(ev["title"])),
        ),
        sess,
    )
    assert sess.frames[0].payload == {"value": "a=B"}


def test_a_filtered_subscription_unbinds_and_closes_through():
    sess = _Session({"event": "open", "key": "a"})
    _run(_echo(FilesApp.files.tree.on_open()), sess)
    (sub,) = sess.subs
    assert sub.bound == []
    assert sub.closed


def test_event_rides_as_a_child_not_a_field():
    change = FilesApp.files.tree.on_rename()
    assert len(nu.tree.children(change)) == 2
    assert "event" not in nu.tree.fields(change)
    assert len(nu.tree.children(FilesApp.files.tree.on_event())) == 1
