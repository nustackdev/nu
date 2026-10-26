"""HistoryRef and the query encoding, and the href / target every link takes.

Wire only, through a fake session, no browser. The query fixtures are the
ones the kit's TS test reads too (tests/fixtures/query.json), so both sides
spell a query the same way.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

import nu
from nu import Context
from nustd.ui import (
    BreadcrumbRef,
    HistoryRef,
    NavItemRef,
    NavRef,
    PageLinkRef,
    Session,
    decode_query,
    encode_query,
)
from nustd.ui.core import Changed
from nustd.ui.nudle import Index, Page
from nustd.ui.refs import EmptyStateRef, Row


FIXTURES = json.loads((Path(__file__).parents[2] / "fixtures" / "query.json").read_text())


class _Session:
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


class App(Index):
    nav = HistoryRef.slot()
    home = type("HomePage", (Page,), {}).slot("/")


def _run(term, sess: _Session | None = None):
    sess = sess or _Session()
    out, _ = asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return out, sess


def _payloads(term) -> list:
    _, sess = _run(term)
    return [f.payload for f in sess.frames]


ENTRY = {
    "uri": "/feed?q=a+b&page=2#top",
    "path": "/feed",
    "query": {"q": "a b", "page": "2"},
    "hash": "#top",
    "state": {"panes": [{"plane": "feed"}]},
}


# --- the name ----------------------------------------------------------------


def test_navref_is_the_old_name_of_historyref():
    assert NavRef is HistoryRef
    assert HistoryRef._wire_type == "HistoryRef"
    [frame] = _run(App.nav.push("/a"))[1].frames
    assert frame.chain[-1][1] == "HistoryRef"


# --- moves -------------------------------------------------------------------


def test_push_and_replace_carry_state_only_when_given():
    assert _payloads(App.nav.push("/feed")) == [{"action": "push", "uri": "/feed"}]
    assert _payloads(App.nav.push("/feed", state={"k": [1, None]})) == [
        {"action": "push", "uri": "/feed", "state": {"k": [1, None]}}
    ]
    assert _payloads(App.nav.replace("/x")) == [{"action": "replace", "uri": "/x"}]
    assert _payloads(App.nav.replace("/x", state=None)) == [
        {"action": "replace", "uri": "/x", "state": None}
    ]


def test_set_is_push():
    assert _payloads(App.nav.set("/feed")) == _payloads(App.nav.push("/feed"))


def test_back_and_forward():
    assert _payloads(App.nav.back() >> App.nav.forward()) == [
        {"action": "back"},
        {"action": "forward"},
    ]


def test_set_query_merges_in_the_browser_with_none_dropping():
    assert _payloads(App.nav.set_query(q="new", page=None)) == [
        {"action": "set_query", "query": {"q": "new", "page": None}}
    ]
    assert _payloads(App.nav.set_query({"sort-by": "date"}, limit=10)) == [
        {"action": "set_query", "query": {"sort-by": "date", "limit": 10}}
    ]


# --- reads -------------------------------------------------------------------


def test_reading_the_ref_is_the_uri():
    out, sess = _run(App.nav, _Session(ENTRY))
    assert out == "/feed?q=a+b&page=2#top"
    assert sess.reads == [("nav",)]


def test_entry_query_state_and_path():
    assert _run(App.nav.entry(), _Session(ENTRY))[0] == ENTRY
    assert _run(App.nav.query(), _Session(ENTRY))[0] == {"q": "a b", "page": "2"}
    assert _run(App.nav.state(), _Session(ENTRY))[0] == {"panes": [{"plane": "feed"}]}
    out, sess = _run(App.nav.path(), _Session(ENTRY))
    assert out == "/feed"
    # One round trip each: the ref child is never read on its own.
    assert sess.reads == [("nav",)]


def test_a_bare_uri_from_an_older_kit_still_reads():
    old = _Session("/feed?q=a+b#top")
    assert _run(App.nav, old)[0] == "/feed?q=a+b#top"
    assert _run(App.nav.entry(), _Session("/feed?q=a+b#top"))[0] == {
        "uri": "/feed?q=a+b#top",
        "path": "/feed",
        "query": {"q": "a b"},
        "hash": "#top",
        "state": None,
    }


def test_on_change_subscribes():
    assert isinstance(App.nav.on_change(), Changed)


def test_docstring_names_no_aread():
    assert "aread" not in (HistoryRef.__doc__ or "")


# --- query encoding: the shared fixtures --------------------------------------


@pytest.mark.parametrize("case", FIXTURES["encode"], ids=lambda c: c["string"] or "empty")
def test_encode_matches_the_kit(case):
    assert encode_query(case["query"]) == case["string"]


@pytest.mark.parametrize("case", FIXTURES["decode"], ids=lambda c: c["string"] or "empty")
def test_decode_matches_the_kit(case):
    assert decode_query(case["string"]) == case["query"]


def test_encode_spells_floats_as_js_does_when_whole():
    assert encode_query(a=2.0, b=1.5, c=-0.25) == "a=2&b=1.5&c=-0.25"
    assert encode_query(id=42, q="a b") == "id=42&q=a+b"


# --- link parity: href, target, set_href ---------------------------------------


def _mount(slot):
    sec = type("LSec", (Row,), {"w": slot})
    page = type("LPage", (Page,), {"sec": sec.slot()})
    app = type("LApp", (Index,), {"page": page.slot("/")})
    return app.page.sec.w


def test_nav_item_takes_a_target_and_set_href():
    assert NavItemRef.slot(href="/d", target="_blank").props["target"] == "_blank"
    assert NavItemRef.slot().props["target"] == "_self"
    item = _mount(NavItemRef.slot())
    assert _payloads(item.set_href("/docs")) == [{"href": "/docs"}]
    assert _payloads(item.set_href("https://x.dev", target="_blank")) == [
        {"href": "https://x.dev", "target": "_blank"}
    ]


def test_page_link_set_takes_a_target():
    link = _mount(PageLinkRef.slot())
    assert _payloads(link.set(href="/a", target="_blank")) == [{"href": "/a", "target": "_blank"}]
    assert _payloads(link.set(title="A")) == [{"title": "A"}]


def test_breadcrumb_carries_a_target_per_crumb():
    props = BreadcrumbRef.slot(
        items=[
            {"label": "Home", "href": "/"},
            {"label": "Spec", "href": "https://x", "target": "_blank"},
        ]
    ).props
    assert props["items"] == [
        {"label": "Home", "href": "/"},
        {"label": "Spec", "href": "https://x", "target": "_blank"},
    ]


def test_empty_state_action_target():
    empty = _mount(EmptyStateRef.slot())
    assert _payloads(empty.set_action("Open", href="/x", target="_blank")) == [
        {"action": "Open", "action_href": "/x", "action_target": "_blank"}
    ]
