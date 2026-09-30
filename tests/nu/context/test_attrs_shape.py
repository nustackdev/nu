"""Tests for attrs refs as Shape slots: a Shape declaring top-level attr names.

``Attrs.plane`` is exactly the attrs ref for the name ``plane``, so ``Let``,
``.set()`` and ``.exists()`` take it like any attrs ref. Attrs are flat: a
Shape holding attrs slots holds nothing else and never nests.
"""

from __future__ import annotations

import pytest

import nu
import nustd.mem as nm
from nu.context import BoolRef, IntRef, Let, ObjectRef, StrRef, TupleRef
from nu.lang import Literal
from nu.lang.helpers import arun, run


class Attrs(nu.Shape):
    plane = StrRef.slot()
    count = IntRef.slot()
    pair = TupleRef.slot()
    ui: BoolRef
    anything: ObjectRef


def _name(ref: object) -> object:
    """The literal name an attrs ref addresses."""
    (address,) = ref._children  # type: ignore[attr-defined]
    return address._payload["value"]


# --- slot access: the right ref type, named after the slot ------------------


@pytest.mark.parametrize(
    ("ref", "ref_cls", "name"),
    [
        (Attrs.plane, StrRef, "plane"),
        (Attrs.count, IntRef, "count"),
        (Attrs.pair, TupleRef, "pair"),
        (Attrs.ui, BoolRef, "ui"),
        (Attrs.anything, ObjectRef, "anything"),
    ],
)
def test_slot_is_the_attrs_ref_for_its_name(ref, ref_cls, name):
    assert type(ref) is ref_cls
    assert _name(ref) == name
    assert ref._payload == ref_cls(name)._payload


def test_slot_reads_what_a_plain_ref_declared():
    value, _ = run(Let(StrRef("plane"), Literal("p1"), Attrs.plane.upper()))
    assert value == "P1"


def test_subclass_inherits_the_names():
    class More(Attrs):
        cell = StrRef.slot()

    assert _name(More.plane) == "plane"
    assert _name(More.cell) == "cell"


# --- Let / set / exists through shape slots ---------------------------------


def test_let_set_exists_through_slots(capsys):
    tree = Let(
        Attrs.count,
        Literal(1),
        Attrs.count.set(Attrs.count + 1)
        >> nu.print(IntRef("count"))
        >> nu.print(Attrs.count.exists()),
    )
    _, ctx = run(tree)
    assert capsys.readouterr().out.split() == ["2", "True"]
    assert "count" not in ctx.attrs
    assert run(Attrs.count.exists())[0] is False


def test_set_through_a_slot_on_an_undeclared_name_raises():
    with pytest.raises(Exception, match="count"):
        run(Attrs.count.set(1))


async def test_let_set_exists_through_slots_async():
    value, ctx = await arun(Let(Attrs.count, Literal(1), Attrs.count + 1))
    assert value == 2
    assert "count" not in ctx.attrs
    assert (await arun(Let(Attrs.ui, Literal(True), Attrs.ui.exists())))[0] is True
    assert (await arun(Attrs.ui.exists()))[0] is False


# --- refusals: attrs shapes are flat -----------------------------------------


def test_mixing_attrs_slots_with_a_collection_is_refused():
    with pytest.raises(TypeError, match="top-level names"):

        class Mixed(nu.Shape):
            plane = StrRef.slot()
            items = nm.ListRef.slot(int)


def test_mixing_attrs_slots_with_another_fabric_leaf_is_refused():
    with pytest.raises(TypeError, match="top-level names"):

        class Mixed(nu.Shape):
            plane = StrRef.slot()
            name: nm.StrRef


def test_mixing_attrs_slots_with_a_nested_shape_is_refused():
    class Inner(nu.Shape):
        name: nm.StrRef

    with pytest.raises(TypeError, match="top-level names"):

        class Mixed(nu.Shape):
            plane = StrRef.slot()
            inner = nm.ShapeRef.slot(Inner)


def test_adding_other_slots_by_inheritance_is_refused():
    with pytest.raises(TypeError, match="top-level names"):

        class Mixed(Attrs):
            name: nm.StrRef


def test_an_attrs_shape_never_nests_under_another_shape():
    class Outer(nu.Shape):
        attrs = nm.ShapeRef.slot(Attrs)

    with pytest.raises(TypeError, match="cannot nest"):
        _ = Outer.attrs.plane
