"""Input leaves: icon and tooltip on a button, the toolbar toggle, the
searchable select, the sketch pad. Wire only, through a fake session, no
browser."""

from __future__ import annotations

import asyncio

import nu
from nu import Context, Shape
from nustd.ui import Column, Session
from nustd.ui.core import Changed
from nustd.ui.refs import ButtonRef, Row, SelectRef, SketchRef, TextRef, ToggleRef


class _RecordingSession:
    """Fake WsSession: records frames, answers reads with a fixed value."""

    def __init__(self, value: object = None) -> None:
        self.frames: list = []
        self.reads: list[tuple[str, ...]] = []
        self.value = value

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...]) -> object:
        self.reads.append(path)
        return self.value


def _mount(widget_slot):
    """A fresh Shape -> Column with `widget_slot` at `.page.sec.w`; returns the handle."""
    sec = type("WSec", (Row,), {"w": widget_slot})
    page = type("WPage", (Column,), {"sec": sec.slot()})
    app = type("WApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _frames(term, sess: _RecordingSession | None = None):
    sess = sess or _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _seeded(frame) -> tuple:
    """The (wire type, props) a write frame seeds its node with."""
    return frame.chain[-1][1:]


# --- ButtonRef: icon and tooltip ---------------------------------------------


def test_button_slot_defaults_carry_empty_icon_and_tooltip():
    assert ButtonRef.slot().props == {
        "label": "",
        "variant": "primary",
        "disabled": False,
        "icon": "",
        "tooltip": "",
        "size": "md",
        "href": "",
        "target": "_self",
    }


def test_button_icon_only_slot():
    props = ButtonRef.slot(icon="refresh-cw", tooltip="Reload", variant="ghost").props
    assert props["label"] == ""
    assert props["icon"] == "refresh-cw"
    assert props["tooltip"] == "Reload"


def test_button_seeds_its_icon_and_tooltip_on_the_wire():
    handle = _mount(ButtonRef.slot(icon="plus", tooltip="Add"))
    [frame] = _frames(handle.set_label("Add"))
    assert _seeded(frame) == (
        "ButtonRef",
        {
            "label": "",
            "variant": "primary",
            "disabled": False,
            "icon": "plus",
            "tooltip": "Add",
            "size": "md",
            "href": "",
            "target": "_self",
        },
    )


def test_button_set_icon_and_tooltip_merge_one_key():
    handle = _mount(ButtonRef.slot())
    assert _frames(handle.set_icon("trash-2"))[0].payload == {"icon": "trash-2"}
    assert _frames(handle.set_tooltip("Delete"))[0].payload == {"tooltip": "Delete"}


def test_button_set_takes_icon_and_tooltip():
    handle = _mount(ButtonRef.slot())
    [frame] = _frames(handle.set("", icon="x", tooltip="Close"))
    assert frame.payload == {"label": "", "icon": "x", "tooltip": "Close"}


def test_button_existing_payloads_unchanged():
    handle = _mount(ButtonRef.slot())
    assert _frames(handle.set("Go"))[0].payload == {"label": "Go"}
    assert _frames(handle.set("Go", variant="danger", disabled=True))[0].payload == {
        "label": "Go",
        "variant": "danger",
        "disabled": True,
    }
    assert _frames(handle.set_label("Stop"))[0].payload == {"label": "Stop"}
    assert _frames(handle.set_variant("ghost"))[0].payload == {"variant": "ghost"}
    assert _frames(handle.set_disabled(False))[0].payload == {"disabled": False}
    assert isinstance(handle.on_click(), Changed)


# --- ToggleRef -----------------------------------------------------------------


def test_toggle_wire_type_and_slot_defaults():
    assert ToggleRef._wire_type == "ToggleRef"
    assert ToggleRef.slot().props == {"label": "", "icon": "", "pressed": False}
    assert ToggleRef.slot(icon="bold", pressed=1).props["pressed"] is True


def test_toggle_set_writes_the_bare_pressed_state():
    handle = _mount(ToggleRef.slot(icon="text-wrap"))
    [frame] = _frames(handle.set(True))
    assert frame.ref == ("page", "sec", "w")
    assert frame.op == "write"
    assert frame.payload is True
    assert _seeded(frame) == ("ToggleRef", {"label": "", "icon": "text-wrap", "pressed": False})


def test_toggle_chrome_setters_merge_one_key():
    handle = _mount(ToggleRef.slot())
    assert _frames(handle.set_label("Wrap"))[0].payload == {"label": "Wrap"}
    assert _frames(handle.set_icon("pin"))[0].payload == {"icon": "pin"}


def test_toggle_reads_the_live_pressed_state():
    handle = _mount(ToggleRef.slot(label="Pin"))
    sess = _RecordingSession(value=True)
    result = asyncio.run(nu.arun(handle, Context().bind(Session, sess)))
    assert sess.reads == [("page", "sec", "w")]
    assert result[0] is True


def test_toggle_on_change_returns_a_subscription():
    assert isinstance(_mount(ToggleRef.slot()).on_change(), Changed)


# --- SelectRef: searchable ----------------------------------------------------


def test_select_searchable_defaults_off():
    props = SelectRef.slot(options=["a", "b"]).props
    assert props["searchable"] is False
    assert props["options"] == [{"value": "a", "label": "a"}, {"value": "b", "label": "b"}]


def test_select_searchable_seeds_and_flips():
    handle = _mount(SelectRef.slot(options=["a"], searchable=True))
    [frame] = _frames(handle.set_searchable(False))
    assert frame.payload == {"searchable": False}
    assert _seeded(frame)[1]["searchable"] is True


def test_select_value_contract_unchanged_when_searchable():
    handle = _mount(SelectRef.slot(options=["a", "b"], searchable=True))
    assert _frames(handle.set("b"))[0].payload == "b"
    sess = _RecordingSession(value="a")
    result = asyncio.run(nu.arun(handle, Context().bind(Session, sess)))
    assert result[0] == "a"


# --- SketchRef -----------------------------------------------------------------

_ELEMENTS = [
    {"type": "path", "points": [[0.1, 0.2], [0.3, 0.4, 0.6]], "stroke": "ink", "width": 0.012},
    {
        "type": "rect",
        "x": 0.1,
        "y": 0.1,
        "w": 0.3,
        "h": 0.2,
        "stroke": "red",
        "fill": "red-soft",
        "width": 0.006,
    },
    {"type": "arrow", "points": [[0.2, 0.8], [0.7, 0.5]], "stroke": "#e11d48", "width": 0.024},
]


def test_sketch_wire_type_and_slot_defaults():
    assert SketchRef._wire_type == "SketchRef"
    assert SketchRef.slot().props == {
        "width": 280,
        "height": None,
        "tools": ["pen", "rect", "ellipse", "line", "arrow"],
        "controls": ["tools", "stroke", "fill", "size", "undo", "redo", "clear"],
        "defaults": {},
        "readonly": False,
        "label": "",
        "value": [],
    }


def test_sketch_mnist_config():
    props = SketchRef.slot(tools=["pen"], controls=["clear"], defaults={"size": 0.07}).props
    assert props["tools"] == ["pen"]
    assert props["controls"] == ["clear"]
    assert props["defaults"] == {"size": 0.07}


def test_sketch_config_keeps_toolbar_order_and_empty_controls():
    props = SketchRef.slot(tools=["arrow", "pen"], controls=[], width=480.0, height=270).props
    assert props["tools"] == ["pen", "arrow"]
    assert props["controls"] == []
    assert (props["width"], props["height"]) == (480, 270)


def test_sketch_config_refuses_unknown_names():
    for bad in (
        {"tools": ["brush"]},
        {"tools": []},
        {"controls": ["zoom"]},
        {"defaults": {"colour": "red"}},
        {"defaults": {"tool": "rect"}, "tools": ["pen"]},
        {"defaults": {"size": 0}},
    ):
        try:
            SketchRef.slot(**bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")


def test_sketch_slot_normalizes_seed_elements():
    seed = [
        [(0.1, 0.2), (2, -1)],
        {"type": "rect", "x": 0.5, "y": 0.5, "w": -0.2, "h": 0.9, "stroke": " blue ", "width": "x"},
        {"type": "line", "points": [[0, 0]]},
        {"type": "blob"},
        "junk",
        {"type": "ellipse", "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2, "fill": "none"},
    ]
    assert SketchRef.slot(value=seed).props["value"] == [
        {"type": "path", "points": [[0.1, 0.2], [1.0, 0.0]]},
        {"type": "rect", "x": 0.3, "y": 0.5, "w": 0.2, "h": 0.5, "stroke": "blue"},
        {"type": "ellipse", "x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2, "fill": "none"},
    ]


def test_sketch_standalone_carries_slot_props():
    pad = SketchRef("pad", props={"width": 140, "controls": []})
    assert pad._payload["props"]["width"] == 140
    assert pad._payload["props"]["controls"] == []
    assert pad._payload["props"]["value"] == []


def test_sketch_set_writes_the_elements():
    handle = _mount(SketchRef.slot(label="Board"))
    [frame] = _frames(handle.set(_ELEMENTS))
    assert frame.ref == ("page", "sec", "w")
    assert frame.op == "write"
    assert frame.payload == _ELEMENTS
    assert _seeded(frame)[0] == "SketchRef"
    assert _seeded(frame)[1]["label"] == "Board"


def test_sketch_set_empty_and_clear_both_wipe():
    handle = _mount(SketchRef.slot())
    assert _frames(handle.set([]))[0].payload == []
    assert _frames(handle.clear())[0].payload == []


def test_sketch_set_keeps_pressure_on_paths_only():
    handle = _mount(SketchRef.slot())
    [frame] = _frames(
        handle.set([{"type": "line", "points": [(0, 0, 0.5), (1.5, 1, 0.5)]}, [(0.5, 0.5, 2)]])
    )
    assert frame.payload == [
        {"type": "line", "points": [[0.0, 0.0], [1.0, 1.0]]},
        {"type": "path", "points": [[0.5, 0.5, 1.0]]},
    ]


def test_sketch_chrome_setters_merge_one_key():
    handle = _mount(SketchRef.slot())
    assert _frames(handle.set_label("Draw a digit"))[0].payload == {"label": "Draw a digit"}
    assert _frames(handle.set_readonly(True))[0].payload == {"readonly": True}


def test_sketch_reads_the_live_elements():
    handle = _mount(SketchRef.slot())
    sess = _RecordingSession(value=_ELEMENTS)
    result = asyncio.run(nu.arun(handle, Context().bind(Session, sess)))
    assert sess.reads == [("page", "sec", "w")]
    assert result[0] == _ELEMENTS


def test_sketch_read_of_nothing_is_a_blank_board():
    handle = _mount(SketchRef.slot())
    result = asyncio.run(nu.arun(handle, Context().bind(Session, _RecordingSession(value=None))))
    assert result[0] == []


class _Notifies:
    def __init__(self) -> None:
        self.callbacks: list = []

    def bind(self, cb):
        self.callbacks.append(cb)

    def unbind(self, cb):
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self):
        self.callbacks = []


class _Tab(_RecordingSession):
    """A tab that also takes subscriptions, so a test can fire its notifies."""

    def __init__(self, value: object = None) -> None:
        super().__init__(value)
        self.subs: dict = {}

    def subscribe(self, path):
        return self.subs.setdefault(path, _Notifies())

    def notify(self, path):
        for cb in tuple(self.subs[path].callbacks):
            cb(None)


def test_sketch_on_change_reacts_to_an_element():
    """An element landing in the browser is one notify; the reaction reads the board back."""
    sec = type("PadSec", (Row,), {"pad": SketchRef.slot(), "count": TextRef.slot()})
    page = type("PadPage", (Column,), {"sec": sec.slot()})
    app = type("PadApp", (Shape,), {"page": page.slot()})
    pad, count = app.page.sec.pad, app.page.sec.count
    tab = _Tab(value=_ELEMENTS)

    async def run():
        react = nu.ReactForever(pad.on_change(), count.set(nu.str(nu.Len(pad))))
        task = asyncio.create_task(nu.arun(react, Context().bind(Session, tab)))
        path = ("page", "sec", "pad")
        for _ in range(100):
            if path in tab.subs and tab.subs[path].callbacks:
                break
            await asyncio.sleep(0.01)
        tab.notify(path)
        for _ in range(100):
            if tab.frames:
                break
            await asyncio.sleep(0.01)
        task.cancel()

    asyncio.run(run())
    assert ("page", "sec", "pad") in tab.reads
    assert [f.payload for f in tab.frames] == ["3"]
