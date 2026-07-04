"""Structural + wire tests for nudle Refs — no browser required.

nudle renders in a browser, but its Ref layer is browser-independent and IS
testable here:

- navigation (``section.field`` via ``__getattr__`` -> ``Slot.create_ref``) is
  pure structure;
- ``with_children`` survival (metadata riding a tree rewrite) is pure structure;
- wire-path resolution + frame emission run through ``nu.arun`` against a *fake*
  ``NudleSession`` that just records the ``Frame`` it is handed — no websocket,
  no browser.

Only the browser-side rendering is out of reach, and the Ref layer never touches
it. This file is the harness that lets the nudle payload migration be verified.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nu.nudle.page import Page
from nu.nudle.refs.row import Row
from nu.nudle.refs.section import SectionRef
from nu.nudle.refs.text import TextRef
from nu.nudle.session import NudleSession


class Panel(Row):
    label = TextRef.slot()
    title = TextRef.slot()


class HomePage(Page):
    panel = Panel.slot()


class _RecordingSession:
    """Fake NudleSession: records frames instead of sending over a websocket."""

    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


# --- navigation -------------------------------------------------------------


def test_section_navigation_returns_child_ref():
    ref = SectionRef("panel", section_cls=Panel, owner_shape=Panel)
    child = ref.label
    assert isinstance(child, TextRef)
    assert child._parent is ref


def test_section_navigation_unknown_slot_raises():
    ref = SectionRef("panel", section_cls=Panel, owner_shape=Panel)
    with pytest.raises(AttributeError):
        _ = ref.nope


# --- with_children survival (the migration's risk point) --------------------


def test_with_children_preserves_section_state():
    ref = SectionRef("panel", section_cls=Panel, owner_shape=Panel)
    variant = ref.with_children(*ref.children)
    assert type(variant) is SectionRef
    assert variant._segment == ref._segment
    assert variant._section_cls is Panel
    assert variant._owner_shape is Panel


def test_with_children_preserves_leaf_segment():
    child = SectionRef("panel", section_cls=Panel, owner_shape=Panel).label
    variant = child.with_children(*child.children)
    assert type(variant) is TextRef
    assert variant._segment == child._segment


# --- wire path resolution + frame emission (through a fake session) ---------


def test_store_emits_frame_with_wire_path():
    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(HomePage.panel.label.store("hi"), ctx))
    assert len(sess.frames) == 1
    assert sess.frames[0].ref == "HomePage.panel.label"
    assert sess.frames[0].payload == "hi"


def test_store_wire_path_reflects_sibling_slot():
    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(HomePage.panel.title.store("T"), ctx))
    assert sess.frames[0].ref == "HomePage.panel.title"


# --- nested sections + the Section-root / deep branches of _aresolve_address --


class Toolbar(Row):
    text = TextRef.slot()


class NestedPage(Page):
    panel = type("PanelWithToolbar", (Row,), {"toolbar": Toolbar.slot()}).slot()


def test_section_root_wire_path_from_server_handle():
    """`Toolbar.text` (a server-side handle rooted at a Section, not a Page)
    resolves via the Section-root branch using `_nudle_mount`."""
    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(Toolbar.text.store("x"), ctx))
    assert sess.frames[0].ref == "NestedPage.panel.toolbar.text"


def test_deep_nested_page_path():
    """Page -> section -> nested section -> widget resolves the full chain."""
    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(NestedPage.panel.toolbar.text.store("y"), ctx))
    assert sess.frames[0].ref == "NestedPage.panel.toolbar.text"


# --- input read path (tab -> server): _aread -> _aresolve_address + _lift ----


def test_input_read_resolves_path_and_reads_session():
    """Input Refs read the live browser value: `_aread` resolves the wire path
    and calls `session.aread(path)`. Covers the read direction + `_lift`."""
    from nu.nudle.refs.input import InputRef

    class Form(Row):
        name = InputRef.slot()

    class FormPage(Page):
        form = Form.slot()

    class ReadSession(_RecordingSession):
        def __init__(self) -> None:
            super().__init__()
            self.reads: list[str] = []

        async def aread(self, path: str) -> object:
            self.reads.append(path)
            return "browser-value"

    sess = ReadSession()
    ctx = Context().bind(NudleSession, sess)
    result = asyncio.run(nu.arun(FormPage.form.name, ctx))
    assert sess.reads == ["FormPage.form.name"]
    assert result[0] == "browser-value"


# --- widget interaction sweep (auto-covers every leaf widget) ----------------


def _leaf_widgets(*, needs_changed: bool = False):
    """(ref_cls, module_name) for every NudleRef leaf widget with store()
    (optionally: only those exposing changed())."""
    import importlib
    import inspect
    import os

    from nu.nudle.refs.base import NudleRef
    from nu.nudle.refs.section import SectionRef

    root = os.path.dirname(importlib.import_module("nu.nudle.refs").__file__)
    out = []
    for fname in sorted(os.listdir(root)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        mod = importlib.import_module("nu.nudle.refs." + fname[:-3])
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if (
                issubclass(cls, NudleRef)
                and not issubclass(cls, SectionRef)  # SectionRef-backed = container, not a leaf
                and cls.__module__ == mod.__name__
                and not name.startswith("_")
                and callable(getattr(cls, "store", None))
                and (not needs_changed or callable(getattr(cls, "changed", None)))
            ):
                out.append((cls, fname[:-3]))
    return out


_STORE_WIDGETS = _leaf_widgets()
_CHANGED_WIDGETS = _leaf_widgets(needs_changed=True)


def _mount(widget_cls):
    """A fresh Page with `widget_cls` at `.sec.w`; returns the widget handle."""
    sec = type("WSec", (Row,), {"w": widget_cls.slot()})
    page = type("WPage", (Page,), {"sec": sec.slot()})
    return page.sec.w


@pytest.mark.parametrize("widget_cls,mod", _STORE_WIDGETS, ids=[m for _, m in _STORE_WIDGETS])
def test_widget_store_emits_write_frame(widget_cls, mod):
    # Widgets differ in payload shape (bare value vs a props dict), but every
    # one must resolve the same wire path and emit exactly one write frame —
    # that is the ref-layer contract this sweep pins.
    handle = _mount(widget_cls)
    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(handle.store("v"), ctx))
    assert len(sess.frames) == 1
    assert sess.frames[0].ref == "WPage.sec.w"
    assert sess.frames[0].op == "write"


@pytest.mark.parametrize("widget_cls,mod", _CHANGED_WIDGETS, ids=[m for _, m in _CHANGED_WIDGETS])
def test_input_widget_changed_returns_subscription(widget_cls, mod):
    from nu.nudle.interactions.changed import Changed

    handle = _mount(widget_cls)
    assert isinstance(handle.changed(), Changed)


def test_widget_sweep_is_non_empty():
    # guard: if discovery silently returns nothing, the parametrized tests
    # would vacuously pass — pin that we actually cover a fleet of widgets.
    assert len(_STORE_WIDGETS) >= 25
    assert len(_CHANGED_WIDGETS) >= 8


# --- section-level chrome ops: tabs, card (mount-ref pattern) ----------------


def test_tabs_store_active_emits_frame():
    from nu.nudle.refs.tabs import TabsRef

    class MyTabs(TabsRef):
        pass

    class TabPage(Page):
        tabs = MyTabs.slot()

    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(MyTabs.store_active("t1"), ctx))
    assert sess.frames[0].ref == "TabPage.tabs"
    assert sess.frames[0].op == "store_active"
    assert sess.frames[0].payload == "t1"


def test_card_store_title_emits_frame():
    """Card chrome store now works (was a pre-existing bug: `_StoreSectionStr`
    held no Ref; fixed by the `_CardMountRef` mount-ref pattern like tabs)."""
    from nu.nudle.refs.card import CardRef

    class MyCard(CardRef):
        pass

    class CardPage(Page):
        card = MyCard.slot()

    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(MyCard.store_title("hello"), ctx))
    assert sess.frames[0].ref == "CardPage.card"
    assert sess.frames[0].op == "store_title"
    assert sess.frames[0].payload == "hello"


def test_table_append_emits_frame():
    from nu.nudle.refs.table import TableRef

    class TSec(Row):
        t = TableRef.slot()

    class TablePage(Page):
        sec = TSec.slot()

    sess = _RecordingSession()
    ctx = Context().bind(NudleSession, sess)
    asyncio.run(nu.arun(TablePage.sec.t.append(["a", "b"]), ctx))
    assert sess.frames[0].ref == "TablePage.sec.t"
