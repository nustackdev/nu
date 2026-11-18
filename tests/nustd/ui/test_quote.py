"""Quote: a header line over a body, as a Ref alone and as a Shape.

The header is the quote's own part, reached by ``.header`` (a Row unless the
Shape names it), never a body key. The string ``title`` is its shorthand.
Every other child is the body, which speaks a Column's layers.

Runs against a recording session, same harness as test_layers.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd import ui
from nustd.ui import Session
from nustd.ui.core.base import _wire_type_of
from nustd.ui.core.chains import boot_chains


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


def test_wire_type_and_slot_defaults():
    assert ui.QuoteRef._wire_type == "Quote"
    assert _wire_type_of(ui.Quote) == "Quote"
    assert ui.QuoteRef.slot().props == {"title": ""}
    assert ui.Quote.slot(title="Note", gap=1).props == {"title": "Note", "gap": 1}
    assert "_wire_type" not in vars(ui.Quote)
    assert "slot" not in vars(ui.Quote)


def test_set_title_is_a_partial_write():
    [frame] = _frames(ui.QuoteRef("q").set_title("Source"))
    assert (frame.op, frame.ref, frame.payload) == ("write", ("q",), {"title": "Source"})


def test_header_defaults_to_a_row():
    quote = ui.QuoteRef("q")
    assert type(quote.header) is ui.RowRef
    [frame] = _frames(ui.TextRef("label", parent_ref=quote.header).set("Working"))
    assert _chain(frame) == [("q", "Quote"), ("header", "Row"), ("label", "TextRef")]
    assert frame.chain[1][2]["gap"] == 2


def test_header_re_kinds_with_to():
    [frame] = _frames(ui.QuoteRef("q").header.to(ui.LineRef).init())
    assert _chain(frame)[1] == ("header", "Line")


def test_header_is_not_a_body_key():
    with pytest.raises(ValueError, match=r"reach it as \.header"):
        ui.QuoteRef("q")["header"]
    with pytest.raises(ValueError, match="own part"):
        ui.QuoteRef.slot(grow={"header": 1})


def test_a_shape_header_slot_wins_over_the_default():
    class Source(ui.Line):
        name = ui.TextRef.slot(value="RFC 9110")

    class Citation(ui.Quote):
        header = Source.slot()
        body = ui.TextRef.slot(value="quoted")

    quote = ui.QuoteRef("c", section_cls=Citation)
    assert type(quote.header) is ui.LineRef


def test_boot_chains_draw_the_header_and_the_body():
    class Trace(ui.Quote):
        header = ui.Row.slot(gap=1)
        body = ui.TextRef.slot(value="step one")

    class Home(ui.Column):
        trace = Trace.slot(gap=1)

    chains = [[lvl[:2] for lvl in c] for c in boot_chains((), Home) if c[0][0] == "trace"]
    assert [("trace", "Quote"), ("header", "Row")] in chains
    assert [("trace", "Quote"), ("body", "TextRef")] in chains


def test_body_children_sit_beside_the_header():
    col = ui.ColumnRef("col")
    note = ui.QuoteRef("note", parent_ref=col, props={"title": "Note"})
    [frame] = _frames(ui.TextRef("t", parent_ref=note).set("hi"))
    assert _chain(frame) == [("col", "Column"), ("note", "Quote"), ("t", "TextRef")]
    assert frame.chain[1][2] == {"title": "Note"}
