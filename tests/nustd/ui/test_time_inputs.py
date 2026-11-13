"""Date and time inputs: TimePickerRef, DateTimePickerRef, DateRangePickerRef.
Slot defaults, the `set` payload, setters, the seed in the write chain and
the read round trip. Wire only, through a fake session, no browser."""

from __future__ import annotations

import asyncio
import datetime as dt

import nu
from nu import Context, Shape
from nustd.ui import Column, Session
from nustd.ui.refs import DateRangePickerRef, DateTimePickerRef, Row, TimePickerRef


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
    sec = type("WSec", (Row,), {"w": widget_slot})
    page = type("WPage", (Column,), {"sec": sec.slot()})
    app = type("WApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _frames(term, sess: _RecordingSession | None = None):
    sess = sess or _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _read(handle, value):
    sess = _RecordingSession(value)
    out, _ = asyncio.run(nu.arun(handle, Context().bind(Session, sess)))
    assert sess.reads == [("page", "sec", "w")]
    return out


COMMON = {
    "label": "",
    "disabled": False,
    "readonly": False,
    "required": False,
    "autofocus": False,
    "size": "md",
}


# --- TimePickerRef -------------------------------------------------------------


def test_time_slot_defaults():
    assert TimePickerRef.slot().props == {
        "value": "",
        "min": "",
        "max": "",
        "step": None,
        "clearable": True,
        **COMMON,
    }


def test_time_slot_takes_time_objects_and_seconds_with_a_small_step():
    props = TimePickerRef.slot(value=dt.time(9, 5), min=dt.time(8, 0)).props
    assert props["value"] == "09:05"
    assert props["min"] == "08:00"
    assert TimePickerRef.slot(value=dt.time(9, 5), step=1).props["value"] == "09:05:00"
    assert TimePickerRef.slot(value=dt.time(9, 5, 30)).props["value"] == "09:05:30"


def test_time_set_writes_the_bare_value_and_seeds_the_chain():
    handle = _mount(TimePickerRef.slot(value="07:00", label="Alarm"))
    [frame] = _frames(handle.set("12:15"))
    assert frame.op == "write"
    assert frame.payload == "12:15"
    wire_type, props = frame.chain[-1][1:]
    assert wire_type == "TimePickerRef"
    assert props["value"] == "07:00"
    assert props["label"] == "Alarm"


def test_time_reads_the_live_value():
    assert _read(_mount(TimePickerRef.slot()), "10:30") == "10:30"


def test_time_has_no_placeholder():
    assert not hasattr(TimePickerRef, "set_placeholder")


# --- DateTimePickerRef ---------------------------------------------------------


def test_date_time_slot_defaults_and_objects():
    assert DateTimePickerRef.slot().props == {
        "placeholder": "",
        "value": "",
        "min": "",
        "max": "",
        "clearable": True,
        **COMMON,
    }
    props = DateTimePickerRef.slot(
        value=dt.datetime(2016, 11, 11, 19, 30), min=dt.date(2016, 11, 1)
    ).props
    assert props["value"] == "2016-11-11T19:30"
    assert props["min"] == "2016-11-01T00:00"


def test_date_time_set_and_setters():
    handle = _mount(DateTimePickerRef.slot())
    assert _frames(handle.set("2016-11-11T19:30"))[0].payload == "2016-11-11T19:30"
    assert _frames(handle.set_placeholder("When"))[0].payload == {"placeholder": "When"}
    assert _frames(handle.set_label("Starts"))[0].payload == {"label": "Starts"}


def test_date_time_reads_the_live_value():
    assert _read(_mount(DateTimePickerRef.slot()), "2020-01-02T03:04") == "2020-01-02T03:04"


# --- DateRangePickerRef --------------------------------------------------------


def test_range_slot_defaults_to_the_empty_range():
    assert DateRangePickerRef.slot().props == {
        "placeholder": "",
        "value": {"start": "", "end": ""},
        "min": "",
        "max": "",
        "clearable": True,
        **COMMON,
    }


def test_range_slot_takes_dates_and_a_half_range():
    props = DateRangePickerRef.slot(
        value={"start": dt.date(2016, 11, 11), "end": "2016-11-13"}, max=dt.date(2016, 12, 31)
    ).props
    assert props["value"] == {"start": "2016-11-11", "end": "2016-11-13"}
    assert props["max"] == "2016-12-31"
    assert DateRangePickerRef.slot(value={"start": "2016-11-11"}).props["value"] == {
        "start": "2016-11-11",
        "end": "",
    }


def test_range_set_wraps_the_value():
    handle = _mount(DateRangePickerRef.slot())
    rng = {"start": "2016-11-11", "end": "2016-11-13"}
    assert _frames(handle.set(rng))[0].payload == {"value": rng}
    assert _frames(handle.set(start="2016-11-11", end="2016-11-13"))[0].payload == {"value": rng}
    assert _frames(handle.set(start="2016-11-11"))[0].payload == {
        "value": {"start": "2016-11-11", "end": ""}
    }


def test_range_reads_the_live_value():
    rng = {"start": "2016-11-11", "end": "2016-11-13"}
    assert _read(_mount(DateRangePickerRef.slot()), rng) == rng
