"""Disclosure containers: Collapsible and Sheet, as Refs alone and as Shapes.

Each carries one chrome value of its own, open vs closed, so each has a
``set()`` that writes only what it is given, and an ``on_change()`` for what
the tab sends back (a Collapsible's toggles, a Sheet's dismiss). Children are
separate nodes, open-ended, under a block flow.

Runs against a recording session, same harness as test_layers.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core.base import _wire_type_of
from nustd.ui.core.chains import boot_chains
from nustd.ui.core.interactions import Changed


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


# --- Collapsible -------------------------------------------------------------


def test_collapsible_wire_type_and_slot_defaults():
    from nustd.ui import Collapsible, CollapsibleRef

    assert CollapsibleRef._wire_type == "Collapsible"
    assert _wire_type_of(Collapsible) == "Collapsible"
    assert CollapsibleRef.slot().props == {"title": "", "open": False}
    assert CollapsibleRef.slot(open=1).props["open"] is True


def test_collapsible_shape_slot_forwards_to_the_ref():
    from nustd.ui import Collapsible, CollapsibleRef

    assert Collapsible.slot().props == CollapsibleRef.slot().props
    assert Collapsible.slot(title="Details", open=True).props == {
        "title": "Details",
        "open": True,
    }
    assert "_wire_type" not in vars(Collapsible)
    assert "slot" not in vars(Collapsible)


def test_collapsible_set_writes_only_what_it_is_given():
    from nustd.ui import CollapsibleRef

    ref = CollapsibleRef("c")
    frames = _frames(
        ref.set(open=True)
        >> ref.set(title="Details")
        >> ref.set(open=False, title="Hidden")
        >> ref.set_open(True)
        >> ref.set_title("T"),
    )
    assert [f.op for f in frames] == ["write"] * 5
    assert [f.payload for f in frames] == [
        {"open": True},
        {"title": "Details"},
        {"open": False, "title": "Hidden"},
        {"open": True},
        {"title": "T"},
    ]
    assert frames[0].ref == ("c",)


def test_collapsible_on_change_is_a_changed():
    from nustd.ui import CollapsibleRef

    assert isinstance(CollapsibleRef("c").on_change(), Changed)


def test_collapsible_boot_chain_on_a_page():
    from nustd.ui import Collapsible, Column, TextRef

    class Details(Collapsible):
        note = TextRef.slot(value="inside")

    class Home(Column):
        details = Details.slot(title="Details", open=True)

    chains = boot_chains((), Home)
    assert [[lvl[:2] for lvl in c] for c in chains if c[0][0] == "details"] == [
        [("details", "Collapsible")],
        [("details", "Collapsible"), ("note", "TextRef")],
    ]
    [head] = [c for c in chains if [lvl[:2] for lvl in c] == [("details", "Collapsible")]]
    assert head[0][2] == {"title": "Details", "open": True}


def test_collapsible_shape_handle_drives_open_state():
    from nu import Shape
    from nustd.ui import Collapsible, Column, TextRef

    class Details(Collapsible):
        note = TextRef.slot()

    class Home(Column):
        details = Details.slot(title="Details")

    class App(Shape):
        home = Home.slot()

    [opened, wrote] = _frames(App.home.details.set(open=True) >> App.home.details.note.set("x"))
    assert opened.ref == ("home", "details")
    assert opened.payload == {"open": True}
    assert _chain(wrote) == [("home", "Column"), ("details", "Collapsible"), ("note", "TextRef")]


def test_collapsible_alone_holds_children():
    from nustd.ui import CollapsibleRef, ColumnRef, TextRef

    col = ColumnRef("col")
    details = CollapsibleRef("details", parent_ref=col, props={"title": "Details"})
    [frame] = _frames(TextRef("t", parent_ref=details).set("hi"))
    assert _chain(frame) == [("col", "Column"), ("details", "Collapsible"), ("t", "TextRef")]
    assert frame.chain[1][2] == {"title": "Details", "open": False}


def test_collapsible_refuses_unknown_props():
    from nustd.ui import CollapsibleRef

    with pytest.raises(TypeError):
        CollapsibleRef("c", props={"side": "left"})


# --- Sheet -------------------------------------------------------------------


def test_sheet_wire_type_and_slot_defaults():
    from nustd.ui import Sheet, SheetRef

    assert SheetRef._wire_type == "Sheet"
    assert _wire_type_of(Sheet) == "Sheet"
    assert SheetRef.slot().props == {
        "open": False,
        "title": "",
        "side": "right",
        "size": "md",
        "dismissible": True,
    }


def test_sheet_shape_slot_forwards_to_the_ref():
    from nustd.ui import Sheet, SheetRef

    props = {"title": "Edit", "side": "left", "size": "lg", "dismissible": False}
    assert Sheet.slot(**props).props == SheetRef.slot(**props).props
    assert Sheet.slot(**props).props["side"] == "left"
    assert "_wire_type" not in vars(Sheet)
    assert "slot" not in vars(Sheet)


def test_sheet_set_writes_only_what_it_is_given():
    from nustd.ui import SheetRef

    ref = SheetRef("s")
    frames = _frames(
        ref.set(open=True)
        >> ref.set(title="Edit host")
        >> ref.set(open=False, title="Closed")
        >> ref.set_open(False)
        >> ref.set_title("T"),
    )
    assert [f.payload for f in frames] == [
        {"open": True},
        {"title": "Edit host"},
        {"open": False, "title": "Closed"},
        {"open": False},
        {"title": "T"},
    ]


def test_sheet_on_change_is_a_changed():
    from nustd.ui import SheetRef

    assert isinstance(SheetRef("s").on_change(), Changed)


def test_sheet_alone_under_a_column():
    from nustd.ui import ColumnRef, SheetRef, TextRef

    col = ColumnRef("col")
    sheet = SheetRef("inspector", parent_ref=col, props={"title": "Edit", "side": "left"})
    [opened, wrote] = _frames(sheet.set(open=True) >> TextRef("t", parent_ref=sheet).set("hi"))
    assert opened.ref == ("col", "inspector")
    assert opened.payload == {"open": True}
    assert _chain(wrote) == [("col", "Column"), ("inspector", "Sheet"), ("t", "TextRef")]
    assert wrote.chain[1][2] == {
        "open": False,
        "title": "Edit",
        "side": "left",
        "size": "md",
        "dismissible": True,
    }


def test_sheet_boot_chain_on_a_page():
    from nustd.ui import ButtonRef, Column, Form, InputRef, Sheet

    class EditForm(Form):
        name = InputRef.slot()
        save = ButtonRef.slot(label="Save")

    class Inspector(Sheet):
        form = EditForm.slot()

    class Home(Column):
        inspector = Inspector.slot(title="Edit host", open=True)

    chains = [c for c in boot_chains((), Home) if c[0][0] == "inspector"]
    assert [[lvl[:2] for lvl in c] for c in chains] == [
        [("inspector", "Sheet")],
        [("inspector", "Sheet"), ("form", "Form")],
        [("inspector", "Sheet"), ("form", "Form"), ("name", "InputRef")],
        [("inspector", "Sheet"), ("form", "Form"), ("save", "ButtonRef")],
    ]
    assert chains[0][0][2]["open"] is True
    assert chains[0][0][2]["title"] == "Edit host"
