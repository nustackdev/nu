"""IconPickerRef on the wire: slot defaults, the stored spelling, ``set``, setters, reads."""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Moves, Session
from nustd.ui.refs import IconPickerRef, Row
from nustd.ui.refs.leaves.icon_picker import normalize_icon


class _Tab:
    def __init__(self, value: object = None) -> None:
        self.frames: list = []
        self.reads: list = []
        self.value = value

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...], field: str | None = None) -> object:
        self.reads.append(path)
        return self.value


def _mount(widget_slot):
    sec = type("ISec", (Row,), {"w": widget_slot})
    page = type("IPage", (Column,), {"sec": sec.slot()})
    app = type("IApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _run(term, tab: _Tab | None = None):
    tab = tab or _Tab()
    out, _ = asyncio.run(nu.arun(term, Context().bind(Session, tab)))
    return out, tab


def _payload(term):
    _, tab = _run(term)
    return tab.frames[0].payload


def test_normalize_folds_every_spelling_to_one():
    assert normalize_icon("") == ""
    assert normalize_icon("  ") == ""
    assert normalize_icon("folder") == "lucide:folder"
    assert normalize_icon("lucide:FileText") == "lucide:file-text"
    assert normalize_icon("Gamepad2") == "lucide:gamepad-2"
    assert normalize_icon(" emoji:🌱 ") == "emoji:🌱"


@pytest.mark.parametrize("raw", ["emoji:", "lucide:", "mdi:home", "lucide:a:b"])
def test_normalize_rejects_what_is_no_icon(raw):
    with pytest.raises(ValueError):
        normalize_icon(raw)


def test_seeds_no_icon_both_kinds_and_clearable():
    props = IconPickerRef.slot().props
    assert props["value"] == ""
    assert props["kinds"] == ["emoji", "lucide"]
    assert props["clearable"] is True
    assert props["placeholder"] == ""


def test_seed_folds_the_value_and_takes_the_kinds():
    props = IconPickerRef.slot(value="FileText", kinds=("lucide", "lucide")).props
    assert props["value"] == "lucide:file-text"
    assert props["kinds"] == ["lucide"]
    with pytest.raises(ValueError, match="kinds"):
        IconPickerRef.slot(kinds=("glyphs",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least one"):
        IconPickerRef.slot(kinds=())


def test_set_folds_a_literal_and_passes_the_rest():
    handle = _mount(IconPickerRef.slot())
    assert _payload(handle.set("Rocket")) == "lucide:rocket"
    assert _payload(handle.set("emoji:🐱")) == "emoji:🐱"
    assert _payload(handle.set("")) == ""
    assert _payload(handle.set(nu.Str("lucide:cpu"))) == "lucide:cpu"
    with pytest.raises(ValueError):
        handle.set("mdi:home")


def test_setters_merge_one_key():
    handle = _mount(IconPickerRef.slot())
    assert _payload(handle.set_kinds(["emoji"])) == {"kinds": ["emoji"]}
    assert _payload(handle.set_clearable(False)) == {"clearable": False}
    assert _payload(handle.set_placeholder("Pick one")) == {"placeholder": "Pick one"}
    assert _payload(handle.set_label("Icon")) == {"label": "Icon"}


def test_reads_the_stored_icon_and_is_a_discrete_pick():
    handle = _mount(IconPickerRef.slot())
    out, tab = _run(handle, _Tab("emoji:🌱"))
    assert out == "emoji:🌱"
    assert tab.reads == [("page", "sec", "w")]
    assert hasattr(handle, "on_change")
    assert not issubclass(IconPickerRef, Moves)
    assert not hasattr(IconPickerRef, "on_submit")
