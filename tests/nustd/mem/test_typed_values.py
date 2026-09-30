"""mem containers are typed by the value they declare.

Descent lands on the mem ref for the declared value, every value an op reads
is that value's form, and collection results carry the declared type on. The
``.slot(...)`` and annotation spellings declare the same thing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

import nu
from nu import run
from nu.domains.shape import Shape
from nu.forms import Dict, DictValues, Int, Iterator, List, Object, Str
from nu.lang import TypeInfo
from nustd.mem import (
    DecimalRef,
    DictRef,
    IntRef,
    ListRef,
    ObjectRef,
    SetRef,
    ShapeRef,
    StrRef,
)


class Row(Shape):
    sym = StrRef.slot()


class Bag(Shape):
    names = DictRef.slot(str)
    counts = DictRef.slot(int, key=int)
    prices = DictRef.slot(Decimal)
    marks = DictRef.slot(DecimalRef)
    rows = DictRef.slot(Row)
    meta = DictRef.slot(object)
    lists = DictRef.slot(list)
    tags = ListRef.slot(str)
    orders = ListRef.slot(Row)
    members = SetRef.slot(str)


class Spelled(Shape):
    names: DictRef[str, str]
    counts: DictRef[int, int]
    rows: DictRef[str, Row]
    tags: ListRef[str]
    orders: ListRef[Row]
    members: SetRef[str]


# --- descent ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("child", "ref_cls"),
    [
        (lambda: Bag.names["a"], StrRef),
        (lambda: Bag.counts[1], IntRef),
        (lambda: Bag.prices["a"], DecimalRef),
        (lambda: Bag.marks["a"], DecimalRef),
        (lambda: Bag.rows["a"], ShapeRef),
        (lambda: Bag.tags[0], StrRef),
        (lambda: Bag.orders[0], ShapeRef),
        (lambda: Bag.meta["a"], ObjectRef),
        (lambda: Bag.lists["a"], ObjectRef),
    ],
)
def test_descent_lands_on_the_ref_for_the_declared_value(child, ref_cls):
    assert type(child()) is ref_cls


def test_a_shape_child_is_bound_to_the_declared_shape(ctx):
    run(Bag.rows["r1"].sym.set("SOL"), ctx)
    run(Bag.orders.set([{"sym": "ETH"}]), ctx)
    assert run(Bag.rows["r1"].sym, ctx)[0] == "SOL"
    assert run(Bag.orders[0].sym, ctx)[0] == "ETH"


def test_a_typed_child_is_an_operand_of_its_value(ctx):
    run(Bag.names["a"].set("gor"), ctx)
    run(Bag.counts[1].set(41), ctx)
    run(Bag.prices["a"].set(Decimal("1.50")), ctx)
    assert run(Bag.names["a"].upper(), ctx)[0] == "GOR"
    assert run(Bag.counts[1] + 1, ctx)[0] == 42
    assert run(Bag.prices["a"], ctx)[0] == Decimal("1.50")


# --- value and collection results ------------------------------------------


def test_value_results_take_the_declared_value_form(ctx):
    run(Bag.names.set({"a": "gor"}), ctx)
    run(Bag.tags.set(["x", "y"]), ctx)
    assert type(Bag.names.get_item("a", "")) is Str
    assert type(Bag.counts.get_item(1, 0)) is Int
    assert type(Bag.names.pop("a")) is Str
    assert type(Bag.tags.first_elem()) is Str
    assert type(Bag.tags.pop()) is Str
    assert type(Bag.members.pop()) is Str
    assert run(Bag.names.get_item("a", "").upper(), ctx)[0] == "GOR"
    assert run(Bag.names.get_item("zz", "none").upper(), ctx)[0] == "NONE"
    assert run(Bag.tags.first_elem().upper(), ctx)[0] == "X"


def test_a_slice_is_a_list_carrying_the_element_type(ctx):
    run(Bag.tags.set(["x", "y", "z"]), ctx)
    sliced = Bag.tags[1:3]
    assert type(sliced) is List
    assert type(sliced.first_elem()) is Str
    assert run(sliced, ctx)[0] == ["y", "z"]
    assert run(sliced.first_elem().upper(), ctx)[0] == "Y"


def test_values_and_copy_carry_the_value_type(ctx):
    run(Bag.names["a"].set("gor"), ctx)
    values = Bag.names.values()
    assert type(values) is DictValues
    assert nu.tree.payload(values)["type_info"].elem == TypeInfo(str)
    assert sorted(run(values.to_list(), ctx)[0]) == ["gor"]
    copied = Bag.names.copy()
    assert type(copied) is Dict
    assert type(copied["a"]) is Str


def test_a_stream_carries_the_declared_element_type(ctx):
    run(Bag.tags.set(["x", "y"]), ctx)
    stream = Bag.tags.iter()
    assert type(stream) is Iterator
    assert type(stream.first()) is Str
    assert type(Bag.members.iter().first()) is Str
    assert run(stream.first().upper(), ctx)[0] == "X"


def test_a_mapping_stream_carries_the_declared_key_type(ctx):
    run(Bag.rows["r1"].sym.set("SOL"), ctx)
    assert type(Bag.rows.iter().first()) is Str
    assert type(Bag.counts.iter().first()) is Int
    assert run(Bag.rows.iter().first().upper(), ctx)[0] == "R1"


def test_stream_ops_keep_the_element_type_while_the_items_are_the_sources(ctx):
    run(Bag.tags.set(["x", "y"]), ctx)
    kept = Bag.tags.iter().filter(nu.Gt(nu.AttrRef("item"), "x"))
    assert type(kept.first()) is Str
    assert run(kept.first().upper(), ctx)[0] == "Y"
    drained = Bag.tags.iter().to_list()
    assert type(drained.first_elem()) is Str
    assert run(drained.first_elem().upper(), ctx)[0] == "X"
    assert nu.tree.payload(Bag.tags.iter().to_set())["type_info"].elem == TypeInfo(str)
    assert type(Bag.tags.iter().map(nu.AttrRef("item")).first()) is Object


def test_undeclared_results_are_object():
    assert type(Bag.meta.get_item("a")) is Object
    assert type(Bag.rows.get_item("a")) is Object


# --- the two spellings -----------------------------------------------------


@pytest.mark.parametrize("name", ["names", "counts", "rows", "tags", "orders", "members"])
def test_slot_and_annotation_declare_the_same_ref(name):
    by_slot, by_annotation = getattr(Bag, name), getattr(Spelled, name)
    assert type(by_slot) is type(by_annotation)
    assert nu.tree.payload(by_slot)["type_info"] == nu.tree.payload(by_annotation)["type_info"]


def test_slot_and_annotation_descend_alike():
    assert type(Bag.names["a"]) is type(Spelled.names["a"])
    assert type(Bag.rows["a"]) is type(Spelled.rows["a"])
    assert type(Bag.orders[0]) is type(Spelled.orders[0])
    assert type(Bag.names.get_item("a")) is type(Spelled.names.get_item("a"))


# --- the undeclared value --------------------------------------------------


def test_an_undeclared_value_carries_the_object_surface(ctx):
    run(Bag.meta["title"].set("hi"), ctx)
    run(Bag.meta["nested"].set({"k": [1, 2]}), ctx)
    assert run(Bag.meta["title"] == "hi", ctx)[0] is True
    assert run(Bag.meta["nested"]["k"], ctx)[0] == [1, 2]
    assert run(nu.Str(Bag.meta["title"]).upper(), ctx)[0] == "HI"


def test_a_view_is_a_kv_option_only():
    with pytest.raises(TypeError, match="view"):
        DictRef.slot(str, view=object)
