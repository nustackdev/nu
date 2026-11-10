"""TimelineRef: what its slot seeds and what each setter puts on the wire."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import nu
from nu import Context, Shape
from nustd.ui import Column, Session, TimelineRef
from nustd.ui.refs import Row


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _mount(**slot):
    sec = type("TSec", (Row,), {"w": TimelineRef.slot(**slot)})
    page = type("TPage", (Column,), {"sec": sec.slot()})
    app = type("TApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def test_slot_seeds_every_prop():
    [frame] = _frames(_mount().set([]))
    wire_type, props = frame.chain[-1][1:]
    assert wire_type == "TimelineRef"
    assert props == {
        "start": 0,
        "end": 0,
        "lanes": [],
        "total_lanes": 0,
        "max_lanes": 10,
        "max_items": 100,
        "noun": "item",
        "noun_plural": "",
        "axis": "relative",
        "legend": {},
        "more_label": "more",
        "more_text": "",
        "more_href": "",
        "more_target": "_self",
        "note": "",
    }


def test_slot_takes_a_legend_and_datetimes():
    now = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)
    [frame] = _frames(_mount(end=now, legend={"ok": "done"}).set([]))
    props = frame.chain[-1][2]
    assert props["end"] == 1_794_319_200_000
    assert props["legend"] == {"ok": "done"}


def test_set_normalizes_items_and_times():
    now = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)
    ms = 1_794_319_200_000
    lanes = [
        {
            "title": "Deploys",
            "icon": "rocket",
            "href": "/deploys",
            "items": [(ms - 60_000, None, "ok", "#41"), (ms - 120_000,)],
        },
        {"title": "tick", "items": [{"start": now, "end": now, "tone": "danger"}], "count": 912},
    ]
    [frame] = _frames(_mount().set(lanes, start=ms - 3_600_000, end=now, total_lanes=2150))
    assert frame.payload == {
        "lanes": [
            {
                "title": "Deploys",
                "icon": "rocket",
                "href": "/deploys",
                "items": [[ms - 60_000, None, "ok", "#41"], [ms - 120_000, None]],
            },
            {"title": "tick", "items": [{"start": ms, "end": ms, "tone": "danger"}], "count": 912},
        ],
        "start": ms - 3_600_000,
        "end": ms,
        "total_lanes": 2150,
    }


def test_set_more_sends_only_what_it_names():
    ref = _mount()
    assert _frames(ref.set_more("more lanes"))[0].payload == {"more_label": "more lanes"}
    assert _frames(ref.set_more("more lanes", text="All", href="/all"))[0].payload == {
        "more_label": "more lanes",
        "more_text": "All",
        "more_href": "/all",
    }


def test_set_window_legend_note():
    ref = _mount()
    assert _frames(ref.set_window(1, 2))[0].payload == {"start": 1, "end": 2}
    assert _frames(ref.set_legend({"danger": "failed"}))[0].payload == {
        "legend": {"danger": "failed"}
    }
    assert _frames(ref.set_note("The last 20"))[0].payload == {"note": "The last 20"}
