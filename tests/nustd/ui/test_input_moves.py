"""The moving inputs: ``Moves`` gives ``on_input()``, heard per keystroke or drag tick.

A subscription on ``on_input()`` and one on ``on_change()`` over the same
fake tab see a typed value and a slider drag the way the browser sends
them: ``input`` per move, then the ``change`` that commits, each with the
value. Discrete inputs have no ``on_input()``.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Moves, Session
from nustd.ui.core import CHANGE, INPUT, Changed, Readable
from nustd.ui.refs import (
    AutocompleteRef,
    CheckboxRef,
    CodeRef,
    ColorPickerRef,
    DatePickerRef,
    InlineEditRef,
    InputRef,
    MarkdownRef,
    NumberInputRef,
    RangeSliderRef,
    Row,
    SelectRef,
    SketchRef,
    SliderRef,
    SwitchRef,
    TagInputRef,
    TextAreaRef,
    ToggleRef,
)


MOVING = [
    InputRef,
    TextAreaRef,
    CodeRef,
    MarkdownRef,
    NumberInputRef,
    InlineEditRef,
    AutocompleteRef,
    TagInputRef,
    SliderRef,
    RangeSliderRef,
    ColorPickerRef,
    SketchRef,
]

DISCRETE = [CheckboxRef, SwitchRef, ToggleRef, SelectRef, DatePickerRef]


class _Notifies:
    def __init__(self) -> None:
        self.callbacks: list = []

    def bind(self, cb) -> None:
        self.callbacks.append(cb)

    def unbind(self, cb) -> None:
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self) -> None:
        self.callbacks = []


class _Tab:
    """A fake tab: takes subscriptions per path and fires notifies at them."""

    def __init__(self) -> None:
        self.subs: dict = {}
        self.asked: list = []

    async def send(self, frame: object) -> None:
        pass

    async def aread(self, path, field=None) -> object:
        raise AssertionError("an event carries its value: nothing reads back")

    def subscribe(self, path, event=None):
        self.asked.append((path, event))
        return self.subs.setdefault(path, _Notifies())

    def notify(self, path, payload) -> None:
        for cb in tuple(self.subs[path].callbacks):
            cb(payload)


def _mount(widget_slot):
    sec = type("MSec", (Row,), {"w": widget_slot})
    page = type("MPage", (Column,), {"sec": sec.slot()})
    app = type("MApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _heard(ref, browser_sends: list[dict]) -> tuple[list, list]:
    """Bind ``on_input()`` and ``on_change()``, fire what the browser sends, return
    (what both heard in order, what the tab was asked to watch)."""
    tab = _Tab()
    heard: list[tuple[str, object]] = []

    async def run():
        ctx = Context().bind(Session, tab)
        moving, _ = await nu.arun(ref.on_input(), ctx)
        committed, _ = await nu.arun(ref.on_change(), ctx)
        moving.bind(lambda p: heard.append(("on_input", p["value"])))
        committed.bind(lambda p: heard.append(("on_change", p["value"])))
        for payload in browser_sends:
            tab.notify(("page", "sec", "w"), payload)

    asyncio.run(run())
    return heard, tab.asked


def test_a_typed_value_is_heard_moving_then_committed():
    ref = _mount(InputRef.slot())
    heard, asked = _heard(
        ref,
        [
            {"event": "input", "value": "D"},
            {"event": "input", "value": "Du"},
            {"event": "input", "value": "Dune"},
            {"event": "change", "value": "Dune"},
        ],
    )
    assert heard == [
        ("on_input", "D"),
        ("on_input", "Du"),
        ("on_input", "Dune"),
        ("on_change", "Dune"),
    ]
    assert asked == [(("page", "sec", "w"), INPUT), (("page", "sec", "w"), CHANGE)]


def test_a_slider_drag_is_heard_per_tick_then_on_release():
    ref = _mount(SliderRef.slot(value=10))
    ticks = [{"event": "input", "value": v} for v in (11, 12, 13)]
    heard, _ = _heard(ref, [*ticks, {"event": "change", "value": 13}])
    assert heard == [("on_input", 11), ("on_input", 12), ("on_input", 13), ("on_change", 13)]


def test_on_input_hears_no_change_and_on_change_no_input():
    ref = _mount(RangeSliderRef.slot())
    heard, _ = _heard(
        ref,
        [
            {"event": "change", "value": [1, 2]},
            {"event": "input", "value": [1, 3]},
            {"event": "submit", "value": [1, 3]},
        ],
    )
    assert heard == [("on_change", [1, 2]), ("on_input", [1, 3])]


@pytest.mark.parametrize("cls", MOVING, ids=lambda c: c.__name__)
def test_the_moving_inputs_take_on_input(cls):
    assert issubclass(cls, Moves)
    assert issubclass(cls, Readable)
    assert isinstance(_mount(cls.slot()).on_input(), Changed)


@pytest.mark.parametrize("cls", DISCRETE, ids=lambda c: c.__name__)
def test_the_discrete_inputs_have_no_on_input(cls):
    assert not issubclass(cls, Moves)
    assert not hasattr(_mount(cls.slot()), "on_input")


def test_sketch_reads_through_readable_with_its_own_lift():
    # The board's main read is Readable's; only the lift is its own.
    assert "_acompile" not in vars(SketchRef)
    assert "_lift" in vars(SketchRef)
