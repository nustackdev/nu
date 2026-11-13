"""Choice inputs on the wire: SegmentedControlRef, CheckboxGroupRef,
MultiSelectRef and AutocompleteRef. Slot defaults, the ``set`` payload, the
setters that merge one key, and a read round trip, through a fake session.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Session
from nustd.ui.refs import (
    AutocompleteRef,
    CheckboxGroupRef,
    MultiSelectRef,
    Row,
    SegmentedControlRef,
)


class _Session:
    """Fake session: records frames, answers reads with a fixed value."""

    def __init__(self, value: object = None) -> None:
        self.frames: list = []
        self.value = value

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...]) -> object:
        return self.value


def _mount(widget_slot):
    sec = type("CSec", (Row,), {"w": widget_slot})
    page = type("CPage", (Column,), {"sec": sec.slot()})
    app = type("CApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _frames(term):
    sess = _Session()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _read(handle, value):
    return asyncio.run(nu.arun(handle, Context().bind(Session, _Session(value))))[0]


OPTS = ["a", {"value": "b", "label": "Bee"}]
NORMALIZED = [{"value": "a", "label": "a"}, {"value": "b", "label": "Bee"}]


def test_segmented_control_slot():
    props = SegmentedControlRef.slot(options=OPTS, value="b").props
    assert props["options"] == NORMALIZED
    assert props["value"] == "b"
    assert props["fill"] is False
    assert "orientation" not in props


def test_checkbox_group_slot():
    props = CheckboxGroupRef.slot(options=OPTS, value=["a"]).props
    assert props["options"] == NORMALIZED
    assert props["value"] == ["a"]
    assert props["orientation"] == "vertical"
    assert CheckboxGroupRef.slot().props["value"] == []


def test_multi_select_slot():
    props = MultiSelectRef.slot(options=OPTS, placeholder="Pick").props
    assert props["options"] == NORMALIZED
    assert props["value"] == []
    assert props["placeholder"] == "Pick"


def test_autocomplete_slot():
    props = AutocompleteRef.slot(options=OPTS, value="free text").props
    assert props["options"] == NORMALIZED
    assert props["value"] == "free text"
    assert props["placeholder"] == ""
    assert props["clear_on_submit"] is False


def test_the_seed_list_is_a_copy():
    seed = ["a"]
    props = CheckboxGroupRef.slot(value=seed).props
    seed.append("b")
    assert props["value"] == ["a"]


@pytest.mark.parametrize(
    ("cls", "value"),
    [
        (SegmentedControlRef, "b"),
        (CheckboxGroupRef, ["a", "b"]),
        (MultiSelectRef, ["b"]),
        (AutocompleteRef, "anything"),
    ],
)
def test_set_writes_the_bare_value_and_a_read_returns_it(cls, value):
    handle = _mount(cls.slot(options=OPTS))
    [frame] = _frames(handle.set(value))
    assert frame.op == "write"
    assert frame.payload == value
    assert _read(handle, value) == value


@pytest.mark.parametrize(
    "cls", [SegmentedControlRef, CheckboxGroupRef, MultiSelectRef, AutocompleteRef]
)
def test_set_options_normalizes_and_merges_one_key(cls):
    handle = _mount(cls.slot())
    [frame] = _frames(handle.set_options(OPTS))
    assert frame.payload == {"options": NORMALIZED}


def test_placeholder_setters():
    for cls in (MultiSelectRef, AutocompleteRef):
        handle = _mount(cls.slot())
        assert _frames(handle.set_placeholder("Type"))[0].payload == {"placeholder": "Type"}
    assert not hasattr(SegmentedControlRef, "set_placeholder")
    assert not hasattr(CheckboxGroupRef, "set_placeholder")


def test_only_autocomplete_submits():
    assert hasattr(AutocompleteRef, "on_submit")
    for cls in (SegmentedControlRef, CheckboxGroupRef, MultiSelectRef):
        assert not hasattr(cls, "on_submit"), cls.__name__


def test_common_setters_merge_one_key():
    handle = _mount(CheckboxGroupRef.slot())
    assert _frames(handle.set_label("Genres"))[0].payload == {"label": "Genres"}
    assert _frames(handle.set_disabled(True))[0].payload == {"disabled": True}
    assert _frames(handle.set_readonly(True))[0].payload == {"readonly": True}
    assert _frames(handle.set_required(True))[0].payload == {"required": True}


def test_reset_ships_a_reset_frame():
    handle = _mount(SegmentedControlRef.slot(options=OPTS, value="a"))
    [frame] = _frames(handle.reset())
    assert frame.op == "reset"
    assert frame.chain[-1][1] == "SegmentedControlRef"
