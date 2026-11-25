"""Chrome reads and events: Tabs, Modal, Sheet, Popover, Collapsible, Accordion.

Each holds state the person changes in the tab (the active tab, open or
closed, the open sections), so each is ``Changes``: reading the Ref reads
that state back in one round trip, and ``on_change()`` hears it move as
``{event: "change", value}``, the value being what the read returns.

Runs over a fake session that answers reads and records subscriptions.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context, Shape
from nu.lang.literal import Literal
from nu.lang.null import NULL
from nustd.ui import Column, Session
from nustd.ui.core import CHANGE, Changes
from nustd.ui.refs import (
    AccordionRef,
    CollapsibleRef,
    ModalRef,
    PopoverRef,
    SheetRef,
    TabsRef,
)


_OPEN_REFS = (ModalRef, SheetRef, PopoverRef, CollapsibleRef)
_ALL = (TabsRef, AccordionRef, *_OPEN_REFS)


class _Tab:
    """Fake session: answers every main read with ``answer``, records what was asked."""

    def __init__(self, answer: object = None) -> None:
        self.answer = answer
        self.reads: list[tuple[tuple[str, ...], str | None]] = []
        self.subscribed: list[tuple[tuple[str, ...], str | None]] = []

    async def send(self, frame: object) -> None:
        pass

    async def aread(self, path: tuple[str, ...], field: str | None = None) -> object:
        self.reads.append((path, field))
        return self.answer

    def subscribe(self, path: tuple[str, ...], event: str | None = None) -> _Sub:
        self.subscribed.append((path, event))
        return _Sub()


class _Sub:
    def bind(self, cb):
        pass

    def unbind(self, cb):
        pass

    def close(self):
        pass


def _mount(slot):
    page = type("RPage", (Column,), {"box": slot})
    app = type("RApp", (Shape,), {"page": page.slot()})
    return app.page.box


def _run(term, tab: _Tab) -> object:
    value, _ = asyncio.run(nu.arun(term, Context().bind(Session, tab)))
    return value


@pytest.mark.parametrize("cls", _ALL)
def test_each_is_changes(cls):
    assert issubclass(cls, Changes)


@pytest.mark.parametrize("cls", _ALL)
def test_on_change_hears_change_only(cls):
    term = cls("x").on_change()
    event = term._children[1]
    assert isinstance(event, Literal)
    assert event.value == CHANGE


@pytest.mark.parametrize("cls", _ALL)
def test_on_change_subscribes_with_its_event(cls):
    ref = _mount(cls.slot())
    tab = _Tab()
    _run(ref.on_change(), tab)
    _run(ref.on_event(), tab)
    assert tab.subscribed == [(("page", "box"), CHANGE), (("page", "box"), None)]


def test_tabs_reads_the_active_id():
    ref = _mount(TabsRef.slot(tabs=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}]))
    tab = _Tab("b")
    assert _run(ref, tab) == "b"
    assert tab.reads == [(("page", "box"), None)]


def test_tabs_with_no_tab_reads_null():
    assert _run(_mount(TabsRef.slot()), _Tab(None)) is NULL


def test_tabs_read_feeds_a_program():
    ref = _mount(TabsRef.slot(tabs=[{"id": "a", "label": "A"}]))
    assert _run(nu.let(ref, lambda active: active == "a"), _Tab("a")) is True


@pytest.mark.parametrize("cls", _OPEN_REFS)
@pytest.mark.parametrize(("raw", "want"), [(True, True), (False, False), (None, False)])
def test_open_refs_read_a_bool(cls, raw, want):
    assert _run(_mount(cls.slot()), _Tab(raw)) is want


def test_accordion_reads_the_open_ids():
    sections = [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}]
    ref = _mount(AccordionRef.slot(sections=sections))
    assert _run(ref, _Tab(["a", "b"])) == ["a", "b"]
    assert _run(ref, _Tab(None)) == []


@pytest.mark.parametrize("cls", _OPEN_REFS)
def test_set_open_on_every_open_ref(cls):
    assert callable(cls("x").set_open)


def test_tabs_and_accordion_slots_still_name_their_children():
    """``on_event`` is the one public name ``Changes`` adds; slots still reach the bodies."""
    from nustd.ui import Accordion, Tabs, TextRef

    class Views(Tabs):
        overview = TextRef.slot()
        changes = TextRef.slot()

    class Faq(Accordion):
        pricing = TextRef.slot()
        change = TextRef.slot()

    views = _mount(Views.slot())
    faq = _mount(Faq.slot())
    assert views.overview._segment == "overview"
    assert views.changes._segment == "changes"
    assert faq.change._segment == "change"
    tab = _Tab("overview")
    assert _run(views, tab) == "overview"
    assert tab.reads == [(("page", "box"), None)]
