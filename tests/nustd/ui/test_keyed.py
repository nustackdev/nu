"""Keyed children: a container slot declared with an item template.

``Grid.slot(Card)`` answers ``ref[key]`` with a Card under that key, the way
``DictRef.slot(Order)`` answers ``desks["d1"]`` with an Order. How a
container takes children is its kind: by key, by index, or only the ones its
Shape declares. The frames must carry the same chain a declared slot would:
each level's segment, wire type and the props its template declared. Same
harness as test_layers.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd import ui
from nustd.ui import Session, shapes
from nustd.ui.refs.containers import (
    DictContainerRef,
    ListContainerRef,
    ShapeContainerRef,
)


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


class Entry(ui.Line):
    name = ui.LinkRef.slot()
    tag = ui.BadgeRef.slot()


class SpeciesCard(ui.Card):
    count = ui.StatRef.slot()


class AtlasCard(SpeciesCard):
    @classmethod
    def slot(cls, item=None, /, **props):
        return super().slot(item, **{"subtitle": "atlas", **props})


class Home(ui.Column):
    entries = ui.List.slot(Entry)
    atlas = ui.Grid.slot(SpeciesCard, min_width=200)
    pinned = ui.Grid.slot(AtlasCard)
    tags = ui.Line.slot(ui.BadgeRef)
    row = ui.Row.slot()


# --- the kinds ----------------------------------------------------------------


KIND = {
    "Accordion": DictContainerRef,
    "Box": DictContainerRef,
    "Card": DictContainerRef,
    "Collapsible": DictContainerRef,
    "Column": DictContainerRef,
    "Field": ShapeContainerRef,
    "Fieldset": DictContainerRef,
    "Form": DictContainerRef,
    "Grid": DictContainerRef,
    "Line": ListContainerRef,
    "List": ListContainerRef,
    "Modal": DictContainerRef,
    "Row": DictContainerRef,
    "Sheet": DictContainerRef,
    "Tabs": DictContainerRef,
}


def test_every_container_shape_has_one_kind():
    assert set(KIND) == set(shapes.__all__)
    for name, kind in KIND.items():
        assert issubclass(getattr(shapes, name)._ref_cls, kind), name


@pytest.mark.parametrize("name", sorted(n for n, k in KIND.items() if k is DictContainerRef))
def test_every_dict_container_takes_children_by_key(name):
    page = type("Page", (ui.Column,), {"c": getattr(shapes, name).slot(ui.TextRef)})
    frames = _frames(page.c["k"].set("hi"))
    assert frames[0].ref == ("c", "k")
    assert frames[0].chain[1][1] == "TextRef"


@pytest.mark.parametrize("name", sorted(n for n, k in KIND.items() if k is ListContainerRef))
def test_every_list_container_takes_children_by_index(name):
    page = type("Page", (ui.Column,), {"c": getattr(shapes, name).slot(ui.TextRef)})
    frames = _frames(page.c[2].set("hi"))
    assert frames[0].chain[1][:2] == ("2", "TextRef")


# --- navigation ---------------------------------------------------------------


def test_a_keyed_child_is_its_template_under_the_key():
    frames = _frames(Home.atlas["lion"].count.set("1"))
    assert _chain(frames[0]) == [("atlas", "Grid"), ("lion", "Card"), ("count", "StatRef")]


def test_an_indexed_child_is_its_template_at_the_index():
    frames = _frames(Home.entries[0].tag.set("VU"))
    assert _chain(frames[0]) == [("entries", "ListRef"), ("0", "Line"), ("tag", "BadgeRef")]


def test_each_key_is_its_own_child():
    frames = _frames(Home.tags[0].set("one") >> Home.tags[1].set("two"))
    assert [f.ref for f in frames] == [("tags", "0"), ("tags", "1")]


def test_a_computed_key_resolves_like_any_address():
    frames = _frames(Home.atlas[nu.Str("sp") + nu.str(3)].count.set("88"))
    assert _chain(frames[0])[1] == ("sp3", "Card")


def test_a_computed_index_resolves_like_any_address():
    frames = _frames(Home.entries[nu.int(1) + 1].tag.set("VU"))
    assert _chain(frames[0])[1] == ("2", "Line")


def test_slot_props_and_template_props_ride_the_chain():
    frames = _frames(Home.pinned["lion"].count.set("1"))
    props = {seg: p for seg, _, p in frames[0].chain}
    assert props["pinned"]["min_width"] == 240
    assert props["lion"]["subtitle"] == "atlas"
    plain = _frames(Home.atlas["lion"].count.set("1"))
    assert dict(plain[0].chain[0][2])["min_width"] == 200


def test_chrome_on_a_keyed_container_child():
    frames = _frames(Home.atlas["lion"].set_title("Lion"))
    assert frames[0].ref == ("atlas", "lion")
    assert frames[0].payload == "Lion"


def test_declared_slots_and_keyed_children_mix():
    class Atlas(ui.Grid):
        header = ui.TextRef.slot()

    class Page(ui.Column):
        atlas = Atlas.slot(SpeciesCard)

    named = _frames(Page.atlas.header.set("Atlas"))
    keyed = _frames(Page.atlas["lion"].count.set("1"))
    assert _chain(named[0]) == [("atlas", "Grid"), ("header", "TextRef")]
    assert _chain(keyed[0])[1] == ("lion", "Card")


def test_tabs_take_their_panels_by_tab_id():
    class Panel(ui.Column):
        body = ui.TextRef.slot()

    class Page(ui.Column):
        tabs = ui.Tabs.slot(Panel)

    frames = _frames(Page.tabs["overview"].body.set("hi"))
    assert frames[0].ref == ("tabs", "overview", "body")


def test_nested_templates_go_through_a_shape():
    class Shelf(ui.Column):
        cards = ui.Grid.slot(SpeciesCard)

    class Page(ui.Column):
        shelves = ui.List.slot(Shelf)

    frames = _frames(Page.shelves[0].cards["lion"].count.set("1"))
    assert frames[0].ref == ("shelves", "0", "cards", "lion", "count")


# --- layer 1 ------------------------------------------------------------------


def test_a_ref_built_alone_takes_an_item():
    grid = ui.GridRef("g", item=SpeciesCard)
    frames = _frames(grid["lion"].count.set("1"))
    assert _chain(frames[0]) == [("g", "Grid"), ("lion", "Card"), ("count", "StatRef")]


def test_a_ref_slot_takes_an_item():
    class Page(ui.Column):
        g = ui.GridRef.slot(ui.TextRef, columns=3)

    frames = _frames(Page.g["k"].set("hi"))
    assert frames[0].chain[0][2]["columns"] == 3
    assert frames[0].chain[1][1] == "TextRef"


# --- refusals -----------------------------------------------------------------


def test_a_field_takes_no_item():
    class Notes(ui.Field):
        notes = ui.TextAreaRef.slot()

    with pytest.raises(TypeError, match="takes no item"):
        Notes.slot(ui.InputRef)
    with pytest.raises(TypeError):
        ui.FieldRef("f", item=ui.InputRef)


def test_a_field_is_not_subscriptable():
    class Notes(ui.Field):
        notes = ui.TextAreaRef.slot()

    class Page(ui.Column):
        f = Notes.slot()

    with pytest.raises(TypeError, match="not subscriptable"):
        Page.f["x"]


def test_a_container_without_an_item_refuses_keys():
    with pytest.raises(TypeError, match=r"\.slot\(Item\)"):
        Home.row["x"]


def test_an_item_must_be_a_section_or_a_ref_class():
    with pytest.raises(TypeError, match="Section or a Ref class"):
        ui.Grid.slot("card")
    with pytest.raises(TypeError, match="Section or a Ref class"):
        ui.Grid.slot(SpeciesCard.slot())


def test_list_indices_are_non_negative_ints():
    with pytest.raises(TypeError, match="ints"):
        Home.entries["a"]
    with pytest.raises(IndexError):
        Home.entries[-1]


def test_a_keyed_leaf_still_refuses_children():
    with pytest.raises(TypeError, match="leaf"):
        ui.TextRef("t", parent_ref=Home.tags[0])


def test_no_class_is_made_for_a_template():
    before = set(ui.Grid.__subclasses__())
    ui.Grid.slot(SpeciesCard)
    ui.Grid.slot(SpeciesCard)
    assert set(ui.Grid.__subclasses__()) == before
