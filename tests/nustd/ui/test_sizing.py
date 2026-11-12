"""Sizing: height and scroll on containers, grow and basis for a Row's or Column's child.

The props ship only when set, so a container that says nothing sends what
it always sent.
"""

from __future__ import annotations

import pytest

import nustd.ui as ui


@pytest.mark.parametrize("ref", [ui.ColumnRef, ui.RowRef, ui.GridRef, ui.BoxRef])
def test_unsized_containers_ship_nothing_new(ref):
    props = ref.slot().props
    assert not {"height", "max_height", "scroll", "grow", "basis"} & set(props)


@pytest.mark.parametrize("ref", [ui.ColumnRef, ui.RowRef, ui.GridRef, ui.BoxRef])
def test_height_max_height_scroll(ref):
    props = ref.slot(height=240, max_height="60vh", scroll="both").props
    assert props["height"] == 240
    assert props["max_height"] == "60vh"
    assert props["scroll"] == "both"


def test_lengths_normalize():
    props = ui.ColumnRef.slot(height="320", max_height=" 20rem ").props
    assert props["height"] == 320
    assert props["max_height"] == "20rem"


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"height": -1}, ValueError),
        ({"height": "tall"}, ValueError),
        ({"height": "calc(100% - 1px)"}, ValueError),
        ({"height": True}, TypeError),
        ({"max_height": [1]}, TypeError),
        ({"scroll": "down"}, ValueError),
    ],
)
def test_bad_sizes_are_refused(kwargs, error):
    with pytest.raises(error):
        ui.ColumnRef.slot(**kwargs)


def test_row_grow_and_basis_key_by_child():
    props = ui.RowRef.slot(grow={"main": 2, 0: 1}, basis={"side": 280}).props
    assert props["grow"] == {"main": 2, "0": 1}
    assert props["basis"] == {"side": 280}


def test_column_grow():
    props = ui.ColumnRef.slot(height=400, grow={"list": 1}).props
    assert props["grow"] == {"list": 1}


@pytest.mark.parametrize(
    ("grow", "error"),
    [
        ({"0": 1}, ValueError),
        ({-1: 1}, IndexError),
        ({"a": -2}, ValueError),
        ({"a": "x"}, TypeError),
        ({True: 1}, TypeError),
    ],
)
def test_bad_weights_are_refused(grow, error):
    with pytest.raises(error):
        ui.RowRef.slot(grow=grow)


def test_props_on_the_constructor_go_through_the_slot():
    row = ui.RowRef("r", props={"grow": {"main": 2}, "scroll": "x"})
    assert row._payload["props"]["grow"] == {"main": 2}
    assert row._payload["props"]["scroll"] == "x"


def test_modal_size():
    assert ui.ModalRef.slot().props["size"] == "md"
    assert ui.ModalRef.slot(size="xl").props["size"] == "xl"
