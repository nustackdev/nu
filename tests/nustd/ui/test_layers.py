"""The two layers: Refs express any UI alone, Shapes are a DSL on top.

Layer 1 is the Refs. A container Ref built alone (``RowRef("r",
parent_ref=card)``) is a whole container: it carries its props through
``props=``, its wire type is its own, and its children are Refs built with
``parent_ref=`` it. A leaf never has children.

Layer 2 is the Shapes. A Section points ``_ref_cls`` at its container Ref,
forwards slot props to it and takes its wire type from it, so a Shape and
the Ref it stands for put the same thing on the wire.

Runs against a recording session, same harness as test_ref_composition.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

import pytest
from typing_extensions import Self

import nu
from nu import Context
from nustd.ui import Session
from nustd.ui.core import Ref, Section, SectionRef
from nustd.ui.core.base import _wire_type_of
from nustd.ui.core.chains import boot_chains
from nustd.ui.refs import ContainerRef, LeafRef


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


# --- local stand-ins, so the core rules are pinned apart from the kit -------


class _BoxRef(ContainerRef):
    _wire_type: ClassVar[str] = "Box"

    @classmethod
    def slot(cls, *, gap: int = 4, tone: str = "plain") -> Self:
        return super().slot(gap=int(gap), tone=tone)


class _Box(Section):
    _ref_cls = _BoxRef


class _NoteRef(LeafRef):
    _wire_type: ClassVar[str] = "Note"

    @classmethod
    def slot(cls, *, value: str = "") -> Self:
        return super().slot(value=value)

    def set(self, value: nu.StrArg) -> nu.Nu:
        from nustd.ui.core import Write

        return Write(self, value)


# --- props= ------------------------------------------------------------------


def test_props_go_through_the_refs_own_slot():
    box = _BoxRef("b", props={"gap": "2"})
    assert box._payload["props"] == {"gap": 2, "tone": "plain"}


def test_no_props_leaves_the_payload_alone():
    assert "props" not in _BoxRef("b")._payload


def test_unknown_prop_is_refused_by_the_slot_signature():
    with pytest.raises(TypeError):
        _BoxRef("b", props={"nope": 1})


def test_ref_built_alone_writes_its_props_on_the_chain():
    outer = _BoxRef("outer")
    inner = _BoxRef("inner", parent_ref=outer, props={"tone": "loud"})
    note = _NoteRef("n", parent_ref=inner)
    [frame] = _frames(note.set("hi"))
    assert _chain(frame) == [("outer", "Box"), ("inner", "Box"), ("n", "Note")]
    assert frame.chain[1][2] == {"gap": 4, "tone": "loud"}
    assert frame.payload == "hi"


# --- leaves hold no children -------------------------------------------------


def test_leaf_as_parent_raises():
    with pytest.raises(TypeError, match=r"_NoteRef is a leaf .* put 'x' in a container"):
        _NoteRef("x", parent_ref=_NoteRef("n"))


def test_leaf_as_parent_names_a_computed_address():
    with pytest.raises(TypeError, match="is a leaf"):
        _NoteRef(nu.Str("x") + nu.str(1), parent_ref=_NoteRef("n"))


def test_section_ref_and_plain_ref_still_take_children():
    class _HostRef(Ref):
        pass

    SectionRef("s", parent_ref=_HostRef("h"))
    _NoteRef("n", parent_ref=_HostRef("h"))
    _NoteRef("n", parent_ref=SectionRef("s"))
    _NoteRef("n", parent_ref=_BoxRef("b"))


# --- a container with no Shape ----------------------------------------------


def test_container_with_no_shape_has_no_slots():
    with pytest.raises(AttributeError, match="carries no Shape"):
        _ = _BoxRef("b").child


def test_container_with_no_shape_reports_its_own_wire_type():
    [frame] = _frames(_NoteRef("n", parent_ref=_BoxRef("b")).set("x"))
    assert _chain(frame) == [("b", "Box"), ("n", "Note")]


# --- Section.slot forwards ---------------------------------------------------


def test_section_slot_forwards_to_the_ref():
    assert _Box.slot(gap=2).props == _BoxRef.slot(gap=2).props == {"gap": 2, "tone": "plain"}
    assert _Box.slot().kwargs["section_cls"] is _Box
    assert _Box.slot().ref_cls is _BoxRef


# --- wire types --------------------------------------------------------------


def test_wire_type_of_a_shape_comes_from_its_ref():
    class Fancy(Section):
        pass

    class MyBox(_Box):
        pass

    assert _wire_type_of(_Box) == "Box"
    assert _wire_type_of(MyBox) == "Box"
    assert _wire_type_of(Fancy) == "Fancy"


def test_wire_type_of_page_is_page():
    from nustd.ui.nudle import Page

    class Home(Page):
        pass

    assert _wire_type_of(Page) == "Page"
    assert _wire_type_of(Home) == "Page"


# --- computed keys -----------------------------------------------------------


def test_computed_keys_under_one_parent_are_distinct_children():
    box = _BoxRef("col")
    writes = [_NoteRef(nu.Str("r") + nu.str(i), parent_ref=box).set("x") for i in range(3)]
    frames = _frames(writes[0] >> writes[1] >> writes[2])
    assert [f.ref for f in frames] == [("col", "r0"), ("col", "r1"), ("col", "r2")]


# --- boot chains -------------------------------------------------------------


def test_boot_chains_emit_a_direct_container_ref_without_descending():
    class Holder(Section):
        box = _Box.slot()
        bare = _BoxRef.slot(gap=1)
        note = _NoteRef.slot()

    class Inner(_Box):
        note = _NoteRef.slot()

    class Outer(Section):
        inner = Inner.slot()
        bare = _BoxRef.slot()

    assert boot_chains((), Holder) == [
        (("box", "Box", {"gap": 4, "tone": "plain"}),),
        (("bare", "Box", {"gap": 1, "tone": "plain"}),),
        (("note", "Note", {"value": ""}),),
    ]
    assert [[lvl[:2] for lvl in c] for c in boot_chains((), Outer)] == [
        [("inner", "Box")],
        [("inner", "Box"), ("note", "Note")],
        [("bare", "Box")],
    ]
