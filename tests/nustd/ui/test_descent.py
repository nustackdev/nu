"""Descent: each container's own way down, bare children, and the checks around them.

Wire only, through a fake session, no browser. A bare child (``row[0]`` with no
``item=``) is a plain ``ItemRef``: it names no kind on the wire, so it can erase,
hide or display what is there, and ``.to(Kind)`` names the kind to go on.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd import ui
from nustd.ui import Session
from nustd.ui.core import ItemRef


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


BODY = [
    ui.RowRef,
    ui.ColumnRef,
    ui.ContainerRef,
    ui.BoxRef,
    ui.ModalRef,
    ui.SheetRef,
    ui.CollapsibleRef,
    ui.FormRef,
    ui.FieldsetRef,
    ui.NavListRef,
    ui.CardRef,
    ui.PageSectionRef,
    ui.ListRef,
]


# --- bare descent -----------------------------------------------------------


@pytest.mark.parametrize("cls", BODY, ids=lambda c: c.__name__)
def test_body_containers_take_positions_and_names(cls):
    c = cls("c")
    for key in (0, 3, "k"):
        child = c[key]
        assert type(child) is ItemRef
        assert child._parent is c
    frames = _frames(c[0].to(ui.TextRef).set("a") >> c["k"].to(ui.TextRef).set("b"))
    assert [f.ref for f in frames] == [("c", "0"), ("c", "k")]


def test_line_takes_positions_only():
    line = ui.LineRef("l")
    assert type(line[0]) is ItemRef
    with pytest.raises(TypeError, match="by position, not by name"):
        line["k"]


def test_a_bare_child_claims_no_kind_on_the_wire():
    row = ui.RowRef("r")
    frames = _frames(row[0].hide() >> row[0].display())
    assert [f.op for f in frames] == ["hide", "display"]
    assert _chain(frames[0]) == [("r", "Row"), ("0", None)]


def test_a_bare_child_erases_by_path():
    frames = _frames(ui.RowRef("r")["k"].erase())
    assert frames[0].op == "remove"
    assert frames[0].ref == ("r", "k")


def test_a_bare_child_refuses_to_create():
    child = ui.RowRef("r")[0]
    with pytest.raises(TypeError, match=r"name it first: \.to"):
        child.init()
    with pytest.raises(TypeError, match="bare child"):
        ui.Write(child, nu.Dict.of(a=1))
    with pytest.raises(TypeError, match="bare child"):
        ui.core.Init(child)


def test_a_bare_child_holds_no_children():
    with pytest.raises(TypeError, match=r"name the kind first"):
        ui.TextRef("t", parent_ref=ui.RowRef("r")[0])


def test_to_chains_through_bare_children():
    row = ui.RowRef("r")
    term = row[0].to(ui.ColumnRef)["a"].to(ui.CardRef)["body"].to(ui.TextRef).set("hi")
    frames = _frames(term)
    assert _chain(frames[0]) == [
        ("r", "Row"),
        ("0", "Column"),
        ("a", "Card"),
        ("body", "TextRef"),
    ]


def test_a_computed_key_is_taken_as_given():
    frames = _frames(ui.RowRef("r")[nu.Str("c") + nu.str(2)].to(ui.TextRef).set("x"))
    assert frames[0].ref == ("r", "c2")


# --- keys -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "err"),
    [
        (True, TypeError),
        (None, TypeError),
        ((0, 1), TypeError),
        (1.5, TypeError),
        (-1, IndexError),
        ("", ValueError),
        ("0", ValueError),
    ],
)
def test_keys_that_fail_loud(key, err):
    with pytest.raises(err):
        ui.RowRef("r")[key]


def test_a_numeric_name_points_at_the_position():
    with pytest.raises(ValueError, match="use the int 0"):
        ui.ColumnRef("c")["0"]


# --- item= as a default spec ------------------------------------------------


def test_item_takes_a_spec_with_props():
    row = ui.RowRef("r", item=ui.CardRef.slot(size="sm"))
    card = row[0]
    assert type(card) is ui.CardRef
    frames = _frames(card.set_title("a"))
    assert frames[0].chain[1][2]["size"] == "sm"


def test_item_default_is_overridden_by_to():
    row = ui.RowRef("r", item=ui.CardRef)
    frames = _frames(row[1].to(ui.TextRef).set("x"))
    assert _chain(frames[0])[1] == ("1", "TextRef")


def test_item_refuses_a_non_ui_slot():
    with pytest.raises(TypeError, match="ui kind"):
        ui.RowRef("r", item=nu.StrRef.slot())


# --- named parts ------------------------------------------------------------


def test_card_parts_have_default_kinds():
    card = ui.CardRef("c")
    assert type(card.actions) is ui.RowRef
    assert type(card.footer) is ui.RowRef
    assert type(card.media) is ui.ColumnRef
    frames = _frames(card.actions["go"].to(ui.ButtonRef).init())
    assert _chain(frames[0]) == [("c", "Card"), ("actions", "Row"), ("go", "ButtonRef")]
    assert frames[0].chain[1][2]["gap"] == 2


def test_a_part_re_kinds_with_to():
    frames = _frames(ui.CardRef("c").media.to(ui.ImageRef).init())
    assert _chain(frames[0])[1] == ("media", "ImageRef")


@pytest.mark.parametrize("part", ["media", "actions", "footer"])
def test_a_part_is_not_a_body_key(part):
    with pytest.raises(ValueError, match=rf"reach it as \.{part}"):
        ui.CardRef("c")[part]


def test_page_section_actions_is_not_a_body_key():
    sec = ui.PageSectionRef("s")
    assert type(sec.actions) is ui.RowRef
    with pytest.raises(ValueError, match="own part"):
        sec["actions"]
    assert type(sec["media"]) is ItemRef


# --- Tabs / Accordion -------------------------------------------------------


def test_tabs_take_bodies_by_declared_id():
    tabs = ui.TabsRef("t", props={"tabs": [{"id": "a", "label": "A"}, {"id": "1", "label": "B"}]})
    assert type(tabs["a"]) is ItemRef
    assert type(tabs["1"]) is ItemRef  # names only, so a numeric id is just an id
    with pytest.raises(ValueError, match="no tab id"):
        tabs["nope"]
    with pytest.raises(ValueError, match="no tab id"):
        ui.TextRef("nope", parent_ref=tabs)
    with pytest.raises(TypeError, match="by name, not by position"):
        tabs[0]


def test_tabs_without_a_declared_strip_take_any_id():
    assert type(ui.TabsRef("t")["later"]) is ItemRef


def test_accordion_refuses_an_unknown_section():
    acc = ui.AccordionRef("a", props={"sections": [{"id": "s1", "label": "One"}]})
    assert type(acc["s1"]) is ItemRef
    with pytest.raises(ValueError, match="no section id"):
        acc["s2"]


def test_a_tabs_shape_still_builds_its_slots():
    class Panes(ui.Tabs):
        one = ui.TextRef.slot()
        two = ui.TextRef.slot()

    class Page(ui.Column):
        panes = Panes.slot()

    frames = _frames(Page.panes.two.set("x"))
    assert frames[0].ref == ("panes", "two")


# --- Field ------------------------------------------------------------------


def test_field_control_is_bare_until_named():
    field = ui.FieldRef("f")
    assert type(field.control) is ItemRef
    frames = _frames(field.control.to(ui.InputRef).init())
    assert _chain(frames[0]) == [("f", "Field"), ("control", "InputRef")]


def test_field_control_is_the_shape_slot():
    class Email(ui.Field):
        email = ui.InputRef.slot()

    class Page(ui.Column):
        f = Email.slot(label="Email")

    assert type(Page.f.control) is ui.InputRef
    assert Page.f.control._payload["segment"] == "email"


def test_field_holds_one_control():
    field = ui.FieldRef("f")
    with pytest.raises(TypeError, match="one control"):
        ui.InputRef("other", parent_ref=field)
    with pytest.raises(TypeError, match="not subscriptable"):
        field["x"]


# --- slot name guard --------------------------------------------------------


@pytest.mark.parametrize("name", ["set_title", "hide", "to", "showing", "erase"])
def test_a_slot_named_after_a_ref_method_is_refused(name):
    with pytest.raises(TypeError, match=rf"slot .{name}. clashes with \w+\.{name}"):
        type("Bad", (ui.Card,), {name: ui.TextRef.slot()})


def test_a_slot_named_after_a_part_is_fine():
    class Fine(ui.Card):
        actions = ui.ButtonRef.slot()
        media = ui.ImageRef.slot()

    assert type(ui.CardRef("c", section_cls=Fine).actions) is ui.ButtonRef


def test_a_row_slot_named_set_title_is_fine():
    class Bar(ui.Row):
        set_title = ui.TextRef.slot()

    assert "set_title" in Bar._slots
