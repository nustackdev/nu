"""InputRef types, InlineEditRef and InputGroup. Wire only, through a fake
session, no browser."""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Session
from nustd.ui.core import Changed
from nustd.ui.refs import (
    ButtonRef,
    Field,
    InlineEditRef,
    InputGroup,
    InputGroupRef,
    InputRef,
    Row,
)


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


def _run(term, sess: _RecordingSession | None = None):
    sess = sess or _RecordingSession()
    result = asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return result, sess


def _frames(term):
    return _run(term)[1].frames


# --- InputRef types ----------------------------------------------------------


@pytest.mark.parametrize("kind", ["text", "search", "email", "url", "tel", "password", "number"])
def test_input_takes_each_type(kind):
    assert InputRef.slot(type=kind).props["type"] == kind


def test_input_refuses_an_unknown_type():
    with pytest.raises(ValueError, match="search"):
        InputRef.slot(type="color")  # type: ignore[arg-type]


def test_search_input_reads_text():
    handle = _mount(InputRef.slot(type="search"))
    result, sess = _run(handle, _RecordingSession("dune"))
    assert result[0] == "dune"
    assert sess.reads == [("page", "sec", "w")]


# --- InlineEditRef -----------------------------------------------------------


def test_inline_edit_slot_defaults():
    props = InlineEditRef.slot().props
    assert props["value"] == ""
    assert props["error"] == ""
    assert props["placeholder"] == ""
    assert props["max_length"] is None
    assert props["size"] == "md"


def test_inline_edit_seeds_value_and_error():
    props = InlineEditRef.slot(value="Notes", error="Taken", required=True, label="Name").props
    assert (props["value"], props["error"], props["required"], props["label"]) == (
        "Notes",
        "Taken",
        True,
        "Name",
    )


def test_inline_edit_set_writes_the_bare_value():
    handle = _mount(InlineEditRef.slot())
    [frame] = _frames(handle.set("Renamed"))
    assert frame.op == "write"
    assert frame.payload == "Renamed"
    assert frame.chain[-1][1] == "InlineEditRef"


def test_inline_edit_setters_merge_one_key():
    handle = _mount(InlineEditRef.slot())
    assert _frames(handle.set_error("Taken"))[0].payload == {"error": "Taken"}
    assert _frames(handle.set_placeholder("Untitled"))[0].payload == {"placeholder": "Untitled"}
    assert _frames(handle.set_label("Name"))[0].payload == {"label": "Name"}


def test_inline_edit_reads_round_trip():
    handle = _mount(InlineEditRef.slot(value="a"))
    result, sess = _run(handle, _RecordingSession("b"))
    assert result[0] == "b"
    assert sess.reads == [("page", "sec", "w")]


def test_inline_edit_hears_change_and_submit():
    handle = _mount(InlineEditRef.slot())
    assert isinstance(handle.on_change(), Changed)
    assert isinstance(handle.on_submit(), Changed)


# --- InputGroup --------------------------------------------------------------


class Say(InputGroup):
    text = InputRef.slot(placeholder="Say something")
    send = ButtonRef.slot(label="Send", icon="send")
    stop = ButtonRef.slot(label="Stop", variant="secondary")


def test_input_group_wire_type_and_layout():
    assert InputGroupRef.slot().props == {}
    assert InputGroupRef.slot(gap=3, max_width="form").props == {"gap": 3, "max_width": "form"}
    assert Say.slot(gap=1).props == InputGroupRef.slot(gap=1).props


def test_input_group_refuses_row_arrange_props():
    with pytest.raises(TypeError):
        InputGroupRef.slot(align="end")  # type: ignore[call-arg]


def test_input_group_children_reach_the_wire_under_it():
    page = type("GPage", (Column,), {"say": Say.slot()})
    app = type("GApp", (Shape,), {"page": page.slot()})
    [frame] = _frames(app.page.say.text.set("hi"))
    assert frame.ref == ("page", "say", "text")
    assert [(seg, typ) for seg, typ, _ in frame.chain] == [
        ("page", "Column"),
        ("say", "InputGroup"),
        ("text", "InputRef"),
    ]


def test_input_group_set_layout():
    page = type("GPage", (Column,), {"say": Say.slot()})
    app = type("GApp", (Shape,), {"page": page.slot()})
    [frame] = _frames(app.page.say.set_layout(gap=4))
    assert frame.payload == {"gap": 4}


def test_input_group_sits_in_a_field():
    class Titled(Field):
        control = Say.slot()

    page = type("FPage", (Column,), {"title": Titled.slot(label="Message")})
    app = type("FApp", (Shape,), {"page": page.slot()})
    [frame] = _frames(app.page.title.control.send.set_label("Go"))
    assert frame.ref == ("page", "title", "control", "send")
