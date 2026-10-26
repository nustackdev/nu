"""The looks a page is built from: text and heading type, button and link
looks, card surfaces and slots, image corners and ratio, tabs, empty state,
badge, box grounds. Wire only, through a recording session, no browser.
"""

from __future__ import annotations

import asyncio

import nu
from nu import Context
from nustd.ui import Card, Index, Page, Row, Session
from nustd.ui.core import Changed
from nustd.ui.refs import (
    BadgeRef,
    BoxRef,
    ButtonRef,
    CardRef,
    DividerRef,
    EmptyStateRef,
    HeadingRef,
    ImageRef,
    LinkRef,
    TabsRef,
    TextRef,
)


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _mount(widget_slot):
    """A fresh Index -> Page with `widget_slot` at `.page.sec.w`; returns the handle."""
    sec = type("LSec", (Row,), {"w": widget_slot})
    page = type("LPage", (Page,), {"sec": sec.slot()})
    app = type("LApp", (Index,), {"page": page.slot("/")})
    return app.page.sec.w


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _payload(term):
    [frame] = _frames(term)
    return frame.payload


# --- TextRef ------------------------------------------------------------------


def test_plain_text_seeds_only_its_value():
    assert TextRef.slot(value="hi").props == {"value": "hi"}
    assert TextRef.slot(value="hi", tone="primary", lines=0).props == {"value": "hi"}


def test_text_seeds_the_style_props_it_sets():
    props = TextRef.slot(
        value="v0.6", tone="muted", size="sm", weight="medium", align="center", mono=True, lines=2
    ).props
    assert props == {
        "value": "v0.6",
        "tone": "muted",
        "size": "sm",
        "weight": "medium",
        "align": "center",
        "mono": True,
        "lines": 2,
    }


def test_text_set_stays_bare_and_style_setters_merge_one_key():
    handle = _mount(TextRef.slot(tone="accent"))
    [frame] = _frames(handle.set("hello"))
    assert frame.payload == "hello"
    assert frame.chain[-1][1:] == ("TextRef", {"value": "", "tone": "accent"})
    assert _payload(handle.set_tone("danger")) == {"tone": "danger"}
    assert _payload(handle.set_size("lg")) == {"size": "lg"}
    assert _payload(handle.set_weight("bold")) == {"weight": "bold"}
    assert _payload(handle.set_align("end")) == {"align": "end"}
    assert _payload(handle.set_mono(True)) == {"mono": True}
    assert _payload(handle.set_lines(1)) == {"lines": 1}


# --- HeadingRef ---------------------------------------------------------------


def test_heading_defaults_follow_the_level_and_align_to_start():
    assert HeadingRef.slot(label="Plans").props == {
        "label": "Plans",
        "level": 1,
        "align": "start",
        "size": None,
        "tone": "primary",
        "eyebrow": "",
        "subtitle": "",
    }


def test_heading_takes_a_display_size_eyebrow_and_subtitle():
    props = HeadingRef.slot(
        label="Ship faster", size="display", eyebrow="New", subtitle="One model", tone="accent"
    ).props
    assert props["size"] == "display"
    assert props["eyebrow"] == "New"
    assert props["subtitle"] == "One model"
    assert props["tone"] == "accent"


def test_heading_still_takes_left_and_right():
    assert HeadingRef.slot(align="left").props["align"] == "left"
    assert DividerRef.slot(align="right").props["align"] == "right"
    assert DividerRef.slot(align="start").props["align"] == "start"


def test_heading_setters_merge_one_key():
    handle = _mount(HeadingRef.slot())
    assert _payload(handle.set_size("display")) == {"size": "display"}
    assert _payload(handle.set_size(None)) == {"size": None}
    assert _payload(handle.set_tone("muted")) == {"tone": "muted"}
    assert _payload(handle.set_eyebrow("Pricing")) == {"eyebrow": "Pricing"}
    assert _payload(handle.set_subtitle("Pick one")) == {"subtitle": "Pick one"}


# --- ButtonRef ------------------------------------------------------------------


def test_button_link_looks_size_and_href():
    props = ButtonRef.slot(
        label="Docs", variant="outline", size="lg", href="/docs", target="_blank"
    ).props
    assert props["variant"] == "outline"
    assert props["size"] == "lg"
    assert props["href"] == "/docs"
    assert props["target"] == "_blank"
    assert ButtonRef.slot(variant="link").props["variant"] == "link"


def test_button_set_href_and_size_merge():
    handle = _mount(ButtonRef.slot())
    assert _payload(handle.set_size("sm")) == {"size": "sm"}
    assert _payload(handle.set_href("/plans")) == {"href": "/plans"}
    assert _payload(handle.set_href("https://x.dev", target="_blank")) == {
        "href": "https://x.dev",
        "target": "_blank",
    }
    assert isinstance(handle.on_click(), Changed)


# --- LinkRef ------------------------------------------------------------------


def test_link_defaults_to_a_text_link():
    assert LinkRef.slot(href="/a").props == {
        "href": "/a",
        "label": "",
        "target": "_self",
        "external": None,
        "variant": "text",
        "icon": "",
        "arrow": False,
    }


def test_link_is_text_or_muted_with_icon_and_arrow():
    # A link that looks like a button is a ButtonRef with an href.
    props = LinkRef.slot(
        href="/start", label="Start", variant="muted", icon="sparkles", arrow=True
    ).props
    assert (props["variant"], props["icon"], props["arrow"]) == ("muted", "sparkles", True)
    assert "size" not in props
    assert not hasattr(LinkRef, "set_size")


def test_link_setters_merge_one_key():
    handle = _mount(LinkRef.slot())
    assert _payload(handle.set_variant("muted")) == {"variant": "muted"}
    assert _payload(handle.set_icon("book")) == {"icon": "book"}
    assert _payload(handle.set_arrow(True)) == {"arrow": True}


# --- CardRef --------------------------------------------------------------------


def test_card_slot_carries_surface_size_and_href():
    assert CardRef.slot(variant="elevated", size="lg", href="/p/1", target="_blank").props == {
        "title": "",
        "subtitle": "",
        "caption": "",
        "variant": "elevated",
        "size": "lg",
        "href": "/p/1",
        "target": "_blank",
    }


def test_card_named_slots_boot_as_children_at_their_keys():
    class Plan(Card):
        media = ImageRef.slot(src="/hero.png", aspect="16/9")
        actions = BadgeRef.slot(label="Popular", variant="brand")
        price = TextRef.slot(value="$9")
        footer = ButtonRef.slot(label="Choose", href="/buy")

    class Plans(Page):
        pro = Plan.slot(title="Pro")

    chains = [c for c in Plans._boot_chains() if c[0][0] == "pro"]
    assert [[lvl[:2] for lvl in c] for c in chains] == [
        [("pro", "Card")],
        [("pro", "Card"), ("media", "ImageRef")],
        [("pro", "Card"), ("actions", "BadgeRef")],
        [("pro", "Card"), ("price", "TextRef")],
        [("pro", "Card"), ("footer", "ButtonRef")],
    ]


def test_card_variant_and_href_ride_a_write():
    card = CardRef("c")
    assert _payload(card.set_variant("sunken")) == {"variant": "sunken"}
    assert _payload(card.set_href("/x", target="_blank")) == {"href": "/x", "target": "_blank"}
    # The chrome ops keep their own names on the wire.
    [frame] = _frames(card.set_caption("note"))
    assert (frame.op, frame.payload) == ("set_caption", "note")


# --- ImageRef -------------------------------------------------------------------


def test_image_radius_and_aspect_keep_rounded():
    props = ImageRef.slot(src="/a.png", radius="full", aspect="1:1", fit="scale-down").props
    assert (props["radius"], props["aspect"], props["fit"]) == ("full", "1:1", "scale-down")
    legacy = ImageRef.slot(rounded=True).props
    assert (legacy["rounded"], legacy["radius"], legacy["aspect"]) == (True, None, "")


def test_image_setters_merge_one_key():
    handle = _mount(ImageRef.slot())
    assert _payload(handle.set_radius("lg")) == {"radius": "lg"}
    assert _payload(handle.set_aspect("4/3")) == {"aspect": "4/3"}


# --- Tabs, EmptyState, Badge, Box ----------------------------------------------


def test_tabs_variant():
    assert TabsRef.slot(tabs=[{"id": "a", "label": "A"}]).props["variant"] == "line"
    assert TabsRef.slot(variant="segmented").props["variant"] == "segmented"
    assert _payload(TabsRef("t").set_variant("pill")) == {"variant": "pill"}


def test_empty_state_icon_and_action():
    props = EmptyStateRef.slot(label="No planes", icon="folder", action="New plane").props
    assert (props["icon"], props["action"], props["action_href"]) == ("folder", "New plane", "")
    handle = _mount(EmptyStateRef.slot())
    assert _payload(handle.set_icon("search")) == {"icon": "search"}
    assert _payload(handle.set_action("Create")) == {"action": "Create"}
    assert _payload(handle.set_action("Docs", href="/docs")) == {
        "action": "Docs",
        "action_href": "/docs",
    }
    assert _payload(handle.set_action("Docs", href="https://x.dev", target="_blank")) == {
        "action": "Docs",
        "action_href": "https://x.dev",
        "action_target": "_blank",
    }
    assert isinstance(handle.on_action(), Changed)


def test_badge_brand_tones_and_size():
    assert BadgeRef.slot(label="New").props == {"label": "New", "variant": "neutral", "size": "md"}
    assert BadgeRef.slot(variant="brand", size="lg").props["variant"] == "brand"
    assert BadgeRef.slot(variant="secondary").props["variant"] == "secondary"
    assert _payload(_mount(BadgeRef.slot()).set_size("sm")) == {"size": "sm"}


def test_box_takes_the_new_grounds():
    for ground in ("sunken", "accent", "brand"):
        assert BoxRef.slot(background=ground).props["background"] == ground
