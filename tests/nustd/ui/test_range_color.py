"""RangeSliderRef and ColorPickerRef on the wire: slot defaults, ``set``, setters, reads."""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Session
from nustd.ui.refs import ColorPickerRef, RangeSliderRef, Row


class _Tab:
    def __init__(self, value: object = None) -> None:
        self.frames: list = []
        self.reads: list = []
        self.value = value

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...]) -> object:
        self.reads.append(path)
        return self.value


def _mount(widget_slot):
    sec = type("RSec", (Row,), {"w": widget_slot})
    page = type("RPage", (Column,), {"sec": sec.slot()})
    app = type("RApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _run(term, tab: _Tab | None = None):
    tab = tab or _Tab()
    out, _ = asyncio.run(nu.arun(term, Context().bind(Session, tab)))
    return out, tab


def _payload(term):
    _, tab = _run(term)
    return tab.frames[0].payload


# ---- RangeSliderRef ---------------------------------------------------------


def test_range_seeds_the_whole_span_and_the_thumb_names():
    props = RangeSliderRef.slot(min=10, max=90).props
    assert props["value"] == [10, 90]
    assert props["thumb_labels"] == ["Minimum", "Maximum"]
    assert props["format"] == "{}"
    assert props["marks"] == []
    assert props["show_value"] is True


def test_range_orders_a_seed_and_rejects_a_non_pair():
    assert RangeSliderRef.slot(value=(60, 20)).props["value"] == [20.0, 60.0]
    with pytest.raises(ValueError, match="pair"):
        RangeSliderRef.slot(value=[1, 2, 3])


def test_range_marks_take_three_shapes():
    props = RangeSliderRef.slot(marks=[0, (50, "half"), {"value": 100, "label": "all"}]).props
    assert props["marks"] == [
        {"value": 0.0},
        {"value": 50.0, "label": "half"},
        {"value": 100.0, "label": "all"},
    ]


def test_range_set_writes_the_pair_bare_or_with_bounds():
    handle = _mount(RangeSliderRef.slot())
    assert _payload(handle.set((20, 40))) == [20, 40]
    assert _payload(handle.set([1, 2], max=10)) == {"value": [1, 2], "max": 10}


def test_range_setters_merge_one_key():
    handle = _mount(RangeSliderRef.slot())
    assert _payload(handle.set_min(5)) == {"min": 5}
    assert _payload(handle.set_format("{}%")) == {"format": "{}%"}
    assert _payload(handle.set_marks([1, (2, "two")])) == {
        "marks": [{"value": 1.0}, {"value": 2.0, "label": "two"}]
    }
    assert _payload(handle.set_label("Span")) == {"label": "Span"}


def test_range_reads_the_pair():
    handle = _mount(RangeSliderRef.slot())
    out, tab = _run(handle, _Tab([20, 40]))
    assert out == [20, 40]
    assert tab.reads == [("page", "sec", "w")]


# ---- ColorPickerRef ---------------------------------------------------------


def test_color_seeds_black_and_folds_a_hex():
    assert ColorPickerRef.slot().props["value"] == "#000000"
    assert ColorPickerRef.slot(value="#ABC").props["value"] == "#aabbcc"
    assert ColorPickerRef.slot(value="8946DB").props["value"] == "#8946db"
    with pytest.raises(ValueError, match="hex"):
        ColorPickerRef.slot(value="red")


def test_color_swatches_are_hex_or_the_palette():
    assert ColorPickerRef.slot().props["swatches"] is None
    assert ColorPickerRef.slot(swatches="palette").props["swatches"] == "palette"
    assert ColorPickerRef.slot(swatches=["#FFF", "123456"]).props["swatches"] == [
        "#ffffff",
        "#123456",
    ]
    with pytest.raises(ValueError):
        ColorPickerRef.slot(swatches="rainbow")  # type: ignore[arg-type]


def test_color_set_folds_a_hex_literal_and_passes_the_rest():
    handle = _mount(ColorPickerRef.slot())
    assert _payload(handle.set("#F0F")) == "#ff00ff"
    assert _payload(handle.set(nu.Str("#123456"))) == "#123456"
    assert _payload(handle.set("nope")) == "nope"


def test_color_setters_merge_one_key():
    handle = _mount(ColorPickerRef.slot())
    assert _payload(handle.set_swatches("palette")) == {"swatches": "palette"}
    assert _payload(handle.set_show_hex(False)) == {"show_hex": False}
    assert _payload(handle.set_required(True)) == {"required": True}


def test_color_reads_the_hex_and_submits():
    handle = _mount(ColorPickerRef.slot())
    out, _ = _run(handle, _Tab("#4269d0"))
    assert out == "#4269d0"
    assert hasattr(ColorPickerRef, "on_submit")
