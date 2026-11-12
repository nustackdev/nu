"""Container layout: the four layers, the per child maps, set_child and set_layout.

Every container reads its layout through one helper, so the same prop is
checked the same way everywhere, and a prop ships only when it is set.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nustd.ui as ui
from nu import Context
from nustd.ui import Session
from nustd.ui.refs.collections.layout import normalize_length


class _Recording:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _one(term):
    sess = _Recording()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    (frame,) = sess.frames
    return frame.op, frame.payload


SIZE = {
    "width": 320,
    "min_width": "12rem",
    "max_width": "prose",
    "height": "60vh",
    "min_height": 0,
    "max_height": 480,
    "scroll": "y",
}

EVERY = [
    ui.ColumnRef,
    ui.RowRef,
    ui.GridRef,
    ui.LineRef,
    ui.ListRef,
    ui.ContainerRef,
    ui.CardRef,
    ui.ModalRef,
    ui.SheetRef,
    ui.PageSectionRef,
    ui.FormRef,
    ui.FieldsetRef,
    ui.FieldRef,
    ui.TabsRef,
    ui.AccordionRef,
    ui.CollapsibleRef,
    ui.NavListRef,
    ui.TableRef,
]

LAYOUT = {
    "width",
    "min_width",
    "max_width",
    "height",
    "min_height",
    "max_height",
    "scroll",
    "padding",
    "gap",
    "justify",
    "align",
    "divided",
    "grow",
    "basis",
    "span",
    "align_self",
    "sticky",
    "wrap",
    "stack_below",
    "max_columns",
    "min_cell_width",
    "dense",
    "center",
}


# --- every container ---------------------------------------------------------


@pytest.mark.parametrize("ref", EVERY)
def test_a_container_that_says_nothing_ships_no_layout(ref):
    assert not LAYOUT & set(ref.slot().props)


@pytest.mark.parametrize("ref", EVERY)
def test_every_container_takes_the_size_layer(ref):
    props = ref.slot(**SIZE).props
    assert {k: props[k] for k in SIZE} == SIZE


@pytest.mark.parametrize("ref", EVERY)
def test_an_unknown_layout_name_fails_loud(ref):
    with pytest.raises(TypeError, match="takes no"):
        ref.slot(gapp=1)


@pytest.mark.parametrize(
    "ref",
    [
        ui.ColumnRef,
        ui.RowRef,
        ui.GridRef,
        ui.ListRef,
        ui.ContainerRef,
        ui.CardRef,
        ui.ModalRef,
        ui.SheetRef,
        ui.PageSectionRef,
        ui.FormRef,
        ui.FieldsetRef,
        ui.CollapsibleRef,
        ui.NavListRef,
    ],
)
def test_space_is_one_scale(ref):
    props = ref.slot(gap=0, padding=16).props
    assert (props["gap"], props["padding"]) == (0, 16)
    with pytest.raises(ValueError, match="0 to 16"):
        ref.slot(gap=17)
    with pytest.raises(TypeError, match="0 to 16"):
        ref.slot(padding="md")


def test_holders_take_only_what_applies():
    assert ui.FieldRef.slot(gap=2).props["gap"] == 2
    for ref in (ui.TabsRef, ui.AccordionRef, ui.TableRef):
        with pytest.raises(TypeError, match="takes no gap"):
            ref.slot(gap=2)
    with pytest.raises(TypeError, match="takes no align"):
        ui.LineRef.slot(align="center")


# --- lengths -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "wire"),
    [(240, 240), ("320", 320), (" 20rem ", "20rem"), ("100%", "100%"), ("main", "main")],
)
def test_a_length_is_px_css_text_or_a_page_width(value, wire):
    assert normalize_length("X", "width", value) == wire


@pytest.mark.parametrize(
    ("value", "error"),
    [
        (-1, ValueError),
        ("tall", ValueError),
        ("calc(1px)", ValueError),
        (True, TypeError),
        ([1], TypeError),
    ],
)
def test_a_bad_length_is_refused(value, error):
    with pytest.raises(error):
        ui.ColumnRef.slot(height=value)


def test_scroll_words():
    with pytest.raises(ValueError, match="y, x, both"):
        ui.ColumnRef.slot(scroll="down")


# --- arrange -----------------------------------------------------------------


def test_justify_is_the_main_axis_and_align_the_cross_one():
    assert ui.RowRef.slot(justify="between", align="baseline").props == {
        "justify": "between",
        "align": "baseline",
    }
    assert ui.LineRef.slot(justify="center").props == {"justify": "center"}
    with pytest.raises(ValueError, match="align is one of"):
        ui.ColumnRef.slot(align="baseline")
    with pytest.raises(ValueError, match="justify is one of"):
        ui.RowRef.slot(justify="evenly")
    assert ui.GridRef.slot(justify="center").props == {"justify": "center"}


# --- surfaces ----------------------------------------------------------------


def test_surface_props_ship_only_when_set():
    assert not {"variant", "size"} & set(ui.CardRef.slot().props)
    assert "size" not in ui.PageSectionRef.slot().props


def test_card_surface_preset_and_explicit_layers():
    props = ui.CardRef.slot(variant="plain", size="sm", padding=2, gap=1).props
    assert {k: props[k] for k in ("variant", "size", "padding", "gap")} == {
        "variant": "plain",
        "size": "sm",
        "padding": 2,
        "gap": 1,
    }
    with pytest.raises(ValueError, match="variant is one of"):
        ui.CardRef.slot(variant="loud")


def test_modal_and_sheet_take_width_not_a_size_preset():
    assert ui.ModalRef.slot(width=672).props["width"] == 672
    assert ui.SheetRef.slot(width="prose").props["width"] == "prose"
    with pytest.raises(TypeError):
        ui.ModalRef.slot(size="lg")


def test_page_section_size_and_divided_parent():
    assert ui.PageSectionRef.slot(size="lg").props["size"] == "lg"
    assert ui.ColumnRef.slot(divided=True).props == {"divided": True}
    with pytest.raises(TypeError):
        ui.PageSectionRef.slot(bordered=True)


def test_container_caps_by_max_width():
    assert ui.ContainerRef.slot(max_width="dashboard", gap=8).props == {
        "max_width": "dashboard",
        "gap": 8,
    }


# --- per child maps ----------------------------------------------------------


def test_flow_maps_key_by_child():
    props = ui.RowRef.slot(
        grow={"main": 2, 0: 1.5},
        basis={"side": 280, "x": "12rem"},
        align_self={"b": "baseline"},
        sticky={"head": "left"},
    ).props
    assert props["grow"] == {"main": 2, "0": 1.5}
    assert props["basis"] == {"side": 280, "x": "12rem"}
    assert props["align_self"] == {"b": "baseline"}
    assert props["sticky"] == {"head": "left"}


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"grow": {"0": 1}}, ValueError),
        ({"grow": {-1: 1}}, IndexError),
        ({"grow": {"a": -2}}, ValueError),
        ({"grow": {"a": "x"}}, TypeError),
        ({"grow": {True: 1}}, TypeError),
        ({"sticky": {"a": "left"}}, ValueError),
        ({"align_self": {"a": "baseline"}}, ValueError),
        ({"span": {"a": 2}}, TypeError),
    ],
)
def test_bad_column_maps_are_refused(kwargs, error):
    with pytest.raises(error):
        ui.ColumnRef.slot(**kwargs)


def test_card_maps_refuse_its_parts():
    with pytest.raises(ValueError, match="own part"):
        ui.CardRef.slot(grow={"actions": 1})


def test_grid_span_is_an_int_or_a_mapping_never_a_tuple():
    assert ui.GridRef.slot(span={"a": 2, "b": {"rows": 2}, "c": 1}).props["span"] == {
        "a": {"cols": 2, "rows": 1},
        "b": {"cols": 1, "rows": 2},
    }
    with pytest.raises(TypeError, match="not tuple"):
        ui.GridRef.slot(span={"a": (2, 1)})
    with pytest.raises(ValueError, match="takes cols and rows"):
        ui.GridRef.slot(span={"a": {"columns": 2}})


def test_placed_grid_keys_maps_by_place():
    props = ui.GridRef.slot(cols=2, span={(0, 1): {"rows": 2}}, align_self={(1, 0): "end"}).props
    assert props["span"] == {"0,1": {"cols": 1, "rows": 2}}
    assert props["align_self"] == {"1,0": "end"}
    with pytest.raises(ValueError, match="placed grid"):
        ui.GridRef.slot(span={(0, 1): 2})


def test_props_on_the_constructor_go_through_the_slot():
    row = ui.RowRef("r", props={"grow": {"main": 2}, "scroll": "x"})
    assert row._payload["props"] == {"grow": {"main": 2}, "scroll": "x"}


# --- run time ----------------------------------------------------------------


def test_set_child_merges_one_child():
    row = ui.RowRef("r")
    assert _one(row.set_child("main", grow=2, basis=None)) == (
        "set_child",
        {"key": "main", "grow": 2, "basis": None},
    )
    assert _one(row.set_child(row["side"], align_self="end")) == (
        "set_child",
        {"key": "side", "align_self": "end"},
    )


def test_set_child_on_a_grid_span_and_place():
    grid = ui.GridRef("g", props={"cols": 2})
    assert _one(grid.set_child((1, 0), span=2)) == (
        "set_child",
        {"key": "1,0", "span": {"cols": 2, "rows": 1}},
    )
    assert _one(grid.set_child((1, 0), span=1)) == ("set_child", {"key": "1,0", "span": None})


def test_set_child_reads_a_cell_for_its_place():
    t = ui.TableRef("t", props={"columns": ["a", "b"]})
    assert _one(t.set_child(t[0, 1], span=2)) == (
        "set_child",
        {"key": "0,1", "span": {"cols": 2, "rows": 1}},
    )
    assert _one(t.set_child(t.header[1], span=2))[1]["key"] == "header,1"
    grid = ui.GridRef("g", props={"cols": 2})
    assert _one(grid.set_child(grid[1, 0], span=2))[1]["key"] == "1,0"


def test_set_child_refuses_a_child_of_another_container():
    with pytest.raises(ValueError, match="child of its own"):
        ui.RowRef("r").set_child(ui.RowRef("o")["k"], grow=1)
    other = ui.TableRef("o")
    with pytest.raises(ValueError, match="its own cells"):
        ui.TableRef("t").set_child(other[0, 1], span=2)


def test_set_child_refuses_what_the_container_does_not_keep():
    with pytest.raises(TypeError, match="keeps no span"):
        ui.RowRef("r").set_child("a", span=2)
    with pytest.raises(TypeError, match="keeps no grow"):
        ui.GridRef("g").set_child("a", grow=1)
    with pytest.raises(TypeError, match="changes nothing"):
        ui.RowRef("r").set_child("a")
    with pytest.raises(TypeError, match="not tuple"):
        ui.GridRef("g").set_child("a", span=(2, 1))


def test_set_layout_writes_checked_layer_props():
    assert _one(ui.CardRef("c").set_layout(gap=2, max_height=None)) == (
        "write",
        {"gap": 2, "max_height": None},
    )
    with pytest.raises(ValueError, match="0 to 16"):
        ui.CardRef("c").set_layout(gap=20)
    with pytest.raises(TypeError, match="set_layout takes"):
        ui.TabsRef("t").set_layout(gap=2)


def test_set_layout_takes_family_and_surface_props():
    assert _one(ui.RowRef("r").set_layout(wrap=True, stack_below=640, gap=2)) == (
        "write",
        {"wrap": True, "stack_below": 640, "gap": 2},
    )
    assert _one(ui.LineRef("l").set_layout(wrap=False)) == ("write", {"wrap": False})
    assert _one(ui.CardRef("c").set_layout(variant="plain", size=None)) == (
        "write",
        {"variant": "plain", "size": None},
    )
    assert _one(ui.TableRef("t").set_layout(variant="striped", density="compact")) == (
        "write",
        {"variant": "striped", "density": "compact"},
    )
    with pytest.raises(TypeError, match="wrap is True or False"):
        ui.RowRef("r").set_layout(wrap=1)
    with pytest.raises(ValueError, match="variant is one of"):
        ui.CardRef("c").set_layout(variant="loud")


def test_set_layout_names_what_it_takes_on_an_unknown_name():
    with pytest.raises(TypeError, match=r"set_layout takes .*stack_below.*wrap.*; not grow"):
        ui.RowRef("r").set_layout(grow=1)
    with pytest.raises(TypeError, match=r"takes .*size.*variant.*; not center"):
        ui.CardRef("c").set_layout(center=True)


def test_a_table_row_has_no_layout():
    row = ui.TableRef("t")[0]
    assert not hasattr(row, "set_layout")
