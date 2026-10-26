"""HtmlRef: a whole html document, drawn in a sandboxed frame.

A server-owned leaf: its slot seeds the props on the boot chain, a setter
sends a partial merge of just the keys it names, and nothing hangs off it.
Runs against a recording session, same harness as test_display.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, HtmlRef, Row, Session
from nustd.ui.refs import LeafRef, TextRef


DEFAULTS = {"html": "", "title": "", "height": None, "bordered": True}


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _mount(**props):
    """A fresh Shape -> Column with an HtmlRef at `.page.sec.w`; returns the handle."""
    sec = type("HSec", (Row,), {"w": HtmlRef.slot(**props)})
    page = type("HPage", (Column,), {"sec": sec.slot()})
    app = type("HApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _write(term):
    [frame] = _frames(term)
    assert frame.op == "write"
    assert frame.ref == ("page", "sec", "w")
    return frame


def test_a_leaf_on_the_wire_under_its_own_name():
    assert issubclass(HtmlRef, LeafRef)
    assert HtmlRef.__dict__["_wire_type"] == "HtmlRef"


def test_refuses_children():
    with pytest.raises(TypeError, match="HtmlRef is a leaf"):
        TextRef("t", parent_ref=HtmlRef("h"))


def test_slot_defaults_seed_the_boot_chain():
    assert HtmlRef.slot().props == DEFAULTS
    [frame] = _frames(_mount().set("<p>hi</p>"))
    assert frame.chain[-1][1:] == ("HtmlRef", DEFAULTS)


def test_slot_takes_no_other_props():
    with pytest.raises(TypeError):
        HtmlRef.slot(src="/page.html")


def test_set_leads_with_html_and_merges():
    doc = _mount()
    assert _write(doc.set("<p>hi</p>")).payload == {"html": "<p>hi</p>"}
    assert _write(doc.set("<p>hi</p>", title="Hi", height=200, bordered=False)).payload == {
        "html": "<p>hi</p>",
        "title": "Hi",
        "height": 200,
        "bordered": False,
    }


def test_each_setter_sends_its_own_key():
    doc = _mount()
    assert _write(doc.set_html("<b>x</b>")).payload == {"html": "<b>x</b>"}
    assert _write(doc.set_title("Mock")).payload == {"title": "Mock"}
    assert _write(doc.set_height(320)).payload == {"height": 320}
    assert _write(doc.set_height(None)).payload == {"height": None}
    assert _write(doc.set_bordered(False)).payload == {"bordered": False}


def test_html_may_be_a_term():
    doc = _mount()
    assert _write(doc.set_html(nu.Str("<p>") + "x" + "</p>")).payload == {"html": "<p>x</p>"}
