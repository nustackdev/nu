"""Input leaves: icon and tooltip on a button, the toolbar toggle. Wire
only, through a fake session, no browser."""

from __future__ import annotations

import asyncio

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core import Changed
from nustd.ui.nudle import Index, Page
from nustd.ui.refs import ButtonRef, Row, ToggleRef


class _RecordingSession:
    """Fake WsSession: records frames, answers reads with a fixed value."""

    def __init__(self, value: object = None) -> None:
        self.frames: list = []
        self.reads: list[tuple[str, ...]] = []
        self.value = value

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...]) -> object:
        self.reads.append(path)
        return self.value


def _mount(widget_slot):
    """A fresh Index -> Page with `widget_slot` at `.page.sec.w`; returns the handle."""
    sec = type("WSec", (Row,), {"w": widget_slot})
    page = type("WPage", (Page,), {"sec": sec.slot()})
    app = type("WApp", (Index,), {"page": page.slot("/")})
    return app.page.sec.w


def _frames(term, sess: _RecordingSession | None = None):
    sess = sess or _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _seeded(frame) -> tuple:
    """The (wire type, props) a write frame seeds its node with."""
    return frame.chain[-1][1:]


# --- ButtonRef: icon and tooltip ---------------------------------------------


def test_button_slot_defaults_carry_empty_icon_and_tooltip():
    assert ButtonRef.slot().props == {
        "label": "",
        "variant": "primary",
        "disabled": False,
        "icon": "",
        "tooltip": "",
    }


def test_button_icon_only_slot():
    props = ButtonRef.slot(icon="refresh-cw", tooltip="Reload", variant="ghost").props
    assert props["label"] == ""
    assert props["icon"] == "refresh-cw"
    assert props["tooltip"] == "Reload"


def test_button_seeds_its_icon_and_tooltip_on_the_wire():
    handle = _mount(ButtonRef.slot(icon="plus", tooltip="Add"))
    [frame] = _frames(handle.set_label("Add"))
    assert _seeded(frame) == (
        "ButtonRef",
        {"label": "", "variant": "primary", "disabled": False, "icon": "plus", "tooltip": "Add"},
    )


def test_button_set_icon_and_tooltip_merge_one_key():
    handle = _mount(ButtonRef.slot())
    assert _frames(handle.set_icon("trash-2"))[0].payload == {"icon": "trash-2"}
    assert _frames(handle.set_tooltip("Delete"))[0].payload == {"tooltip": "Delete"}


def test_button_set_takes_icon_and_tooltip():
    handle = _mount(ButtonRef.slot())
    [frame] = _frames(handle.set("", icon="x", tooltip="Close"))
    assert frame.payload == {"label": "", "icon": "x", "tooltip": "Close"}


def test_button_existing_payloads_unchanged():
    handle = _mount(ButtonRef.slot())
    assert _frames(handle.set("Go"))[0].payload == {"label": "Go"}
    assert _frames(handle.set("Go", variant="danger", disabled=True))[0].payload == {
        "label": "Go",
        "variant": "danger",
        "disabled": True,
    }
    assert _frames(handle.set_label("Stop"))[0].payload == {"label": "Stop"}
    assert _frames(handle.set_variant("ghost"))[0].payload == {"variant": "ghost"}
    assert _frames(handle.set_disabled(False))[0].payload == {"disabled": False}
    assert isinstance(handle.on_click(), Changed)


# --- ToggleRef -----------------------------------------------------------------


def test_toggle_wire_type_and_slot_defaults():
    assert ToggleRef._wire_type == "ToggleRef"
    assert ToggleRef.slot().props == {"label": "", "icon": "", "pressed": False}
    assert ToggleRef.slot(icon="bold", pressed=1).props["pressed"] is True


def test_toggle_set_writes_the_bare_pressed_state():
    handle = _mount(ToggleRef.slot(icon="wrap-text"))
    [frame] = _frames(handle.set(True))
    assert frame.ref == ("page", "sec", "w")
    assert frame.op == "write"
    assert frame.payload is True
    assert _seeded(frame) == ("ToggleRef", {"label": "", "icon": "wrap-text", "pressed": False})


def test_toggle_chrome_setters_merge_one_key():
    handle = _mount(ToggleRef.slot())
    assert _frames(handle.set_label("Wrap"))[0].payload == {"label": "Wrap"}
    assert _frames(handle.set_icon("pin"))[0].payload == {"icon": "pin"}


def test_toggle_reads_the_live_pressed_state():
    handle = _mount(ToggleRef.slot(label="Pin"))
    sess = _RecordingSession(value=True)
    result = asyncio.run(nu.arun(handle, Context().bind(Session, sess)))
    assert sess.reads == [("page", "sec", "w")]
    assert result[0] is True


def test_toggle_on_change_returns_a_subscription():
    assert isinstance(_mount(ToggleRef.slot()).on_change(), Changed)
