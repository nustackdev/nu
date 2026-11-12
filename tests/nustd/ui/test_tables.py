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
    t = ui.TableRef("t", props={"columns": ["Part", "Status"]})
    (frame,) = _frames(t[0, 1].to(ui.BadgeRef).set("ok"))
    assert frame.ref == ("t", "0", "1")
    assert _kinds(frame) == [("t", "Table"), ("0", "TableRow"), ("1", "BadgeRef")]
    assert frame.chain[0][2]["columns"] == [{"key": "Part"}, {"key": "Status"}]


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
        specs = ui.TableRef.slot(ui.TextRef, columns=["a"], density="compact")

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
        columns=["a", {"label": "b", "align": "end"}],
        variant="striped",
        span={(0, 0): 2, ("header", 1): 1, (1, 0): {"cols": 2, "rows": 3}},
    )
    assert s.props["columns"] == [{"key": "a"}, {"label": "b", "align": "end"}]
    assert s.props["variant"] == "striped"
    assert s.props["span"] == {"0,0": {"cols": 2, "rows": 1}, "1,0": {"cols": 2, "rows": 3}}


def test_looks_ship_only_when_set():
    props = ui.TableRef.slot().props
    assert "variant" not in props
    assert "density" not in props
    with pytest.raises(ValueError, match="variant"):
        ui.TableRef.slot(variant="zebra")
    with pytest.raises(ValueError, match="density"):
        ui.TableRef.slot(density="dense")


@pytest.mark.parametrize(
    ("span", "error"),
    [(0, ValueError), ((2, 1), TypeError), ({"cols": 2, "wide": 1}, ValueError), (True, TypeError)],
)
def test_span_values(span, error):
    with pytest.raises(error):
        ui.TableRef.slot(span={(0, 0): span})


def test_span_keys_are_places():
    with pytest.raises(TypeError):
        ui.TableRef.slot(span={0: 2})
    with pytest.raises(TypeError):
        ui.TableRef.slot(span={("x", 0): 2})


def test_set_columns_and_set_child():
    t = ui.TableRef("t")
    frames = _frames(
        t.set_columns(["x", {"key": "y", "align": "end"}])
        >> t.set_child((1, 0), span=2)
        >> t.set_child((1, 0), span=1)
        >> t.set_child(("header", 0), span={"cols": 3})
    )
    assert [f.op for f in frames] == ["write", "set_child", "set_child", "set_child"]
    assert frames[0].payload == {"columns": [{"key": "x"}, {"key": "y", "align": "end"}]}
    assert frames[1].payload == {"key": "1,0", "span": {"cols": 2, "rows": 1}}
    assert frames[2].payload == {"key": "1,0", "span": None}
    assert frames[3].payload == {"key": "header,0", "span": {"cols": 3, "rows": 1}}


def test_set_child_keeps_only_span():
    with pytest.raises(TypeError, match="grow"):
        ui.TableRef("t").set_child((0, 0), grow=1)


def test_size_layer():
    s = ui.TableRef.slot(max_height=240, scroll="y")
    assert (s.props["max_height"], s.props["scroll"]) == (240, "y")
    with pytest.raises(TypeError, match="gap"):
        ui.TableRef.slot(gap=2)


# --- the column record, both tables ----------------------------------------


@pytest.mark.parametrize("table", [ui.TableRef, ui.DataTableRef])
def test_column_record(table):
    s = table.slot(
        columns=[
            {
                "key": "a",
                "label": "A",
                "width": 120,
                "min_width": "4rem",
                "max_width": "prose",
                "wrap": "truncate",
                "hide_below": 480,
                "align": "center",
            }
        ]
    )
    assert s.props["columns"] == [
        {
            "key": "a",
            "label": "A",
            "width": 120,
            "min_width": "4rem",
            "max_width": "prose",
            "wrap": "truncate",
            "hide_below": 480,
            "align": "center",
        }
    ]


@pytest.mark.parametrize("table", [ui.TableRef, ui.DataTableRef])
@pytest.mark.parametrize(
    ("column", "error", "match"),
    [
        ({"key": "a", "titel": "x"}, ValueError, "takes no titel"),
        ({"key": "a", "wrap": "clip"}, ValueError, "wrap"),
        ({"key": "a", "align": "right"}, ValueError, "align"),
        ({"key": "a", "width": "wide"}, ValueError, "width"),
        ({"key": "a", "width": True}, TypeError, "width"),
        ({"key": "a", "hide_below": "480px"}, ValueError, "hide_below"),
        ({"key": "a", "hide_below": -1}, ValueError, "hide_below"),
        (3, TypeError, "column"),
    ],
)
def test_column_record_refuses(table, column, error, match):
    with pytest.raises(error, match=match):
        table.slot(columns=[column])


def test_content_table_takes_no_data_keys():
    with pytest.raises(ValueError, match="kind"):
        ui.TableRef.slot(columns=[{"key": "a", "kind": "number"}])


def test_data_table_data_keys():
    s = ui.DataTableRef.slot(
        columns=[{"key": "a", "kind": "select", "options": ["x", 1], "editable": False}]
    )
    assert s.props["columns"] == [
        {"key": "a", "kind": "select", "options": ["x", "1"], "editable": False}
    ]
    with pytest.raises(ValueError, match="kind"):
        ui.DataTableRef.slot(columns=[{"key": "a", "kind": "date"}])
    with pytest.raises(TypeError, match="flag"):
        ui.DataTableRef.slot(columns=[{"key": "a", "sortable": "no"}])


def test_data_table_looks():
    props = ui.DataTableRef.slot().props
    assert "variant" not in props
    assert "density" not in props
    s = ui.DataTableRef.slot(variant="borderless", density="compact")
    assert (s.props["variant"], s.props["density"]) == ("borderless", "compact")
    with pytest.raises(ValueError, match="variant"):
        ui.DataTableRef.slot(variant="zebra")


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
    assert name == {"key": "name"}
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
