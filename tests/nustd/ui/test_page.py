"""Page parts: sections, navs, icons, spacers, page links, and a capped Column.

Wire types, slot props and their defaults, the frames each setter ships,
and where named children land. Runs against a recording session, same
harness as test_grid.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core.base import _wire_type_of
from nustd.ui.core.chains import boot_chains


class _RecordingSession:
    def __init__(self) -> None:
        self.frames: list = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)


def _frames(term):
    sess = _RecordingSession()
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    return sess.frames


def _chain(frame):
    return [(seg, typ) for seg, typ, _ in frame.chain]


# --- wire types --------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "wire"),
    [
        ("PageSectionRef", "PageSection"),
        ("NavListRef", "NavList"),
        ("IconRef", "IconRef"),
        ("SpacerRef", "SpacerRef"),
        ("PageLinkRef", "PageLinkRef"),
        ("NavItemRef", "NavItemRef"),
    ],
)
def test_wire_types(name, wire):
    import nustd.ui as ui

    assert getattr(ui, name)._wire_type == wire


def test_containers_and_leaves():
    from nustd.ui import (
        IconRef,
        LeafRef,
        NavItemRef,
        NavList,
        NavListRef,
        PageLinkRef,
        PageSection,
        PageSectionRef,
        SpacerRef,
    )
    from nustd.ui.refs import CollectionRef

    for ref_cls in (PageSectionRef, NavListRef):
        assert issubclass(ref_cls, CollectionRef)
    for ref_cls in (IconRef, SpacerRef, PageLinkRef, NavItemRef):
        assert issubclass(ref_cls, LeafRef)
    assert PageSection._ref_cls is PageSectionRef
    assert NavList._ref_cls is NavListRef
    assert _wire_type_of(PageSection) == "PageSection"
    assert _wire_type_of(NavList) == "NavList"


# --- PageSection -------------------------------------------------------------


SECTION_DEFAULTS = {"title": "", "description": "", "size": "md", "bordered": False, "gap": 4}


def test_section_slot_defaults_and_shape_forwarding():
    from nustd.ui import PageSection, PageSectionRef

    assert PageSectionRef.slot().props == SECTION_DEFAULTS
    props = PageSection.slot(title="Usage", size="lg", bordered=1, gap="6").props
    assert props == {**SECTION_DEFAULTS, "title": "Usage", "size": "lg", "bordered": True, "gap": 6}
    with pytest.raises(TypeError):
        PageSectionRef.slot(actions="nope")


def test_section_actions_is_a_row_in_the_header_key():
    from nustd.ui.refs import ButtonRef, ColumnRef, PageSectionRef

    section = PageSectionRef("usage", parent_ref=ColumnRef("page"), props={"title": "Usage"})
    [frame] = _frames(ButtonRef("export", parent_ref=section.actions).set_label("Export"))
    assert frame.ref == ("page", "usage", "actions", "export")
    assert _chain(frame) == [
        ("page", "Column"),
        ("usage", "PageSection"),
        ("actions", "Row"),
        ("export", "ButtonRef"),
    ]
    assert frame.chain[1][2]["title"] == "Usage"
    assert frame.chain[2][2]["gap"] == 2


def test_a_shape_actions_slot_wins_over_the_default_row():
    from nustd.ui import ButtonRef, Column, PageSection, TextRef

    class Usage(PageSection):
        actions = ButtonRef.slot(label="Export")
        note = TextRef.slot(value="body")

    class Home(Column):
        usage = Usage.slot(title="Usage")

    chains = [c for c in boot_chains((), Home) if c[0][0] == "usage"]
    assert [[lvl[:2] for lvl in c] for c in chains] == [
        [("usage", "PageSection")],
        [("usage", "PageSection"), ("actions", "ButtonRef")],
        [("usage", "PageSection"), ("note", "TextRef")],
    ]
    [frame] = _frames(Home.usage.actions.set_label("Download"))
    assert frame.ref == ("usage", "actions")
    assert _chain(frame)[-1] == ("actions", "ButtonRef")


def test_section_setters_write_their_key():
    from nustd.ui.refs import PageSectionRef

    sec = PageSectionRef("s")
    frames = _frames(sec.set_title("T") >> sec.set_description("D") >> sec.set_bordered(True))
    assert [f.op for f in frames] == ["write"] * 3
    assert [f.payload for f in frames] == [{"title": "T"}, {"description": "D"}, {"bordered": True}]


# --- NavList and NavItem -----------------------------------------------------


def test_nav_list_and_items():
    from nustd.ui import Column, NavItemRef, NavList, NavListRef

    assert NavListRef.slot().props == {"variant": "vertical", "label": ""}

    class Sidebar(NavList):
        home = NavItemRef.slot(label="Home", href="/", icon="home")
        docs = NavItemRef.slot(label="Docs", href="/docs", icon="book-open", meta="12")

    class Home(Column):
        sidebar = Sidebar.slot(label="Workspace")

    chains = [c for c in boot_chains((), Home) if c[0][0] == "sidebar"]
    assert chains[0][0][1:] == ("NavList", {"variant": "vertical", "label": "Workspace"})
    assert chains[2][1] == (
        "docs",
        "NavItemRef",
        {
            "label": "Docs",
            "href": "/docs",
            "icon": "book-open",
            "meta": "12",
            "active": None,
            "exact": False,
            "target": "_self",
        },
    )


def test_nav_item_active_is_auto_by_default_and_pinnable():
    from nustd.ui.refs import NavItemRef, NavListRef

    assert NavItemRef.slot().props["active"] is None
    assert NavItemRef.slot(active=1).props["active"] is True
    item = NavItemRef("i", parent_ref=NavListRef("bar", props={"variant": "horizontal"}))
    pinned, auto = _frames(item.set_active(True) >> item.set_active(None))
    assert pinned.payload == {"active": True}
    assert auto.payload == {"active": None}
    assert pinned.chain[0] == ("bar", "NavList", {"variant": "horizontal", "label": ""})


# --- leaves ------------------------------------------------------------------


def test_icon_slot_and_set():
    from nustd.ui.refs import IconRef

    assert IconRef.slot().props == {
        "name": "",
        "size": "md",
        "tone": "inherit",
        "framed": False,
        "label": "",
    }
    icon = IconRef("i")
    [named, toned] = _frames(icon.set("rocket") >> icon.set_tone("accent"))
    assert named.payload == {"name": "rocket"}
    assert toned.payload == {"tone": "accent"}


def test_spacer_takes_no_props_and_no_children():
    from nustd.ui.refs import RowRef, SpacerRef, TextRef

    assert SpacerRef.slot().props == {}
    with pytest.raises(TypeError):
        SpacerRef.slot(size=2)
    spacer = SpacerRef("gap", parent_ref=RowRef("bar"))
    with pytest.raises(TypeError, match="SpacerRef is a leaf"):
        TextRef("t", parent_ref=spacer)


def test_page_link_slot_and_partial_set():
    from nustd.ui.refs import GridRef, PageLinkRef

    assert PageLinkRef.slot(title="Notes", href="/notes", icon="📝", variant="tile").props == {
        "href": "/notes",
        "title": "Notes",
        "icon": "📝",
        "description": "",
        "meta": "",
        "variant": "tile",
        "target": "_self",
    }
    link = PageLinkRef(nu.Str("p") + nu.str(1), parent_ref=GridRef("pages"))
    [frame] = _frames(link.set(title="Roadmap", meta="2d ago"))
    assert frame.ref == ("pages", "p1")
    assert frame.payload == {"title": "Roadmap", "meta": "2d ago"}
    assert _chain(frame) == [("pages", "Grid"), ("p1", "PageLinkRef")]


# --- Column: page width ------------------------------------------------------


def test_column_caps_and_centers():
    from nustd.ui import Column, ColumnRef

    props = ColumnRef.slot().props
    assert props["max_width"] == "full"
    assert props["center"] is True
    assert Column.slot(max_width="prose", center=False, justify="evenly").props == {
        **props,
        "max_width": "prose",
        "center": False,
        "justify": "evenly",
    }


# --- the header actions key: one spelling for Card and Section ---------------


def test_card_actions_is_a_row_at_the_same_key_as_a_section():
    from nustd.ui.refs import ButtonRef, CardRef, ColumnRef, PageSectionRef

    card = CardRef("plan", parent_ref=ColumnRef("page"), props={"title": "Pro"})
    [frame] = _frames(ButtonRef("buy", parent_ref=card.actions).set_label("Buy"))
    assert frame.ref == ("page", "plan", "actions", "buy")
    assert _chain(frame)[1:3] == [("plan", "Card"), ("actions", "Row")]
    section = PageSectionRef("s")
    assert card.actions._payload["segment"] == section.actions._payload["segment"] == "actions"


def test_a_card_shape_actions_slot_wins_over_the_default_row():
    from nustd.ui import BadgeRef, Card

    class Plan(Card):
        actions = BadgeRef.slot(label="Popular")

    from nustd.ui.refs import CardRef

    card = CardRef("p", section_cls=Plan)
    assert type(card.actions).__name__ == "BadgeRef"


# --- icons: the names the docs list are the names the kit ships ---------------


def test_the_button_docstring_lists_every_icon_the_kit_ships():
    import re
    from pathlib import Path

    from nustd.ui import ButtonRef

    icons = Path(__file__).resolve().parents[3] / "pkgs/ts/ui-kit/src/nodes/input/icons.ts"
    body = icons.read_text().split("export const ICONS", 1)[1]
    shipped = re.findall(r'^\s*"?([a-z0-9-]+)"?:\s*[A-Z]', body, re.M)
    doc = " ".join(ButtonRef.__doc__.split())
    listed = doc.split("takes):", 1)[1].split(". An unknown", 1)[0]
    assert [n.strip() for n in listed.split(",")] == shipped


# --- init: a node on screen as declared ----------------------------------------


def test_init_inits_the_node_and_every_slot_its_shape_declares():
    from nustd.ui import Column, HeadingRef, Row
    from nustd.ui.core import OP_INIT
    from nustd.ui.refs import ButtonRef, ColumnRef

    class Hero(Column):
        title = HeadingRef.slot(label="Hi")

        class Bar(Row):
            go = ButtonRef.slot(label="Go")

        bar = Bar.slot(gap=2)

    page = ColumnRef("p", section_cls=Hero, props={"gap": 6})
    frames = _frames(page.init())
    assert {f.op for f in frames} == {OP_INIT}
    assert [tuple(f.ref) for f in frames] == [
        ("p",),
        ("p", "title"),
        ("p", "bar"),
        ("p", "bar", "go"),
    ]
    assert all(f.payload is None for f in frames)
    assert frames[0].chain[0][2]["gap"] == 6
    assert frames[1].chain[-1] == ("title", "HeadingRef", {"label": "Hi", **frames[1].chain[-1][2]})


def test_init_on_a_plain_ref_is_one_init_with_its_props():
    from nustd.ui.refs import ColumnRef, TextRef

    [frame] = _frames(TextRef("t", parent_ref=ColumnRef("c"), props={"value": "x"}).init())
    assert (frame.op, tuple(frame.ref)) == ("init", ("c", "t"))
    assert frame.chain[-1][2] == {"value": "x"}


# --- hide / display: a node off screen and back ---------------------------------


@pytest.mark.parametrize(("method", "op"), [("hide", "hide"), ("display", "display")])
def test_hide_and_display_ship_the_chain_and_no_payload(method, op):
    from nustd.ui.core import OP_DISPLAY, OP_HIDE
    from nustd.ui.refs import CardRef, ColumnRef

    card = CardRef("c", parent_ref=ColumnRef("p", props={"gap": 6}), props={"title": "T"})
    [frame] = _frames(getattr(card, method)())
    assert frame.op == {"hide": OP_HIDE, "display": OP_DISPLAY}[method] == op
    assert tuple(frame.ref) == ("p", "c")
    assert frame.payload is None
    assert _chain(frame) == [("p", "Column"), ("c", "Card")]
    assert frame.chain[0][2]["gap"] == 6
    assert frame.chain[1][2]["title"] == "T"


def test_hide_on_a_shape_is_one_frame_for_the_whole_subtree():
    """Hidden is the node's flag and its subtree goes with it, so a Shape's
    slots get no frames of their own, unlike init."""
    from nustd.ui import Column, HeadingRef
    from nustd.ui.refs import ColumnRef

    class Hero(Column):
        title = HeadingRef.slot(label="Hi")

    frames = _frames(ColumnRef("p", section_cls=Hero).hide())
    assert [(f.op, tuple(f.ref)) for f in frames] == [("hide", ("p",))]


def test_hide_then_display_reach_a_slot_through_its_page():
    from nustd.ui import Column, HeadingRef

    class Hero(Column):
        title = HeadingRef.slot(label="Hi")

    frames = _frames(Hero.title.hide() >> Hero.title.display())
    assert [(f.op, tuple(f.ref)) for f in frames] == [
        ("hide", ("title",)),
        ("display", ("title",)),
    ]


# --- named child keys: Card media / actions / footer ---------------------------


def test_card_named_children_land_at_their_keys():
    from nustd.ui.refs import ButtonRef, CardRef, ImageRef
    from nustd.ui.refs.collections.named import ACTIONS, FOOTER, MEDIA

    card = CardRef("c", props={"caption": "note"})
    frames = _frames(
        ImageRef("img", parent_ref=card.media).set("/a.png")
        >> ButtonRef("go", parent_ref=card.footer).set_label("Go")
    )
    assert [_chain(f)[:2] for f in frames] == [
        [("c", "Card"), (MEDIA, "Column")],
        [("c", "Card"), (FOOTER, "Row")],
    ]
    # The footer child and the caption prop live side by side.
    assert frames[1].chain[0][2]["caption"] == "note"
    assert frames[1].chain[1][2] == CardRef("x").actions._payload["props"]
    assert card.actions._payload["segment"] == ACTIONS


def test_card_and_section_actions_rows_carry_the_same_props():
    from nustd.ui.refs import CardRef, PageSectionRef

    assert CardRef("c").actions._payload["props"] == PageSectionRef("s").actions._payload["props"]


def test_a_card_shape_media_and_footer_slots_win_over_the_defaults():
    from nustd.ui import ButtonRef, Card, ImageRef
    from nustd.ui.refs import CardRef

    class Plan(Card):
        media = ImageRef.slot(src="/hero.png")
        footer = ButtonRef.slot(label="Buy")

    card = CardRef("p", section_cls=Plan)
    assert type(card.media).__name__ == "ImageRef"
    assert type(card.footer).__name__ == "ButtonRef"


# --- setters on the page containers --------------------------------------------


def test_section_size_gap_and_nav_variant_setters():
    from nustd.ui.refs import NavListRef, PageSectionRef

    sec, nav = PageSectionRef("s"), NavListRef("n")
    frames = _frames(sec.set_size("lg") >> sec.set_gap(6) >> nav.set_variant("horizontal"))
    assert [f.payload for f in frames] == [{"size": "lg"}, {"gap": 6}, {"variant": "horizontal"}]


def test_box_and_form_set_title():
    from nustd.ui.refs import BoxRef, FormRef

    frames = _frames(BoxRef("b").set_title("B") >> FormRef("f").set_title("F"))
    assert [(f.op, f.payload) for f in frames] == [
        ("write", {"title": "B"}),
        ("write", {"title": "F"}),
    ]


# --- href: one spelling on everything that links -------------------------------


@pytest.mark.parametrize("ref_name", ["ButtonRef", "CardRef", "LinkRef", "PageLinkRef"])
def test_set_href_takes_a_target_on_everything_that_links(ref_name):
    import nustd.ui as ui

    ref = getattr(ui, ref_name)("x")
    plain, blank = _frames(ref.set_href("/a") >> ref.set_href("/b", target="_blank"))
    assert plain.payload == {"href": "/a"}
    assert blank.payload == {"href": "/b", "target": "_blank"}


def test_link_set_target_still_works():
    from nustd.ui.refs import LinkRef

    [frame] = _frames(LinkRef("l").set_target("_blank"))
    assert frame.payload == {"target": "_blank"}


# --- PageLink inline -----------------------------------------------------------


def test_page_link_inline_variant_on_the_wire():
    from nustd.ui.refs import LineRef, PageLinkRef

    link = PageLinkRef(
        "p",
        parent_ref=LineRef("prose"),
        props={"href": "/notes", "title": "Notes", "icon": "file-text", "variant": "inline"},
    )
    shown, switched = _frames(link.init() >> link.set_variant("tile"))
    assert _chain(shown) == [("prose", "Line"), ("p", "PageLinkRef")]
    # Inline draws no description or meta, but the props still carry them.
    assert shown.chain[-1][2] == {
        "href": "/notes",
        "title": "Notes",
        "icon": "file-text",
        "description": "",
        "meta": "",
        "variant": "inline",
        "target": "_self",
    }
    assert switched.payload == {"variant": "tile"}


# --- slot() coerces what it is handed ------------------------------------------


@pytest.mark.parametrize(
    ("ref_name", "given", "expected"),
    [
        ("RowRef", {"wrap": 1, "gap": "2"}, {"wrap": True, "gap": 2}),
        ("ColumnRef", {"gap": "3", "padding": "1"}, {"gap": 3, "padding": 1}),
        ("ModalRef", {"open": 1, "dismissible": 0}, {"open": True, "dismissible": False}),
        ("FieldsetRef", {"disabled": 1}, {"disabled": True}),
        ("FieldRef", {"required": 1}, {"required": True}),
        ("ListRef", {"start": "3"}, {"start": 3}),
        ("FormRef", {"gap": "2"}, {"gap": 2}),
    ],
)
def test_slot_coerces_bools_and_ints(ref_name, given, expected):
    import nustd.ui as ui

    props = getattr(ui, ref_name).slot(**given).props
    for key, value in expected.items():
        assert props[key] == value and type(props[key]) is type(value), (ref_name, key)


# --- Tabs / Accordion: every declared slot is listed ---------------------------


def test_tabs_without_a_tabs_list_take_one_tab_per_slot():
    from nustd.ui import Tabs, TextRef

    class Views(Tabs):
        overview = TextRef.slot(value="o")
        raw_data = TextRef.slot(value="r")

    assert Views.slot().props["tabs"] == [
        {"id": "overview", "label": "Overview"},
        {"id": "raw_data", "label": "Raw data"},
    ]


def test_tabs_that_leave_a_slot_out_raise():
    from nustd.ui import Tabs, TextRef

    class Views(Tabs):
        overview = TextRef.slot()
        raw = TextRef.slot()

    with pytest.raises(ValueError, match=r"\['raw'\]"):
        Views.slot(tabs=[{"id": "overview", "label": "Overview"}])
    # Extra entries are item template children, not a mistake.
    listed = [
        {"id": "overview", "label": "O"},
        {"id": "raw", "label": "R"},
        {"id": "x", "label": "X"},
    ]
    assert [t["id"] for t in Views.slot(tabs=listed).props["tabs"]] == ["overview", "raw", "x"]


def test_accordion_sections_follow_the_same_rule():
    from nustd.ui import Accordion, TextRef

    class Faq(Accordion):
        pricing = TextRef.slot()
        billing = TextRef.slot()

    assert [s["id"] for s in Faq.slot().props["sections"]] == ["pricing", "billing"]
    with pytest.raises(ValueError, match="sections="):
        Faq.slot(sections=[{"id": "pricing", "label": "Pricing"}])


def test_a_bare_tabs_slot_still_has_an_empty_strip():
    from nustd.ui import Tabs

    assert Tabs.slot().props["tabs"] == []
