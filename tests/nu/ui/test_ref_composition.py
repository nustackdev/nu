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
from nu.ui import Session
from nu.ui.core import SectionRef
from nu.ui.nudle import Index, Page
from nu.ui.refs import Row, TextRef


class Panel(Row):
    label = TextRef.slot()
    title = TextRef.slot()


class HomePage(Page):
    panel = Panel.slot()


class HomeApp(Index):
    home = HomePage.slot("/")


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
    variant = ref._with_children(*ref._children)
    assert type(variant) is SectionRef
    assert variant._payload["segment"] == ref._payload["segment"]
    assert variant._payload["section_cls"] is Panel
    assert variant._owner_shape is Panel


def test_with_children_preserves_leaf_segment():
    child = SectionRef("panel", section_cls=Panel, owner_shape=Panel).label
    variant = child._with_children(*child._children)
    assert type(variant) is TextRef
    assert variant._payload["segment"] == child._payload["segment"]


# --- wire path resolution + frame emission (through a fake session) ---------


def test_set_emits_frame_with_wire_path():
    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(HomeApp.home.panel.label.set("hi"), ctx))
    assert len(sess.frames) == 1
    assert sess.frames[0].ref == ("home", "panel", "label")
    assert sess.frames[0].payload == "hi"


def test_set_wire_path_reflects_sibling_slot():
    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(HomeApp.home.panel.title.set("T"), ctx))
    assert sess.frames[0].ref == ("home", "panel", "title")


# --- nested sections: the address is the chain and only the chain -----------


class Toolbar(Row):
    text = TextRef.slot()


class NestedPage(Page):
    panel = type("PanelWithToolbar", (Row,), {"toolbar": Toolbar.slot()}).slot()


class NestedApp(Index):
    nested = NestedPage.slot("/")


def test_section_class_handle_resolves_bare():
    """A Section holds no mount point, so a handle taken off the class is the
    whole chain: one segment, wherever that section happens to be declared."""
    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(Toolbar.text.set("x"), ctx))
    assert sess.frames[0].ref == ("text",)


def test_one_section_mounts_under_many_parents():
    """The same Section subclass on two pages: each chain gives its own
    address, no class-level mount point to collide over."""

    class Shared(Row):
        text = TextRef.slot()

    class LeftPage(Page):
        panel = Shared.slot()

    class RightPage(Page):
        other = Shared.slot()

    class TwoApp(Index):
        left = LeftPage.slot("/")
        right = RightPage.slot("/right")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(TwoApp.left.panel.text.set("l"), ctx))
    asyncio.run(nu.arun(TwoApp.right.other.text.set("r"), ctx))
    assert sess.frames[0].ref == ("left", "panel", "text")
    assert sess.frames[1].ref == ("right", "other", "text")


def test_same_slot_name_on_two_pages_does_not_collide():
    """Two pages both declaring `panel`: the page slot in front keeps them
    apart, which is the whole reason a page contributes a segment."""

    class Left(Page):
        panel = Panel.slot()

    class Right(Page):
        panel = Panel.slot()

    class TwinApp(Index):
        left = Left.slot("/")
        right = Right.slot("/right")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(TwinApp.left.panel.label.set("l"), ctx))
    asyncio.run(nu.arun(TwinApp.right.panel.label.set("r"), ctx))
    assert sess.frames[0].ref == ("left", "panel", "label")
    assert sess.frames[1].ref == ("right", "panel", "label")


def test_page_class_handle_resolves_bare():
    """A Page is a Section with a route: no Index navigated to it, so there
    is no page segment to add. That is the single-page shorthand -- the
    address matches what `Page._mount_fields` emits for an auto-mount."""

    class Solo(Page):
        panel = Panel.slot()

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(Solo.panel.label.set("x"), ctx))
    assert sess.frames[0].ref == ("panel", "label")
    assert [f["path"] for f in Solo._mount_fields()] == [("panel",)]


def test_kv_slot_on_a_page_stays_a_kv_path():
    """A Page is not special to the shape DSL, so a kv slot declared on one
    resolves as a plain kv path -- no ui Ref wedged under it."""

    class Mixed(Page):
        label = TextRef.slot()
        count = nu.kv.IntRef.slot()

    ref = Mixed.count
    assert isinstance(ref, nu.kv.IntRef)
    assert ref._parent is None


def test_write_carries_the_annotated_chain():
    """The chain is the path plus what the browser needs to build it: one
    (segment, type, props) triple per level, root-first, page included."""

    class Fields(Row):
        label = TextRef.slot(value="hi")

    class ChainPage(Page):
        fields = Fields.slot()

    class ChainApp(Index):
        page = ChainPage.slot("/")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(ChainApp.page.fields.label.set("x"), ctx))
    chain = sess.frames[0].chain
    assert [(seg, typ) for seg, typ, _ in chain] == [
        ("page", "ChainPage"),
        ("fields", "Row"),
        ("label", "TextRef"),
    ]
    assert chain[0][2] == {}  # page slot declared no props
    assert chain[1][2]["gap"] == 4  # Row.slot() pins its chrome defaults
    assert chain[2][2] == {"value": "hi"}
    assert sess.frames[0].ref == tuple(seg for seg, _, _ in chain)


def test_append_carries_the_annotated_chain():
    from nu.ui.refs import TableRef

    class TSec2(Row):
        t = TableRef.slot()

    class TPage2(Page):
        sec = TSec2.slot()

    class TApp2(Index):
        table = TPage2.slot("/")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(TApp2.table.sec.t.append(["a", "b"]), ctx))
    assert [lvl[1] for lvl in sess.frames[0].chain] == ["TPage2", "Row", "TableRef"]


def test_deep_nested_page_path():
    """Page -> section -> nested section -> widget resolves the full chain."""
    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(NestedApp.nested.panel.toolbar.text.set("y"), ctx))
    assert sess.frames[0].ref == ("nested", "panel", "toolbar", "text")


# --- input read path (tab -> server): _aread -> _aresolve_address + _lift ----


def test_input_read_resolves_path_and_reads_session():
    """Input Refs read the live browser value: `_aread` resolves the wire path
    and calls `session.aread(path)`. Covers the read direction + `_lift`."""
    from nu.ui.refs import InputRef

    class Form(Row):
        name = InputRef.slot()

    class FormPage(Page):
        form = Form.slot()

    class FormApp(Index):
        form = FormPage.slot("/")

    class ReadSession(_RecordingSession):
        def __init__(self) -> None:
            super().__init__()
            self.reads: list[tuple[str, ...]] = []

        async def aread(self, path: tuple[str, ...]) -> object:
            self.reads.append(path)
            return "browser-value"

    sess = ReadSession()
    ctx = Context().bind(Session, sess)
    result = asyncio.run(nu.arun(FormApp.form.form.name, ctx))
    assert sess.reads == [("form", "form", "name")]
    assert result[0] == "browser-value"


def test_prose_round_trips_markdown_both_ways():
    """ProseRef is bidirectional: `set` ships the markdown source out as a bare
    string, and reading the handle pulls the browser's edited source back."""
    from nu.ui.refs import ProseRef

    class Doc(Row):
        body = ProseRef.slot(placeholder="Write something")

    class DocPage(Page):
        doc = Doc.slot()

    class DocApp(Index):
        doc = DocPage.slot("/")

    class ReadSession(_RecordingSession):
        async def aread(self, path: tuple[str, ...]) -> object:
            return "# edited\n\nby the browser\n"

    sess = ReadSession()
    ctx = Context().bind(Session, sess)

    asyncio.run(nu.arun(DocApp.doc.doc.body.set("# seeded\n"), ctx))
    assert sess.frames[0].ref == ("doc", "doc", "body")
    assert sess.frames[0].op == "write"
    assert sess.frames[0].payload == "# seeded\n"

    result = asyncio.run(nu.arun(DocApp.doc.doc.body, ctx))
    assert result[0] == "# edited\n\nby the browser\n"


def test_prose_partial_write_carries_a_dict():
    """The chrome setters use the map form, so a placeholder change does not
    also blow away the document."""
    from nu.ui.refs import ProseRef

    class Doc2(Row):
        body = ProseRef.slot()

    class DocPage2(Page):
        doc = Doc2.slot()

    class DocApp2(Index):
        doc = DocPage2.slot("/")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(DocApp2.doc.doc.body.set_read_only(True), ctx))
    assert sess.frames[0].payload == {"read_only": True}


# --- widget interaction sweep (auto-covers every leaf widget) ----------------


def _leaf_widgets(*, needs_changed: bool = False):
    """(ref_cls, module_name) for every Ref leaf widget with set()
    (optionally: only those exposing changed())."""
    import importlib
    import inspect
    from pathlib import Path

    from nu.ui.core import Ref, SectionRef

    root = Path(importlib.import_module("nu.ui.refs").__file__).parent
    out = []
    for entry in sorted(root.iterdir()):
        fname = entry.name
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        mod = importlib.import_module("nu.ui.refs." + fname[:-3])
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if (
                issubclass(cls, Ref)
                and not issubclass(cls, SectionRef)  # SectionRef-backed = container, not a leaf
                and cls.__module__ == mod.__name__
                and not name.startswith("_")
                and callable(getattr(cls, "set", None))
                and (not needs_changed or callable(getattr(cls, "changed", None)))
            ):
                out.append((cls, fname[:-3]))
    return out


_SET_WIDGETS = _leaf_widgets()
_CHANGED_WIDGETS = _leaf_widgets(needs_changed=True)


def _mount(widget_cls):
    """A fresh Index -> Page with `widget_cls` at `.page.sec.w`; returns the handle."""
    sec = type("WSec", (Row,), {"w": widget_cls.slot()})
    page = type("WPage", (Page,), {"sec": sec.slot()})
    app = type("WApp", (Index,), {"page": page.slot("/")})
    return app.page.sec.w


@pytest.mark.parametrize("widget_cls,mod", _SET_WIDGETS, ids=[m for _, m in _SET_WIDGETS])
def test_widget_set_emits_write_frame(widget_cls, mod):
    # Widgets differ in payload shape (bare value vs a props dict), but every
    # one must resolve the same wire path and emit exactly one write frame —
    # that is the ref-layer contract this sweep pins.
    handle = _mount(widget_cls)
    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(handle.set("v"), ctx))
    assert len(sess.frames) == 1
    assert sess.frames[0].ref == ("page", "sec", "w")
    assert sess.frames[0].op == "write"


@pytest.mark.parametrize("widget_cls,mod", _CHANGED_WIDGETS, ids=[m for _, m in _CHANGED_WIDGETS])
def test_input_widget_changed_returns_subscription(widget_cls, mod):
    from nu.ui.core import Changed

    handle = _mount(widget_cls)
    assert isinstance(handle.changed(), Changed)


def test_widget_sweep_is_non_empty():
    # guard: if discovery silently returns nothing, the parametrized tests
    # would vacuously pass — pin that we actually cover a fleet of widgets.
    assert len(_SET_WIDGETS) >= 25
    assert len(_CHANGED_WIDGETS) >= 8


# --- section-level chrome ops: tabs, card (mount-ref pattern) ----------------


def test_tabs_set_active_emits_frame():
    """Section chrome is driven off the bound Ref, so it addresses the
    section's own slot on the page that declares it."""
    from nu.ui.refs import Tabs

    class MyTabs(Tabs):
        pass

    class TabPage(Page):
        tabs = MyTabs.slot()

    class TabApp(Index):
        tab = TabPage.slot("/")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(TabApp.tab.tabs.set_active("t1"), ctx))
    assert sess.frames[0].ref == ("tab", "tabs")
    assert sess.frames[0].op == "set_active"
    assert sess.frames[0].payload == "t1"


def test_card_set_title_emits_frame():
    from nu.ui.refs import Card

    class MyCard(Card):
        pass

    class CardPage(Page):
        card = MyCard.slot()

    class CardApp(Index):
        card = CardPage.slot("/")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(CardApp.card.card.set_title("hello"), ctx))
    assert sess.frames[0].ref == ("card", "card")
    assert sess.frames[0].op == "set_title"
    assert sess.frames[0].payload == "hello"


def test_table_append_emits_frame():
    from nu.ui.refs import TableRef

    class TSec(Row):
        t = TableRef.slot()

    class TablePage(Page):
        sec = TSec.slot()

    class TableApp(Index):
        table = TablePage.slot("/")

    sess = _RecordingSession()
    ctx = Context().bind(Session, sess)
    asyncio.run(nu.arun(TableApp.table.sec.t.append(["a", "b"]), ctx))
    assert sess.frames[0].ref == ("table", "sec", "t")
