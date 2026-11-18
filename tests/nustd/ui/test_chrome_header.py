"""The header part on chrome containers, and the Popover's trigger part.

A Card, PageSection, Modal, Sheet or Popover takes a ``header`` child in place
of its string title: ``ref.header`` answers with the Shape's ``header`` slot,
or a Row at key ``header``. A Popover also takes a ``trigger`` child, drawn
inside its trigger button. Wire only, through a recording session.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Context
from nustd import ui
from nustd.ui import Session
from nustd.ui.core.chains import boot_chains
from nustd.ui.refs.collections.disclosure import TRIGGER
from nustd.ui.refs.collections.named import HEADER


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


_HOSTS = [
    ("CardRef", "Card"),
    ("PageSectionRef", "PageSection"),
    ("ModalRef", "Modal"),
    ("SheetRef", "Sheet"),
    ("PopoverRef", "Popover"),
]


@pytest.mark.parametrize(("name", "wire"), _HOSTS)
def test_header_is_a_row_at_the_header_key(name, wire):
    host = getattr(ui, name)("box", parent_ref=ui.ColumnRef("page"), props={"title": "Plain"})
    assert type(host.header) is ui.RowRef
    [frame] = _frames(ui.TextRef("name", parent_ref=host.header).set("web-03"))
    assert frame.ref == ("page", "box", HEADER, "name")
    assert _chain(frame) == [
        ("page", "Column"),
        ("box", wire),
        (HEADER, "Row"),
        ("name", "TextRef"),
    ]
    # The string title rides along as the shorthand; the header replaces it on screen.
    assert frame.chain[1][2]["title"] == "Plain"
    # The same row as the actions rail: a line of small parts, centred.
    assert frame.chain[2][2] == ui.CardRef("c").actions._payload["props"]


@pytest.mark.parametrize(("name", "_wire"), _HOSTS)
def test_header_is_not_a_body_key(name, _wire):
    with pytest.raises(ValueError, match=r"reach it as \.header"):
        getattr(ui, name)("box")[HEADER]


def test_a_card_shape_header_slot_wins_over_the_default_row():
    class Plan(ui.Card):
        header = ui.TextRef.slot(value="Pro plan", lines=1)
        note = ui.TextRef.slot(value="body")

    class Home(ui.Column):
        plan = Plan.slot()

    chains = [c for c in boot_chains((), Home) if c[0][0] == "plan"]
    assert [[lvl[:2] for lvl in c] for c in chains] == [
        [("plan", "Card")],
        [("plan", "Card"), (HEADER, "TextRef")],
        [("plan", "Card"), ("note", "TextRef")],
    ]
    assert type(Home.plan.header).__name__ == "TextRef"
    [frame] = _frames(Home.plan.header.set("Team plan"))
    assert frame.ref == ("plan", HEADER)


@pytest.mark.parametrize(
    "shape", [ui.PageSection, ui.Modal, ui.Sheet, ui.Popover], ids=lambda s: s.__name__
)
def test_every_shape_takes_a_header_slot(shape):
    class Boxed(shape):
        header = ui.BadgeRef.slot(label="new")

    ref = shape._ref_cls("b", section_cls=Boxed)
    assert type(ref.header).__name__ == "BadgeRef"


def test_header_sits_beside_the_actions():
    card = ui.CardRef("c")
    frames = _frames(
        ui.TextRef("t", parent_ref=card.header).set("Name")
        >> ui.ButtonRef("b", parent_ref=card.actions).set_label("Go")
    )
    assert [_chain(f)[:2] for f in frames] == [
        [("c", "Card"), (HEADER, "Row")],
        [("c", "Card"), ("actions", "Row")],
    ]


# --- the Popover's trigger -----------------------------------------------------


def test_popover_trigger_is_a_row_at_the_trigger_key():
    pop = ui.PopoverRef("who", props={"tooltip": "Account"})
    assert type(pop.trigger) is ui.RowRef
    [frame] = _frames(ui.TextRef("name", parent_ref=pop.trigger).set("Gor"))
    assert frame.ref == ("who", TRIGGER, "name")
    assert _chain(frame) == [("who", "Popover"), (TRIGGER, "Row"), ("name", "TextRef")]
    assert frame.chain[0][2]["tooltip"] == "Account"
    assert frame.chain[1][2]["gap"] == 2
    with pytest.raises(ValueError, match=r"reach it as \.trigger"):
        pop[TRIGGER]


def test_a_popover_shape_trigger_slot_wins_over_the_default_row():
    class Account(ui.Popover):
        trigger = ui.BadgeRef.slot(label="Gor")
        header = ui.TextRef.slot(value="Signed in")
        out = ui.ButtonRef.slot(label="Sign out")

    class Home(ui.Row):
        account = Account.slot(tooltip="Account")

    chains = [c for c in boot_chains((), Home) if c[0][0] == "account"]
    assert [lvl[:2] for lvl in chains[1][1:]] == [(TRIGGER, "BadgeRef")]
    assert [lvl[:2] for lvl in chains[2][1:]] == [(HEADER, "TextRef")]
    assert type(Home.account.trigger).__name__ == "BadgeRef"
    assert type(Home.account.header).__name__ == "TextRef"


def test_cards_without_a_header_seed_no_header_child():
    """The header is a child like any other: nothing lands at its key until built."""
    [frame] = _frames(ui.CardRef("c", props={"title": "T"}).set_title("U"))
    assert _chain(frame) == [("c", "Card")]
