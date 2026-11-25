"""MicCaptureRef and CameraCaptureRef: upload inputs whose file the tab recorded.

The slots follow the contract and refuse what it does not take, a program
cannot put a take in, the setters write one prop each, ``on_status`` hears
only status notifies, and a take reads its bytes with the upload reads,
the command shipped on the capture node's own chain.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Any

import pytest

import nu
import nustd.ui
from nu import Context, Shape
from nu.lang.null import is_null
from nustd.ui import CameraCaptureRef, Column, MicCaptureRef, Row, Session
from nustd.ui.uploads import UploadView


if TYPE_CHECKING:
    from pathlib import Path


SID = "tab1"
MIC = ("page", "sec", "mic")
CAM = ("page", "sec", "cam")


def _app():
    sec = type(
        "CapSec",
        (Row,),
        {
            "mic": MicCaptureRef.slot(label="Memo", max_duration=60),
            "cam": CameraCaptureRef.slot(mode="video", audio=False),
        },
    )
    page = type("CapPage", (Column,), {"sec": sec.slot()})
    return type("CapApp", (Shape,), {"page": page.slot()})


APP = _app()
M = APP.page.sec.mic
C = APP.page.sec.cam


# --- a tab that holds one take per node ----------------------------------------


class _Sub:
    def __init__(self, tab: _Tab, path: tuple[str, ...]) -> None:
        self.tab = tab
        self.path = path
        self.callbacks: list = []

    def bind(self, cb) -> None:
        self.callbacks.append(cb)

    def unbind(self, cb) -> None:
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self) -> None:
        self.callbacks = []
        if self in self.tab.subs:
            self.tab.subs.remove(self)


class _Tab(Session):
    """A tab whose capture nodes each hold ``takes[path]`` bytes, or nothing."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.frames: list = []
        self.subs: list[_Sub] = []
        self.takes: dict[tuple[str, ...], bytes] = {}
        self.value: Any = None

    async def send(self, frame) -> None:
        self.frames.append(frame)
        asyncio.get_running_loop().call_soon(self._handle, frame)

    async def aread(self, path, field=None):
        return self.value

    def subscribe(self, path, event=None):
        sub = _Sub(self, tuple(path))
        self.subs.append(sub)
        return sub

    def notify(self, path, payload) -> None:
        for sub in tuple(self.subs):
            if sub.path == tuple(path):
                for cb in tuple(sub.callbacks):
                    cb(payload)

    def _handle(self, frame) -> None:
        path, p = tuple(frame.ref), frame.payload
        if frame.op != "slice":
            return
        data = self.takes.get(path)
        if data is None:
            self.notify(path, _slice(p, None, "failed", 0, "no_file"))
            return
        token = uuid.uuid4().hex
        home = self.root / SID
        home.mkdir(parents=True, exist_ok=True)
        (home / token).write_bytes(data[p["start"] : p["end"]])
        self.notify(path, _slice(p, token, "picked", len(data), ""))


def _slice(p, token, state, size, error) -> dict:
    return {
        "event": "slice",
        "key": "take",
        "rid": p["rid"],
        "token": token,
        "cached": False,
        "state": state,
        "size": size,
        "error": error,
    }


@pytest.fixture
def tab(tmp_path: Path) -> _Tab:
    return _Tab(tmp_path / "area")


def _ctx(tab: _Tab) -> Context:
    return Context().bind(Session, tab).bind(UploadView, UploadView(tab.root, SID))


def _run(tab: _Tab, term) -> Any:
    out, _ = asyncio.run(nu.arun(term, _ctx(tab)))
    return out


# --- slots -------------------------------------------------------------------------


COMMON = {
    "label": "",
    "disabled": False,
    "readonly": False,
    "required": False,
    "autofocus": False,
    "size": "md",
}


def test_mic_slot_props_follow_the_contract():
    assert MicCaptureRef.slot().props == {"max_duration": None, "processing": True, **COMMON}
    props = MicCaptureRef.slot(max_duration=30, processing=False, label="Memo").props
    assert props["max_duration"] == 30
    assert props["processing"] is False
    assert props["label"] == "Memo"
    assert "value" not in props


def test_camera_slot_props_follow_the_contract():
    assert CameraCaptureRef.slot().props == {
        "mode": "photo",
        "facing": "user",
        "resolution": "hd",
        "format": "jpeg",
        "audio": True,
        "max_duration": None,
        "aspect": "",
        **COMMON,
    }
    props = CameraCaptureRef.slot(
        mode="video", facing="environment", resolution="fhd", format="webp", aspect="1/1"
    ).props
    assert (props["mode"], props["facing"], props["resolution"]) == ("video", "environment", "fhd")
    assert (props["format"], props["aspect"]) == ("webp", "1/1")


@pytest.mark.parametrize("bad", [0, -5, 1.5, True, "10"])
def test_slots_refuse_a_bad_duration(bad):
    with pytest.raises(ValueError, match="max_duration"):
        MicCaptureRef.slot(max_duration=bad)
    with pytest.raises(ValueError, match="max_duration"):
        CameraCaptureRef.slot(max_duration=bad)


@pytest.mark.parametrize(
    ("field", "bad"),
    [("mode", "burst"), ("facing", "left"), ("resolution", "4k"), ("format", "gif")],
)
def test_camera_slot_refuses_an_unknown_choice(field, bad):
    with pytest.raises(ValueError, match=field):
        CameraCaptureRef.slot(**{field: bad})


def test_slots_take_no_value_seed():
    with pytest.raises(TypeError):
        MicCaptureRef.slot(value={"name": "x"})
    with pytest.raises(TypeError):
        CameraCaptureRef.slot(value={"name": "x"})


def test_set_raises_when_the_tree_is_built():
    with pytest.raises(TypeError, match="take in a recorder"):
        M.set({"name": "a.webm"})
    with pytest.raises(TypeError, match="take in a recorder"):
        C.set({"name": "a.jpg"})


def test_exported_from_nustd_ui():
    assert nustd.ui.MicCaptureRef is MicCaptureRef
    assert nustd.ui.CameraCaptureRef is CameraCaptureRef


# --- value, setters, reset ---------------------------------------------------------


def test_value_is_the_take_or_null(tab):
    take = {
        "key": "k1",
        "name": "recording-2026-11-17-140322.webm",
        "mime": "audio/webm",
        "size": 3,
        "modified": 1,
        "state": "picked",
        "sent": 0,
        "error": "",
        "duration": 1.5,
        "width": 0,
        "height": 0,
    }
    tab.value = take
    assert _run(tab, M) == take
    tab.value = None
    assert is_null(_run(tab, M))


def test_setters_write_one_prop(tab):
    _run(tab, M.set_max_duration(90) >> C.set_mode("photo") >> C.set_facing("environment"))
    _run(tab, M.set_label("Say hi") >> C.set_disabled(True))
    assert [(f.op, f.payload) for f in tab.frames] == [
        ("write", {"max_duration": 90}),
        ("write", {"mode": "photo"}),
        ("write", {"facing": "environment"}),
        ("write", {"label": "Say hi"}),
        ("write", {"disabled": True}),
    ]


def test_reset_ships_on_the_node_with_its_type(tab):
    _run(tab, M.reset() >> C.reset())
    assert [(f.op, tuple(f.ref), f.chain[-1][1]) for f in tab.frames] == [
        ("reset", MIC, "MicCaptureRef"),
        ("reset", CAM, "CameraCaptureRef"),
    ]


# --- status ------------------------------------------------------------------------


async def _hear(ctx: Context, reaction, heard: list) -> None:
    sub, _ = await nu.arun(reaction, ctx)
    sub.bind(heard.append)


def test_on_status_hears_status_only(tab):
    statuses: list[dict] = []
    changes: list[dict] = []

    async def run():
        ctx = _ctx(tab)
        await _hear(ctx, M.on_status(), statuses)
        await _hear(ctx, M.on_change(), changes)
        tab.notify(MIC, {"event": "status", "status": "recording", "error": ""})
        tab.notify(MIC, {"event": "change"})
        tab.notify(MIC, {"event": "status", "status": "blocked", "error": "denied"})

    asyncio.run(run())
    assert [(s["status"], s["error"]) for s in statuses] == [
        ("recording", ""),
        ("blocked", "denied"),
    ]
    assert changes == [{"event": "change"}]


# --- reads -------------------------------------------------------------------------


def test_a_take_reads_like_an_upload(tab):
    data = bytes(range(256)) * 4
    tab.takes[MIC] = data
    tab.takes[CAM] = b"\xff\xd8photo"
    assert _run(tab, M.bytes()) == data
    assert _run(tab, M.slice(0, 4)) == data[:4]
    assert _run(tab, C.slice(0, 2)) == b"\xff\xd8"
    first = tab.frames[0]
    assert (first.op, tuple(first.ref), first.payload["key"]) == ("slice", MIC, None)
    assert first.chain[-1][1] == "MicCaptureRef"


def test_an_empty_capture_raises_no_file(tab):
    with pytest.raises(nustd.ui.NoFile):
        _run(tab, M.bytes())
