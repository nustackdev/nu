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
