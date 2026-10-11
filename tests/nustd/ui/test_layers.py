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


# --- the kit: container Refs built alone ------------------------------------


def test_row_alone_under_card_alone():
    from nustd.ui.refs import CardRef, RowRef, TextRef

    card = CardRef("card", props={"title": "Hosts"})
    row = RowRef("r", parent_ref=card, props={"wrap": True})
    [frame] = _frames(TextRef("t", parent_ref=row).set("hi"))
    assert _chain(frame) == [("card", "Card"), ("r", "Row"), ("t", "TextRef")]
    assert frame.chain[0][2] == {"title": "Hosts", "subtitle": "", "footer": ""}
    assert frame.chain[1][2] == {
        "gap": 4,
        "align": "center",
        "justify": "start",
        "wrap": True,
        "padding": 0,
    }


def test_every_former_bare_section_has_its_own_ref():
    from nustd.ui.core.base import _level_type
    from nustd.ui.refs import BoxRef, ColumnRef, FormRef, RowRef

    for ref_cls, wire in ((ColumnRef, "Column"), (RowRef, "Row"), (BoxRef, "Container")):
        assert _level_type(ref_cls("x")) == wire
    assert _level_type(FormRef("x")) == "Form"


def test_kit_leaf_as_parent_raises():
    from nustd.ui.refs import ButtonRef, TableRef, TextRef

    with pytest.raises(TypeError, match=r"TextRef is a leaf and holds no children; put 'x'"):
        TextRef("x", parent_ref=TextRef("t"))
    with pytest.raises(TypeError, match="TableRef is a leaf"):
        ButtonRef("b", parent_ref=TableRef("tbl"))


def test_kit_container_with_no_shape_has_no_slots():
    from nustd.ui.refs import RowRef

    with pytest.raises(AttributeError, match="carries no Shape"):
        _ = RowRef("r").label


def test_shape_slot_props_equal_the_refs():
    from nustd.ui import Accordion, AccordionRef, Card, CardRef, Row, RowRef

    assert Row.slot().props == RowRef.slot().props
    assert Row.slot(wrap=True).props == RowRef.slot(wrap=True).props
    assert Card.slot(title="t").props == CardRef.slot(title="t").props
    sections = [{"id": 1, "label": None}]
    assert Accordion.slot(sections=sections).props == AccordionRef.slot(sections=sections).props
    assert Accordion.slot(sections=sections).props["sections"] == [{"id": "1", "label": ""}]


def test_kit_wire_types_of_shapes():
    from nustd.ui import Card, Container, Form, List, Row

    class Toolbar(Row):
        pass

    assert _wire_type_of(Row) == "Row"
    assert _wire_type_of(Toolbar) == "Row"
    assert _wire_type_of(Card) == "Card"
    assert _wire_type_of(Container) == "Container"
    assert _wire_type_of(Form) == "Form"
    assert _wire_type_of(List) == "ListRef"


def test_kit_computed_keys_resolve_distinct_paths():
    from nustd.ui.refs import ColumnRef, RowRef, TextRef

    col = ColumnRef("col")
    writes = [
        TextRef("t", parent_ref=RowRef(nu.Str("r") + nu.str(i), parent_ref=col)).set("x")
        for i in range(3)
    ]
    frames = _frames(writes[0] >> writes[1] >> writes[2])
    assert [f.ref for f in frames] == [("col", f"r{i}", "t") for i in range(3)]
    assert {tuple(_chain(f)[1]) for f in frames} == {("r0", "Row"), ("r1", "Row"), ("r2", "Row")}


def test_kit_boot_chains_of_a_page():
    from nustd.ui import BadgeRef, Card, List, ListRef, Row, RowRef, TextRef
    from nustd.ui.nudle import Page

    class Bar(Row):
        a = TextRef.slot()

    class Box(Card):
        b = TextRef.slot()

    class Tags(List):
        c = BadgeRef.slot(label="x")

    class Home(Page):
        bar = Bar.slot()
        box = Box.slot(title="T")
        tags = Tags.slot(items=["s"])
        names = ListRef.slot(items=["n"])
        free = RowRef.slot(wrap=True)

    chains = Home._boot_chains()
    assert [[lvl[:2] for lvl in c] for c in chains] == [
        [("bar", "Row")],
        [("bar", "Row"), ("a", "TextRef")],
        [("box", "Card")],
        [("box", "Card"), ("b", "TextRef")],
        [("tags", "ListRef")],
        [("tags", "ListRef"), ("c", "BadgeRef")],
        [("names", "ListRef")],
        [("free", "Row")],
    ]
    assert chains[2][0][2]["title"] == "T"
    assert chains[4][0][2] == {"items": ["s"], "variant": "bullet", "start": 1}
    assert chains[7][0][2]["wrap"] is True


def test_list_takes_any_node_as_an_item():
    from nustd.ui import BadgeRef, LinkRef, ListRef

    names = ListRef("names", props={"items": ["first"]})
    frames = _frames(
        names.append("second")
        >> BadgeRef("b", parent_ref=names).set("live")
        >> LinkRef("l", parent_ref=names).set("/docs", label="Docs")
    )
    assert frames[0].payload == "second"
    assert [_chain(f) for f in frames[1:]] == [
        [("names", "ListRef"), ("b", "BadgeRef")],
        [("names", "ListRef"), ("l", "LinkRef")],
    ]
    assert frames[1].chain[0][2] == {"items": ["first"], "variant": "bullet", "start": 1}


# --- every Ref sits under the right base ------------------------------------


def _ref_classes_under(package: str) -> list[type]:
    import importlib
    import inspect
    import pkgutil

    pkg = importlib.import_module(package)
    out = []
    for info in pkgutil.walk_packages(pkg.__path__, package + "."):
        mod = importlib.import_module(info.name)
        out.extend(
            cls
            for _, cls in inspect.getmembers(mod, inspect.isclass)
            if issubclass(cls, Ref) and cls.__module__ == mod.__name__
        )
    return out


def test_every_ref_under_leaves_is_a_leaf():
    leaves = _ref_classes_under("nustd.ui.refs.leaves")
    assert len(leaves) >= 35
    assert [c.__name__ for c in leaves if not issubclass(c, LeafRef)] == []


def test_every_ref_under_containers_is_a_container():
    containers = _ref_classes_under("nustd.ui.refs.containers")
    assert len(containers) >= 9
    assert [c.__name__ for c in containers if not issubclass(c, ContainerRef)] == []


def test_structural_and_lens_refs_are_leaves():
    from nustd.ui.lens import LensRef
    from nustd.ui.refs import NavRef, TitleRef

    assert issubclass(NavRef, LeafRef)
    assert issubclass(TitleRef, LeafRef)
    assert issubclass(LensRef, LeafRef)


# --- back-compat: every name importable on main still is ---------------------

_UI_ALL_ON_MAIN = (
    "Accordion AccordionRef AlertRef Append AreaChart BadgeRef BarChart Boot ButtonRef Card "
    "CardRef Changed CheckboxRef CodeRef Column Container DatePickerRef DividerRef "
    "EmptyStateRef Field FieldRef Fieldset FieldsetRef Form Frame GaugeRef HeadingRef "
    "ImageRef Index InputRef InsertRow JsonViewerRef KbdRef LineChart LinkRef ListRef "
    "MarkdownRef Modal ModalRef NavRef NumberInputRef Page PageRef PieChart ProgressRef "
    "RadioGroupRef Ref Remove RemoveRows Row Section SectionRef SelectRef Send Session "
    "SetOrder SetRow ShortcutRef SliderRef Sparkline StatRef StatusDotRef Subscription "
    "SwitchRef TableRef Tabs TabsRef TagInputRef TextAreaRef TextRef TitleRef TreeRef Write "
    "WsSession core lens nudle refs serve table"
).split()

_REFS_ALL_ON_MAIN = (
    "Accordion AccordionRef AlertRef AreaChart BadgeRef BarChart ButtonRef Card CardRef "
    "CheckboxRef CodeRef Column Container DatePickerRef DividerRef EmptyStateRef Field "
    "FieldRef Fieldset FieldsetRef Form GaugeRef HeadingRef ImageRef InputRef InsertRow "
    "JsonViewerRef KbdRef LineChart LinkRef ListRef MarkdownRef Modal ModalRef NavRef "
    "NumberInputRef PieChart ProgressRef RadioGroupRef Ref RemoveRows Row Section SectionRef "
    "SelectRef SetOrder SetRow ShortcutRef SliderRef Sparkline StatRef StatusDotRef SwitchRef "
    "TableRef Tabs TabsRef TagInputRef TextAreaRef TextRef TitleRef TreeRef"
).split()

_CORE_ALL_ON_MAIN = (
    "EVENT OP_ERROR OP_INIT OP_NOTIFY OP_READ OP_REMOVE OP_WRITE Append Chain Changed Frame "
    "Ref Remove Section SectionRef Send Session Subscription Write WsSession WsSubscription "
    "boot_chains decode encode"
).split()


@pytest.mark.parametrize(
    ("module", "names"),
    [
        ("nustd.ui", _UI_ALL_ON_MAIN),
        ("nustd.ui.refs", _REFS_ALL_ON_MAIN),
        ("nustd.ui.core", _CORE_ALL_ON_MAIN),
    ],
)
def test_every_name_on_main_still_imports(module, names):
    import importlib

    mod = importlib.import_module(module)
    assert [n for n in names if not hasattr(mod, n)] == []
    assert [n for n in names if n not in mod.__all__] == []
    # Sorted the way ruff sorts it: CONSTANTS, then Classes, then modules.
    order = sorted(mod.__all__, key=lambda n: (0 if n.isupper() else 1 if n[0].isupper() else 2, n))
    assert mod.__all__ == order


def test_core_all_is_unchanged():
    import nustd.ui.core

    assert sorted(nustd.ui.core.__all__) == sorted(_CORE_ALL_ON_MAIN)


def test_old_submodule_paths_still_import():
    import nustd.ui
    from nustd.ui.refs.chart import LineChart
    from nustd.ui.refs.input import ButtonRef
    from nustd.ui.refs.layout import AccordionRef, Row
    from nustd.ui.refs.output import ListRef, TableRef
    from nustd.ui.refs.tree import TreeRef

    assert Row is nustd.ui.Row
    assert AccordionRef is nustd.ui.AccordionRef
    for cls in (LineChart, ButtonRef, ListRef, TableRef, TreeRef):
        assert getattr(nustd.ui, cls.__name__) is cls


def test_section_ref_with_a_shape_keeps_its_shapes_wire_type():
    import nustd.ui
    from nustd.ui.core.base import _level_type
    from nustd.ui.refs.layout import AccordionRef

    assert _level_type(AccordionRef("o", section_cls=nustd.ui.Accordion)) == "Accordion"
    assert _level_type(SectionRef("c", section_cls=nustd.ui.Column)) == "Column"
