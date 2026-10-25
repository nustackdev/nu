"""Flow containers and the frames that build them, with no browser.

Row's slot defaults (sizing comes from the child's kind, so the one knob is
the row's ``min_width``), and the chrome commands of Card and Tabs: they ship
the Ref's chain, so a container nobody booted (built from Refs alone, a
nested Section, a nuspace cell) is created by the frame that sets its chrome.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.refs import (
    CardRef,
    ColumnRef,
    PieChart,
    Row,
    RowRef,
    TabsRef,
    TextRef,
)


class _Recording:
    """Fake Session: keeps every frame it is handed."""

    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _run(term: nu.Nu) -> list:
    sess = _Recording()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


# --- Row slot ----------------------------------------------------------------


ROW_DEFAULTS = {
    "gap": 4,
    "align": "center",
    "justify": "start",
    "wrap": False,
    "padding": 0,
    "min_width": 240,
}


def test_row_slot_defaults_include_min_width():
    assert RowRef.slot().props == ROW_DEFAULTS


def test_row_slot_takes_min_width():
    assert RowRef.slot(wrap=True, min_width=320).props == {
        **ROW_DEFAULTS,
        "wrap": True,
        "min_width": 320,
    }


def test_row_shape_forwards_its_props_to_the_ref():
    class Tiles(Row):
        a = TextRef.slot()

    slot = Tiles.slot(wrap=True, min_width=200)
    assert slot.props == {**ROW_DEFAULTS, "wrap": True, "min_width": 200}
    assert slot.ref_cls is RowRef


def test_row_built_alone_carries_its_defaults_on_the_chain():
    row = RowRef("r", parent_ref=ColumnRef("c"), props={"wrap": True})
    text = TextRef("t", parent_ref=row)
    (frame,) = _run(text.set("hi"))
    assert frame.chain[1] == ("r", "Row", {**ROW_DEFAULTS, "wrap": True})


def test_row_refuses_an_unknown_prop():
    with pytest.raises(TypeError):
        RowRef.slot(width=100)


# --- chrome commands carry the chain ----------------------------------------


def _deep_card() -> CardRef:
    """A Card two levels down, built from Refs alone: no Shape, no boot."""
    outer = ColumnRef("outer")
    inner = ColumnRef("inner", parent_ref=outer)
    return CardRef("card", parent_ref=inner, props={"title": "declared"})


@pytest.mark.parametrize("op", ["set_title", "set_subtitle", "set_caption"])
def test_card_chrome_ships_the_chain(op):
    (frame,) = _run(getattr(_deep_card(), op)("hello"))
    assert frame.op == op
    assert frame.ref == ("outer", "inner", "card")
    assert frame.payload == "hello"
    assert [(seg, typ) for seg, typ, _ in frame.chain] == [
        ("outer", "Column"),
        ("inner", "Column"),
        ("card", "Card"),
    ]
    assert frame.chain[-1][2] == {
        "title": "declared",
        "subtitle": "",
        "caption": "",
        "variant": "default",
        "size": "md",
        "href": "",
        "target": "_self",
    }


def _deep_tabs() -> TabsRef:
    return TabsRef("tabs", parent_ref=ColumnRef("inner", parent_ref=ColumnRef("outer")))


def test_tabs_set_tabs_ships_the_chain_and_normalizes():
    (frame,) = _run(_deep_tabs().set_tabs([{"id": 1, "label": "One"}, {"label": "no id"}]))
    assert frame.op == "set_tabs"
    assert frame.payload == [{"id": "1", "label": "One"}]
    assert frame.chain[-1][:2] == ("tabs", "Tabs")
    assert [seg for seg, _, _ in frame.chain] == ["outer", "inner", "tabs"]


def test_tabs_set_active_ships_the_chain():
    (frame,) = _run(_deep_tabs().set_active("t2"))
    assert frame.op == "set_active"
    assert frame.payload == "t2"
    assert frame.chain[-1][:2] == ("tabs", "Tabs")


# --- chart payloads ----------------------------------------------------------


def test_pie_set_takes_label_value_maps():
    slices = [{"label": "Birds", "value": 3}, {"name": "Fish", "value": 2}]
    pie = PieChart("pie", parent_ref=ColumnRef("c"))
    (frame,) = _run(pie.set(slices))
    assert frame.op == "merge"
    assert frame.payload == {
        "series": [{"data": [{"name": "Birds", "value": 3}, {"name": "Fish", "value": 2}]}]
    }
