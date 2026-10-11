"""Input leaves: icon and tooltip on a button. Wire only, through a fake
session, no browser."""

from __future__ import annotations

import asyncio

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core import Changed
from nustd.ui.nudle import Index, Page
from nustd.ui.refs import ButtonRef, Row


class _RecordingSession:
    """Fake WsSession: records frames."""

    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


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
