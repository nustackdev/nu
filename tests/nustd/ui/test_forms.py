"""The input contract and Form submit, on the wire through a fake session.

Every input seeds with ``value=``, sets with ``set``, takes the common props,
and names its notifies: ``on_change`` hears changes, ``on_submit`` submits,
``on_click`` clicks. A Form hears one submit with every value in it, reads
the same snapshot, and resets its inputs to their seeds.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nustd.ui import Column, Session
from nustd.ui.refs import (
    ButtonRef,
    CheckboxRef,
    CodeRef,
    DatePickerRef,
    Field,
    Form,
    FormRef,
    InputLeaf,
    InputRef,
    MarkdownRef,
    NumberInputRef,
    RadioGroupRef,
    Row,
    SelectRef,
    SketchRef,
    SliderRef,
    SwitchRef,
    TagInputRef,
    TextAreaRef,
    TextRef,
    ToggleRef,
)


class _Notifies:
    def __init__(self) -> None:
        self.callbacks: list = []

    def bind(self, cb):
        self.callbacks.append(cb)

    def unbind(self, cb):
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self):
        self.callbacks = []


class _Tab:
    """A fake tab: records frames, answers reads, takes subscriptions."""

    def __init__(self, value: object = None) -> None:
        self.frames: list = []
        self.reads: list[tuple[str, ...]] = []
        self.value = value
        self.subs: dict = {}

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...]) -> object:
        self.reads.append(path)
        return self.value

    def subscribe(self, path):
        return self.subs.setdefault(path, _Notifies())

    def notify(self, path, payload):
        for cb in tuple(self.subs[path].callbacks):
            cb(payload)


def _mount(widget_slot):
    sec = type("WSec", (Row,), {"w": widget_slot})
    page = type("WPage", (Column,), {"sec": sec.slot()})
    app = type("WApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _frames(term, tab: _Tab | None = None):
    tab = tab or _Tab()
    asyncio.run(nu.arun(term, Context().bind(Session, tab)))
    return tab.frames


def _react(sub, path, payloads, tab: _Tab, out) -> list:
    """Run ``ReactEvery(sub, out.set(...))``, fire ``payloads`` at ``path``, return the writes."""

    async def run():
        react = nu.ReactEvery(sub, out.set("heard"))
        task = asyncio.create_task(nu.arun(react, Context().bind(Session, tab)))
        for _ in range(200):
            if path in tab.subs and tab.subs[path].callbacks:
                break
            await asyncio.sleep(0.01)
        for p in payloads:
            tab.notify(path, p)
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(run())
    return [f for f in tab.frames if f.op == "write"]


COMMON = {"label", "disabled", "readonly", "required", "autofocus", "size"}

INPUTS = [
    CheckboxRef,
    DatePickerRef,
    InputRef,
    NumberInputRef,
    RadioGroupRef,
    SelectRef,
    SliderRef,
    SwitchRef,
    TagInputRef,
    TextAreaRef,
    ToggleRef,
]


@pytest.mark.parametrize("cls", INPUTS, ids=[c.__name__ for c in INPUTS])
def test_every_input_seeds_value_and_takes_the_common_props(cls):
    props = cls.slot().props
    assert "value" in props
    assert COMMON <= set(props)
    assert props["size"] == "md"
    assert issubclass(cls, InputLeaf)


@pytest.mark.parametrize(
    ("cls", "old"),
    [
        (CheckboxRef, "checked"),
        (SwitchRef, "default"),
        (ToggleRef, "pressed"),
        (SelectRef, "selected"),
        (RadioGroupRef, "selected"),
        (NumberInputRef, "default"),
        (DatePickerRef, "default"),
    ],
)
def test_the_old_seed_names_are_gone(cls, old):
    with pytest.raises(TypeError):
        cls.slot(**{old: None})


def test_set_value_is_gone_and_set_writes_the_bare_value():
    assert not hasattr(NumberInputRef, "set_value")
    assert not hasattr(SliderRef, "set_value")
    handle = _mount(NumberInputRef.slot())
    assert _frames(handle.set(4.0))[0].payload == 4.0


def test_textarea_select_and_radio_take_a_label():
    assert TextAreaRef.slot(label="Notes").props["label"] == "Notes"
    assert SelectRef.slot(label="Genre").props["label"] == "Genre"
    assert RadioGroupRef.slot(label="Mode").props["label"] == "Mode"


def test_common_setters_merge_one_key():
    handle = _mount(InputRef.slot())
    assert _frames(handle.set_label("Title"))[0].payload == {"label": "Title"}
    assert _frames(handle.set_placeholder("Type"))[0].payload == {"placeholder": "Type"}
    assert _frames(handle.set_disabled(True))[0].payload == {"disabled": True}
    assert _frames(handle.set_readonly(True))[0].payload == {"readonly": True}
    assert _frames(handle.set_required(True))[0].payload == {"required": True}


def test_reset_ships_a_reset_frame_with_the_chain():
    handle = _mount(InputRef.slot(value="seed"))
    [frame] = _frames(handle.reset())
    assert frame.op == "reset"
    assert frame.ref == ("page", "sec", "w")
    assert frame.chain[-1][1] == "InputRef"


def test_submit_inputs():
    for cls in (InputRef, NumberInputRef, DatePickerRef, TagInputRef, TextAreaRef, CodeRef):
        assert hasattr(cls, "on_submit"), cls.__name__
    for cls in (MarkdownRef, CheckboxRef, SwitchRef, SelectRef, SliderRef, SketchRef):
        assert not hasattr(cls, "on_submit"), cls.__name__


def test_textarea_submit_on_and_clear_on_submit():
    props = TextAreaRef.slot(submit_on="enter", clear_on_submit=True).props
    assert props["submit_on"] == "enter"
    assert props["clear_on_submit"] is True
    assert TextAreaRef.slot().props["submit_on"] == "mod+enter"


def _pair(widget):
    sec = type("PSec", (Row,), {"w": widget, "out": TextRef.slot()})
    page = type("PPage", (Column,), {"sec": sec.slot()})
    app = type("PApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w, app.page.sec.out


def test_on_change_hears_changes_only():
    w, out = _pair(InputRef.slot())
    writes = _react(
        w.on_change(),
        ("page", "sec", "w"),
        [{"event": "submit"}, {"event": "change"}, None],
        _Tab(),
        out,
    )
    assert len(writes) == 1


def test_on_submit_hears_submits_only():
    w, out = _pair(InputRef.slot())
    writes = _react(
        w.on_submit(),
        ("page", "sec", "w"),
        [{"event": "change"}, {"event": "submit"}, {"event": "submit"}],
        _Tab(),
        out,
    )
    assert len(writes) == 2


def test_on_click_hears_clicks():
    w, out = _pair(ButtonRef.slot(label="Go"))
    writes = _react(w.on_click(), ("page", "sec", "w"), [{"event": "click"}], _Tab(), out)
    assert len(writes) == 1


def test_button_submit_and_loading():
    props = ButtonRef.slot(label="Save", submit=True, loading=True).props
    assert props["submit"] is True
    assert props["loading"] is True
    handle = _mount(ButtonRef.slot())
    assert _frames(handle.set_loading(True))[0].payload == {"loading": True}


# --- Form --------------------------------------------------------------------


class TitleField(Field):
    input = InputRef.slot()


class AddForm(Form):
    title = TitleField.slot(label="Title")
    year = NumberInputRef.slot(value=2000)
    save = ButtonRef.slot(label="Save", submit=True)


def _app():
    page = type(
        "FPage", (Column,), {"add": AddForm.slot(clear_on_submit=True), "out": TextRef.slot()}
    )
    app = type("FApp", (Shape,), {"page": page.slot()})
    return app.page.add, app.page.out


def test_form_slot_props():
    props = FormRef.slot(clear_on_submit=True, busy_on_submit=True).props
    assert props["clear_on_submit"] is True
    assert props["busy_on_submit"] is True
    assert FormRef.slot().props["clear_on_submit"] is False


def test_form_on_submit_hands_the_payload_to_the_body():
    form, out = _app()
    tab = _Tab()

    async def run():
        react = nu.ReactEvery(form.on_submit(), lambda sub: out.set(sub["values"]["title"]))
        task = asyncio.create_task(nu.arun(react, Context().bind(Session, tab)))
        path = ("page", "add")
        for _ in range(200):
            if path in tab.subs and tab.subs[path].callbacks:
                break
            await asyncio.sleep(0.01)
        tab.notify(path, {"event": "change"})
        tab.notify(
            path,
            {"event": "submit", "values": {"title": "Dune", "year": 2021}, "button": "save"},
        )
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(run())
    writes = [f for f in tab.frames if f.op == "write"]
    assert [f.payload for f in writes] == [{"value": "Dune"}]
    assert tab.reads == []


def test_form_values_is_one_read_on_the_form():
    form, _ = _app()
    tab = _Tab(value={"title": "Dune", "year": 2021})
    result = asyncio.run(nu.arun(form.values()["title"], Context().bind(Session, tab)))
    assert tab.reads == [("page", "add")]
    assert result[0] == "Dune"


def test_form_reset_and_busy():
    form, _ = _app()
    [frame] = _frames(form.reset())
    assert frame.op == "reset"
    assert frame.ref == ("page", "add")
    assert _frames(form.set_busy(False))[0].payload == {"busy": False}


def test_form_reserves_its_method_names_for_slots():
    for name in ("on_submit", "values", "reset", "set_busy"):
        with pytest.raises((TypeError, ValueError)):
            type("Bad", (Form,), {name: InputRef.slot()})
