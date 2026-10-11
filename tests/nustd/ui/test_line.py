"""Line: the inline flow container, as a Shape and as Refs alone.

A Line holds open-ended children that run inline and wrap like a paragraph.
Its props are its own (align, wrap); a child carries none. Runs against a
recording session, same harness as test_layers.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core.base import _wire_type_of


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _chain(frame):
    return [(seg, typ) for seg, typ, _ in frame.chain]


def test_line_is_a_container_with_its_own_wire_type():
    from nustd.ui import Line, LineRef
    from nustd.ui.refs import ContainerRef

    assert issubclass(LineRef, ContainerRef)
    assert LineRef._wire_type == "Line"
    assert Line._ref_cls is LineRef
    assert "_wire_type" not in vars(Line)
    assert _wire_type_of(Line) == "Line"


def test_slot_defaults():
    from nustd.ui import LineRef

    assert LineRef.slot().props == {"align": "start", "wrap": True}
    assert LineRef.slot(align="center", wrap=False).props == {"align": "center", "wrap": False}


def test_slot_takes_no_other_props():
    from nustd.ui import LineRef

    with pytest.raises(TypeError):
        LineRef.slot(gap=2)


def test_shape_slot_forwards_to_the_ref():
    from nustd.ui import Line, LineRef

    class Status(Line):
        pass

    assert Line.slot().props == LineRef.slot().props
    assert Status.slot(align="end").props == LineRef.slot(align="end").props
    assert Status.slot(wrap=False).props["wrap"] is False


def test_boot_chains_of_a_page_with_a_line():
    from nustd.ui import BadgeRef, Line, LinkRef, ShortcutRef, TextRef
    from nustd.ui.nudle import Page

    class Status(Line):
        lead = TextRef.slot(value="Built with")
        link = LinkRef.slot(href="https://nustack.dev", label="Nu")
        tag = BadgeRef.slot(label="0.6", variant="info")
        combo = ShortcutRef.slot(keys=["mod", "K"])

    class Home(Page):
        status = Status.slot(align="center")

    chains = Home._boot_chains()
    status = [c for c in chains if c[0][0] == "status"]
    assert [[lvl[:2] for lvl in c] for c in status] == [
        [("status", "Line")],
        [("status", "Line"), ("lead", "TextRef")],
        [("status", "Line"), ("link", "LinkRef")],
        [("status", "Line"), ("tag", "BadgeRef")],
        [("status", "Line"), ("combo", "ShortcutRef")],
    ]
    assert status[0][0][2] == {"align": "center", "wrap": True}
    assert status[4][1][2]["keys"] == ["mod", "K"]


def test_refs_alone_text_under_line_under_card():
    from nustd.ui.refs import CardRef, LineRef, TextRef

    card = CardRef("card", props={"title": "Build"})
    line = LineRef("status", parent_ref=card, props={"wrap": False})
    [frame] = _frames(TextRef("lead", parent_ref=line).set("Built with"))
    assert _chain(frame) == [("card", "Card"), ("status", "Line"), ("lead", "TextRef")]
    assert frame.chain[1][2] == {"align": "start", "wrap": False}
    assert frame.ref == ("card", "status", "lead")


def test_refs_alone_computed_runs_keep_their_order():
    from nustd.ui.refs import BadgeRef, LineRef

    line = LineRef("tags")
    writes = [BadgeRef(nu.Str("b") + nu.str(i), parent_ref=line).set(f"t{i}") for i in range(3)]
    frames = _frames(writes[0] >> writes[1] >> writes[2])
    assert [f.ref for f in frames] == [("tags", f"b{i}") for i in range(3)]


def test_a_leaf_under_a_line_still_refuses_children():
    from nustd.ui.refs import LineRef, TextRef

    run = TextRef("lead", parent_ref=LineRef("status"))
    with pytest.raises(TypeError, match="TextRef is a leaf"):
        TextRef("x", parent_ref=run)
