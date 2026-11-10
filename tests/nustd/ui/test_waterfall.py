"""WaterfallRef: spans normalized on the slot and on set, partial writes, select notify."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import nu
from nu import Context, Shape
from nustd.ui import Column, Row, Session, WaterfallRef
from nustd.ui.core.base import _wire_type_of
from nustd.ui.refs import LeafRef


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _mount(**props):
    sec = type("WSec", (Row,), {"w": WaterfallRef.slot(**props)})
    page = type("WPage", (Column,), {"sec": sec.slot()})
    app = type("WApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _write(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    [frame] = sess.frames
    assert frame.op == "write"
    assert frame.ref == ("page", "sec", "w")
    return frame.payload


def test_is_a_leaf_under_its_own_name():
    assert issubclass(WaterfallRef, LeafRef)
    assert _wire_type_of(WaterfallRef) == "WaterfallRef"


def test_slot_defaults():
    props = WaterfallRef.slot().props
    assert props == {
        "spans": [],
        "start": None,
        "end": None,
        "now": None,
        "max_rows": 50,
        "label_width": 200,
        "selectable": False,
        "selected": "",
    }


def test_spans_are_normalized():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    props = WaterfallRef.slot(
        spans=[
            {"id": "a", "label": "root", "start": 0, "end": 100, "tone": "ok"},
            {"label": "child", "start": 10, "end": None, "parent": "a"},
            {"id": "t", "label": "dated", "start": t0, "end": t0},
            {"label": "no start"},
            "not a span",
        ],
    ).props
    ms = t0.timestamp() * 1000
    assert props["spans"] == [
        {"id": "a", "label": "root", "start": 0.0, "end": 100.0, "tone": "ok"},
        {"id": "1", "label": "child", "start": 10.0, "end": None, "parent": "a"},
        {"id": "t", "label": "dated", "start": ms, "end": ms},
    ]


def test_set_writes_normalized_spans():
    w = _mount()
    payload = _write(w.set([{"id": "x", "label": "x", "start": 1, "end": 2, "detail": ""}]))
    assert dict(payload) == {"spans": [{"id": "x", "label": "x", "start": 1.0, "end": 2.0}]}


def test_setters_send_only_their_keys():
    w = _mount()
    assert dict(_write(w.set_window(0, 500))) == {"start": 0.0, "end": 500.0}
    assert dict(_write(w.set_window(None, None))) == {"start": None, "end": None}
    assert dict(_write(w.set_now(250))) == {"now": 250.0}
    assert dict(_write(w.set_max_rows(10))) == {"max_rows": 10}
    assert dict(_write(w.set_selected("x"))) == {"selected": "x"}


def test_on_select_filters_on_the_select_event():
    w = _mount()
    term = w.on_select()
    assert term.__class__.__name__ == "Changed"
