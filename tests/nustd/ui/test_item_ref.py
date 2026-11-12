"""ui item refs: every leaf and container is core's item ref, and ``.to`` re-kinds one.

Wire only, through a fake session, no browser. The kind-mismatch refusal
itself happens in the browser store (ui-core ``tree.ts``); here is the Python
end of it, an inbound ``error`` frame surfacing in the log.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

import nu
import nustd.ui as ui
from nu import Context, Shape
from nu.domains import shape
from nu.domains.shape import Slot
from nustd.ui import Session
from nustd.ui.core import OP_ERROR, Frame, ItemRef, SectionRef, WsSession, encode
from nustd.ui.refs import Column, Row
from nustd.ui.refs.collections.base import CollectionRef
from nustd.ui.refs.leaves.base import LeafRef


class _RecordingSession:
    """Fake WsSession: records the frames it is handed."""

    def __init__(self) -> None:
        self.frames: list[Frame] = []

    async def send(self, frame: Frame) -> None:
        self.frames.append(frame)


def _frames(term: nu.Nu) -> list[Frame]:
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


class Toolbar(Row):
    text = ui.TextRef.slot()


class Page(Column):
    top = ui.DataTableRef.slot(columns=["name"])
    bar = Toolbar.slot(gap=1)


class App(Shape):
    page = Page.slot()


# --- the family ------------------------------------------------------------


def test_leaves_and_containers_are_core_item_refs():
    assert issubclass(ItemRef, shape.ItemRef)
    assert issubclass(ItemRef, ui.Ref)
    for cls in (LeafRef, SectionRef, CollectionRef):
        assert issubclass(cls, ItemRef)


def test_every_shipped_ui_ref_is_an_item_ref():
    refs = [
        obj
        for name in dir(ui)
        if isinstance(obj := getattr(ui, name), type) and issubclass(obj, ui.Ref)
    ]
    assert len(refs) > 50
    assert [r.__name__ for r in refs if not issubclass(r, ItemRef)] == ["Ref"]


def test_descent_returns_item_refs():
    grid = ui.GridRef("g", item=ui.CardRef)
    assert isinstance(grid["a"], ItemRef)
    assert isinstance(App.page.top, ItemRef)
    assert isinstance(App.page.bar.text, ItemRef)


def test_slot_is_a_real_slot():
    spec = ui.DataTableRef.slot(columns=["a"])
    assert isinstance(spec, Slot)
    assert spec.ref_cls is ui.DataTableRef
    assert spec.props["columns"] == ["a"]
    section_spec = Toolbar.slot(gap=2)
    assert isinstance(section_spec, Slot)
    assert section_spec.ref_cls is ui.RowRef
    assert section_spec.kwargs["section_cls"] is Toolbar


# --- .to -------------------------------------------------------------------


def test_to_a_bare_class():
    cell = ui.GridRef("g", item=ui.CardRef)["a"]
    text = cell.to(ui.TextRef)
    assert type(text) is ui.TextRef
    assert text._parent is cell._parent
    assert nu.tree.payload(text)["segment"] == "a"


def test_to_a_slot_spec_with_props():
    table = ui.GridRef("g", item=ui.CardRef)["a"].to(
        ui.DataTableRef.slot(columns=["x"], dense=True)
    )
    assert type(table) is ui.DataTableRef
    assert table._payload["props"]["columns"] == ["x"]
    assert table._payload["props"]["dense"] is True


def test_to_a_section_spec_navigates_its_slots():
    bar = ui.GridRef("g", item=ui.CardRef)["a"].to(Toolbar.slot())
    assert isinstance(bar, ui.RowRef)
    assert isinstance(bar.text, ui.TextRef)
    assert bar.text._parent is bar


def test_to_a_container_spec_with_an_item_template():
    inner = ui.ColumnRef("c").to(ui.GridRef.slot(ui.TextRef, max_columns=2))
    assert type(inner["k"]) is ui.TextRef


def test_to_over_a_shape_slot():
    as_text = App.page.top.to(ui.TextRef)
    assert type(as_text) is ui.TextRef
    assert as_text._parent is not None
    assert as_text._root_shape is App


def test_to_a_leaf_still_refuses_children():
    leaf = ui.ColumnRef("c").to(ui.TextRef.slot())
    with pytest.raises(TypeError, match="is a leaf and holds no children"):
        ui.TextRef("x", parent_ref=leaf)


# --- the wire after .to ----------------------------------------------------


def test_wire_chain_carries_the_new_kind_and_props():
    grid = ui.GridRef("g", item=ui.CardRef)
    term = grid["a"].to(ui.DataTableRef.slot(columns=["x"], dense=True)).set([{"x": 1}])
    (frame,) = _frames(term)
    assert frame.ref == ("g", "a")
    assert [(seg, typ) for seg, typ, _ in frame.chain] == [("g", "Grid"), ("a", "DataTableRef")]
    assert frame.chain[1][2]["columns"] == ["x"]
    assert frame.chain[1][2]["dense"] is True


def test_wire_chain_after_a_nested_to_chain():
    term = (
        ui.ContainerRef("page")
        .to(ui.GridRef.slot(ui.CardRef, max_columns=2))["a"]
        .to(ui.ColumnRef.slot(gap=3))
        .to(ui.ColumnRef.slot(ui.RowRef, gap=3))["r"]
        .to(Toolbar.slot(gap=1))
        .text.set("hi")
    )
    (frame,) = _frames(term)
    assert frame.ref == ("page", "a", "r", "text")
    assert frame.payload == "hi"
    assert [(seg, typ) for seg, typ, _ in frame.chain] == [
        ("page", "Grid"),
        ("a", "Column"),
        ("r", "Row"),
        ("text", "TextRef"),
    ]
    assert frame.chain[0][2]["max_columns"] == 2
    assert frame.chain[1][2]["gap"] == 3
    assert frame.chain[2][2]["gap"] == 1


def test_wire_chain_after_to_over_a_shape():
    (frame,) = _frames(App.page.bar.to(ui.CardRef.slot(title="T")).set_title("U"))
    assert [(seg, typ) for seg, typ, _ in frame.chain] == [
        ("page", "Column"),
        ("bar", "Card"),
    ]
    assert frame.chain[1][2]["title"] == "T"


def test_bare_class_ships_no_props_like_a_hand_built_ref():
    grid = ui.GridRef("g", item=ui.CardRef)
    (via_to,) = _frames(grid["a"].to(ui.TextRef).set("x"))
    (by_hand,) = _frames(ui.TextRef("a", parent_ref=grid).set("x"))
    assert via_to.chain == by_hand.chain


# --- kind mismatch: the browser's refusal surfaces on this side ------------


class _FakeWs:
    """Hands out the queued frames, then disconnects."""

    def __init__(self, *frames: Frame) -> None:
        self._raw = [encode(f) for f in frames]

    async def receive_bytes(self) -> bytes:
        from starlette.websockets import WebSocketDisconnect

        if not self._raw:
            raise WebSocketDisconnect
        return self._raw.pop(0)


def test_inbound_error_frame_is_logged(caplog):
    refused = Frame(
        OP_ERROR,
        ref=("g", "a"),
        payload={
            "code": "kind_mismatch",
            "message": "kind mismatch at g / a: the node is TextRef, the write names DataTableRef",
        },
    )
    session = WsSession(_FakeWs(refused))  # type: ignore[arg-type]
    with caplog.at_level(logging.ERROR, logger="nustd.ui.core.session"):
        asyncio.run(session.run_intake())
    (record,) = caplog.records
    assert record.levelno == logging.ERROR
    assert "kind_mismatch at g/a" in record.getMessage()
    assert "the node is TextRef, the write names DataTableRef" in record.getMessage()


def test_inbound_error_frame_without_a_payload_still_logs(caplog):
    session = WsSession(_FakeWs(Frame(OP_ERROR, ref=("x",))))  # type: ignore[arg-type]
    with caplog.at_level(logging.ERROR, logger="nustd.ui.core.session"):
        asyncio.run(session.run_intake())
    assert len(caplog.records) == 1
