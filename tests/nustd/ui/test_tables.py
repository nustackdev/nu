"""The two tables: ``TableRef`` (content, cells are places) and ``DataTableRef`` (rows are data).

Wire only, through a fake session, no browser.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nustd.ui as ui
from nu import Context
from nustd.ui import Session
from nustd.ui.core import Frame, ItemRef


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list[Frame] = []

    async def send(self, frame: Frame) -> None:
        self.frames.append(frame)


def _frames(term: nu.Nu) -> list[Frame]:
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _kinds(frame: Frame) -> list[tuple[str, str]]:
    return [(seg, typ) for seg, typ, _ in frame.chain]


# --- TableRef: a content table ---------------------------------------------


def test_cell_is_a_place_under_its_row():
    t = ui.TableRef("t", props={"header": ["Part", "Status"]})
    (frame,) = _frames(t[0, 1].to(ui.BadgeRef).set("ok"))
    assert frame.ref == ("t", "0", "1")
    assert _kinds(frame) == [("t", "Table"), ("0", "TableRow"), ("1", "BadgeRef")]
    assert frame.chain[0][2]["header"] == ["Part", "Status"]


def test_header_cell():
    t = ui.TableRef("t")
    (frame,) = _frames(t.header[2].to(ui.TextRef).set("Status"))
    assert frame.ref == ("t", "header", "2")
    assert _kinds(frame)[1] == ("header", "TableRow")


def test_bare_cell_without_item():
    cell = ui.TableRef("t")[1, 1]
    assert type(cell) is ItemRef


def test_item_is_the_default_cell_kind():
    t = ui.TableRef("t", item=ui.TextRef.slot(tone="muted"))
    cell = t[3, 0]
    assert type(cell) is ui.TextRef
    assert cell._payload["props"]["tone"] == "muted"
    assert type(t.header[0]) is ui.TextRef
    (frame,) = _frames(cell.set("x"))
    assert frame.ref == ("t", "3", "0")


def test_item_on_slot():
    class Page(ui.Column):
        specs = ui.TableRef.slot(ui.TextRef, header=["a"], density="compact")

    (frame,) = _frames(Page.specs[0, 0].set("hi"))
    assert _kinds(frame) == [("specs", "Table"), ("0", "TableRow"), ("0", "TextRef")]
    assert frame.chain[0][2]["density"] == "compact"


def test_rows_and_cells_by_method():
    t = ui.TableRef("t")
    assert type(t[2]) is ui.TableRowRef
    assert type(t.row(2)) is ui.TableRowRef
    (frame,) = _frames(t.row(2).cell(1).to(ui.TextRef).set("x"))
    assert frame.ref == ("t", "2", "1")
    (frame,) = _frames(t.cell(4, 0).to(ui.TextRef).set("y"))
    assert frame.ref == ("t", "4", "0")


def test_nesting_continues_through_a_cell():
    t = ui.TableRef("t")
    inner = t[0, 0].to(ui.RowRef.slot(gap=2))[1].to(ui.ButtonRef)
    (frame,) = _frames(inner.set_label("Open"))
    assert frame.ref == ("t", "0", "0", "1")
    assert [typ for _, typ, _ in frame.chain] == ["Table", "TableRow", "Row", "ButtonRef"]


@pytest.mark.parametrize(
    ("at", "error"),
    [
        (("a", 0), TypeError),
        ((0, "a"), TypeError),
        ((-1, 0), IndexError),
        ((0, -1), IndexError),
        ((True, 0), TypeError),
        ((None, 0), TypeError),
        ((0, 1, 2), TypeError),
    ],
)
def test_keys_are_positions_only(at, error):
    with pytest.raises(error):
        ui.TableRef("t")[at]


def test_header_row_cells_are_positions_too():
    with pytest.raises(TypeError):
        ui.TableRef("t").header["x"]


def test_slot_props_normalized():
    s = ui.TableRef.slot(
        header=["a", "b"],
        align=["left", "right"],
        variant="striped",
        spans={(0, 0): 2, ("header", 1): (1, 1), (1, 0): (2, 3)},
    )
    assert s.props["align"] == ["left", "right"]
    assert s.props["spans"] == {"0,0": {"cols": 2, "rows": 1}, "1,0": {"cols": 2, "rows": 3}}
    with pytest.raises(ValueError, match="column align"):
        ui.TableRef.slot(align=["middle"])
    with pytest.raises(ValueError, match="at least 1 by 1"):
        ui.TableRef.slot(spans={(0, 0): 0})


def test_chrome_writes():
    t = ui.TableRef("t")
    frames = _frames(t.set_header(["x", "y"]) >> t.set_align(["right"]) >> t.set_span((1, 0), 2))
    assert [f.op for f in frames] == ["write", "write", "set_span"]
    assert frames[0].payload == {"header": ["x", "y"]}
    assert frames[1].payload == {"align": ["right"]}
    assert frames[2].payload == {"key": "1,0", "cols": 2, "rows": 1}


def test_header_span_key():
    (frame,) = _frames(ui.TableRef("t").set_span(("header", 0), 3))
    assert frame.payload["key"] == "header,0"


def test_row_erase_takes_the_row():
    (frame,) = _frames(ui.TableRef("t")[2].erase())
    assert frame.ref == ("t", "2")


# --- DataTableRef: per-column cell specs -----------------------------------


def test_column_cell_spec_lowers_to_the_wire():
    s = ui.DataTableRef.slot(
        columns=[
            "name",
            {"key": "status", "cell": ui.BadgeRef.slot(variant="info")},
            {"key": "seen", "cell": ui.RelativeTimeRef},
        ],
    )
    name, status, seen = s.props["columns"]
    assert name == "name"
    assert status["cell"]["kind"] == "BadgeRef"
    assert status["cell"]["props"]["variant"] == "info"
    assert status["cell"]["prop"] == "label"
    assert seen["cell"] == {"kind": "RelativeTimeRef", "props": {}, "prop": "ts"}


def test_column_cell_spec_on_set_columns_and_set():
    t = ui.DataTableRef("t")
    cols = [{"key": "s", "cell": ui.StatusDotRef}]
    frames = _frames(t.set_columns(cols) >> t.set({"columns": cols, "rows": []}))
    assert frames[0].payload["columns"][0]["cell"]["kind"] == "StatusDotRef"
    assert frames[1].payload["columns"][0]["cell"]["prop"] == "tone"


def test_lowered_cell_spec_passes_through():
    lowered = {"kind": "TextRef", "props": {"tone": "muted"}, "prop": "value"}
    s = ui.DataTableRef.slot(columns=[{"key": "a", "cell": lowered}])
    assert s.props["columns"][0]["cell"] == lowered


def test_column_cell_spec_refuses_other_kinds():
    with pytest.raises(TypeError, match="cannot draw as ButtonRef"):
        ui.DataTableRef.slot(columns=[{"key": "a", "cell": ui.ButtonRef}])
    with pytest.raises(TypeError, match=r"ref class or a Kind\.slot"):
        ui.DataTableRef.slot(columns=[{"key": "a", "cell": "BadgeRef"}])


def test_data_table_stays_a_leaf():
    with pytest.raises(TypeError, match="DataTableRef is a leaf"):
        ui.TextRef("x", parent_ref=ui.DataTableRef("t"))
