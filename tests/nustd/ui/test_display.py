"""Display leaves: Avatar, Breadcrumb, Skeleton, Spinner, StatusPill.

Each is a server-owned leaf: its slot seeds the props on the boot chain, a
setter sends a partial merge of just the keys it names, and nothing hangs
off it. Runs against a recording session, same harness as
test_ref_composition.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Index, Page, Row, Session
from nustd.ui.refs import (
    AvatarRef,
    BreadcrumbRef,
    LeafRef,
    SkeletonRef,
    SpinnerRef,
    StatusPillRef,
    TextRef,
)


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _mount(widget_cls, **props):
    """A fresh Index -> Page with `widget_cls` at `.page.sec.w`; returns the handle."""
    sec = type("DSec", (Row,), {"w": widget_cls.slot(**props)})
    page = type("DPage", (Page,), {"sec": sec.slot()})
    app = type("DApp", (Index,), {"page": page.slot("/")})
    return app.page.sec.w


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _write(term):
    [frame] = _frames(term)
    assert frame.op == "write"
    assert frame.ref == ("page", "sec", "w")
    return frame


DISPLAY = [AvatarRef, BreadcrumbRef, SkeletonRef, SpinnerRef, StatusPillRef]


@pytest.mark.parametrize("cls", DISPLAY, ids=lambda c: c.__name__)
def test_each_is_a_leaf_on_the_wire_under_its_own_name(cls):
    assert issubclass(cls, LeafRef)
    assert cls.__dict__["_wire_type"] == cls.__name__


@pytest.mark.parametrize("cls", DISPLAY, ids=lambda c: c.__name__)
def test_each_refuses_children(cls):
    with pytest.raises(TypeError, match=f"{cls.__name__} is a leaf"):
        TextRef("t", parent_ref=cls("d"))


@pytest.mark.parametrize(
    ("cls", "defaults"),
    [
        (AvatarRef, {"src": "", "name": "", "size": "md"}),
        (BreadcrumbRef, {"items": []}),
        (SkeletonRef, {"lines": 1, "shape": "text", "height": 0}),
        (SpinnerRef, {"size": "md", "label": ""}),
        (StatusPillRef, {"tone": "neutral", "label": ""}),
    ],
    ids=lambda v: v.__name__ if isinstance(v, type) else "",
)
def test_slot_defaults_seed_the_boot_chain(cls, defaults):
    assert cls.slot().props == defaults
    [frame] = _frames(_mount(cls).set_lines(2) if cls is SkeletonRef else _mount(cls).set("x"))
    assert frame.chain[-1][1:] == (cls.__name__, defaults)


def test_props_keyword_normalizes_through_slot():
    ref = AvatarRef("a", props={"name": "Ada Lovelace"})
    assert ref._payload["props"] == {"src": "", "name": "Ada Lovelace", "size": "md"}
    with pytest.raises(TypeError):
        AvatarRef("a", props={"shape": "square"})


# --- Avatar -------------------------------------------------------------------


def test_avatar_set_leads_with_src_and_merges():
    avatar = _mount(AvatarRef)
    assert _write(avatar.set("/me.png")).payload == {"src": "/me.png"}
    assert _write(avatar.set("/me.png", name="Ada", size="xl")).payload == {
        "src": "/me.png",
        "name": "Ada",
        "size": "xl",
    }
    assert _write(avatar.set_src("")).payload == {"src": ""}
    assert _write(avatar.set_name("Grace Hopper")).payload == {"name": "Grace Hopper"}
    assert _write(avatar.set_size("sm")).payload == {"size": "sm"}


def test_avatar_set_options_are_keyword_only():
    with pytest.raises(TypeError):
        AvatarRef("a").set("/me.png", "Ada")


# --- Breadcrumb ---------------------------------------------------------------


def test_breadcrumb_slot_takes_strings_and_dicts():
    crumbs = BreadcrumbRef.slot(items=["Home", {"label": "Docs", "href": "/docs"}, {"label": 3}])
    assert crumbs.props == {
        "items": [
            {"label": "Home", "href": ""},
            {"label": "Docs", "href": "/docs"},
            {"label": "3", "href": ""},
        ]
    }


def test_breadcrumb_drops_what_is_not_a_crumb():
    assert BreadcrumbRef.slot(items=["a", 7, None, {"href": "/b"}]).props == {
        "items": [{"label": "a", "href": ""}, {"label": "", "href": "/b"}]
    }


def test_breadcrumb_set_replaces_the_trail_normalized():
    trail = _mount(BreadcrumbRef)
    payload = _write(trail.set([{"label": "Home", "href": "/"}, "Settings"])).payload
    assert payload == {"items": [{"label": "Home", "href": "/"}, {"label": "Settings", "href": ""}]}
    assert _write(trail.set([])).payload == {"items": []}


# --- Skeleton -----------------------------------------------------------------


def test_skeleton_has_no_primary_value():
    assert not hasattr(SkeletonRef, "set")


def test_skeleton_setters_merge_one_key_each():
    sk = _mount(SkeletonRef)
    assert _write(sk.set_lines(3)).payload == {"lines": 3}
    assert _write(sk.set_shape("circle")).payload == {"shape": "circle"}
    assert _write(sk.set_height(120)).payload == {"height": 120}


def test_skeleton_slot_coerces_numbers():
    assert SkeletonRef.slot(lines=3.0, shape="rect", height="80").props == {
        "lines": 3,
        "shape": "rect",
        "height": 80,
    }


# --- Spinner ------------------------------------------------------------------


def test_spinner_set_is_the_label():
    spin = _mount(SpinnerRef)
    assert _write(spin.set("Fetching rows")).payload == {"label": "Fetching rows"}
    assert _write(spin.set_size("lg")).payload == {"size": "lg"}


# --- StatusPill ---------------------------------------------------------------


def test_status_pill_set_carries_tone_first():
    pill = _mount(StatusPillRef)
    frame = _write(pill.set("Deployed", tone="ok"))
    assert frame.payload == {"tone": "ok", "label": "Deployed"}
    assert list(frame.payload) == ["tone", "label"]
    assert _write(pill.set("Queued")).payload == {"label": "Queued"}
    assert _write(pill.set_tone("danger")).payload == {"tone": "danger"}
    assert _write(pill.set_label("Failed")).payload == {"label": "Failed"}


def test_status_pill_tone_is_keyword_only():
    with pytest.raises(TypeError):
        StatusPillRef("p").set("Deployed", "ok")
