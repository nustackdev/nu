"""Container: the page frame. Slot defaults, the setters' frames, the Shape.

Wire only, through a recording session. How it draws (the cap, the gutter)
is the kit's test.
"""

from __future__ import annotations

import asyncio
from typing import get_args

import nu
from nu import Context
from nustd.ui import Container, ContainerRef, HeadingRef, Session, TitleRef
from nustd.ui.core.base import _wire_type_of
from nustd.ui.refs import CollectionRef, ColumnRef
from nustd.ui.refs.vocab import PageWidth


class _Recording:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _run(term: nu.Nu) -> list:
    sess = _Recording()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


DEFAULTS = {"size": "main", "gap": 6, "padding": "gutter"}


def test_page_widths_are_the_tokens():
    assert get_args(PageWidth) == ("form", "prose", "panel", "main", "dashboard", "full")


def test_is_a_collection_drawn_as_container():
    assert issubclass(ContainerRef, CollectionRef)
    assert ContainerRef._wire_type == "Container"
    assert Container._ref_cls is ContainerRef
    assert _wire_type_of(Container) == "Container"


def test_slot_defaults_and_shape_forwarding():
    assert ContainerRef.slot().props == DEFAULTS
    assert Container.slot(size="form", gap="3", padding="none").props == {
        "size": "form",
        "gap": 3,
        "padding": "none",
    }


def test_column_shares_the_width_names():
    assert ColumnRef.slot(max_width="dashboard").props["max_width"] == "dashboard"


def test_setters_ship_partial_writes_with_the_chain():
    page = ContainerRef("page", props={})
    frames = _run(page.set_size("prose") >> page.set_gap(4) >> page.set_padding("none"))
    assert [f.payload for f in frames] == [{"size": "prose"}, {"gap": 4}, {"padding": "none"}]
    assert frames[0].chain[0][:2] == ("page", "Container")
    assert frames[0].chain[0][2] == DEFAULTS


def test_a_shape_boots_its_slots_under_the_frame():
    class Home(Container):
        heading = HeadingRef.slot(label="Home")

    class App(nu.Shape):
        title = TitleRef.slot()
        home = Home.slot(size="dashboard")

    frames = _run(App.home.init())
    assert [(f.op, f.ref) for f in frames] == [("init", ("home",)), ("init", ("home", "heading"))]
    assert frames[0].chain[0][:2] == ("home", "Container")
    assert frames[0].chain[0][2]["size"] == "dashboard"
