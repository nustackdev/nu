"""``.to``: the same address, read as another kind, so the chain goes on in it."""

from __future__ import annotations

import pytest

import nu
from nu.domains.shape import ItemRef, Slot, StructuredRef, with_parent


class Order(nu.Shape):
    qty = nu.IntRef.slot()


class State(nu.Shape):
    anything = nu.DictRef.slot(object)
    orders = nu.DictRef.slot(Order)


def test_to_a_bare_class_keeps_parent_and_address():
    item = State.anything["a"]
    as_int = item.to(nu.IntRef)
    assert type(as_int) is nu.IntRef
    assert as_int._parent is item._parent
    assert nu.tree.fields(nu.tree.children(as_int)[1]) == {"value": "a"}
    assert as_int._owner_shape is item._owner_shape
    assert as_int._root_shape is State


def test_to_keeps_a_computed_address_as_is():
    key = nu.Str("a") + "b"
    item = State.anything[key]
    assert nu.tree.children(item.to(nu.IntRef))[1] is nu.tree.children(item)[1]


def test_to_a_slot_spec_carries_its_declaration():
    spec = nu.DictRef.slot(int)
    as_dict = State.anything["a"].to(spec)
    assert type(as_dict) is nu.DictRef
    assert as_dict._type_info is spec._resolve_type_info()
    assert type(as_dict["k"]) is nu.IntRef


def test_to_drops_the_old_kind_declaration():
    item = State.anything["a"]
    assert item._type_info is not None
    assert item.to(nu.IntRef)._type_info is None


def test_to_leaves_the_spec_reusable():
    spec = nu.IntRef.slot()
    first = State.anything["a"].to(spec)
    second = State.anything["b"].to(spec)
    assert spec.name is None
    assert first is not second


def test_to_a_shape_spec_continues_into_its_slots():
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State)
    order = State.anything["o"].to(nu.ShapeRef.slot(Order))
    nu.run(order.qty.set(2), ctx)
    assert store == {"anything": {"o": {"qty": 2}}}


def test_to_writes_land_at_the_same_address():
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State)
    nu.run(State.anything["a"].to(nu.IntRef).set(3), ctx)
    assert store == {"anything": {"a": 3}}
    assert nu.run(State.anything["a"].to(nu.IntRef) + 1, ctx)[0] == 4


def test_to_chains_after_to():
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State)
    deep = State.anything["a"].to(nu.DictRef.slot(object))["b"].to(nu.DictRef.slot(int))["c"]
    nu.run(deep.set(1), ctx)
    assert store == {"anything": {"a": {"b": {"c": 1}}}}


def test_to_keeps_a_placed_chain_placed():
    placed = with_parent(Order.qty, State.orders["x"])
    as_str = placed.to(nu.StrRef)
    assert as_str._root_shape is State
    with pytest.raises(ValueError, match="already has a parent"):
        with_parent(as_str, State.orders["y"])


@pytest.mark.parametrize("spec", [Order, nu.IntRef.slot, 3, "IntRef"])
def test_to_refuses_anything_but_a_ref_class_or_slot(spec):
    with pytest.raises(TypeError, match=r"to takes a ref class or a Kind\.slot"):
        State.anything["a"].to(spec)


def test_to_is_on_every_item_ref():
    assert isinstance(State.anything["a"], ItemRef)
    assert isinstance(nu.IntRef.slot(), Slot)


# --- containers ---------------------------------------------------------------


def test_to_is_on_every_structured_ref():
    assert not isinstance(State.anything, ItemRef)
    assert isinstance(State.anything, StructuredRef)
    assert StructuredRef.to is ItemRef.to


def test_to_on_a_container_keeps_parent_and_address():
    as_dict = State.anything["a"].to(nu.DictRef.slot(object))
    as_int = as_dict.to(nu.IntRef)
    assert type(as_int) is nu.IntRef
    assert as_int._parent is as_dict._parent
    assert nu.tree.fields(nu.tree.children(as_int)[1]) == {"value": "a"}
    assert as_int._root_shape is State


def test_to_rekinds_a_container_again():
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State)
    nu.run(State.anything["a"].to(nu.DictRef.slot(object)).to(nu.IntRef).set(5), ctx)
    assert store == {"anything": {"a": 5}}


@pytest.mark.parametrize(
    "spec", [nu.ListRef.slot(int), nu.SetRef.slot(int), nu.ShapeRef.slot(Order)]
)
def test_to_from_every_container_kind(spec):
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State)
    nu.run(State.anything["a"].to(spec).to(nu.StrRef).set("x"), ctx)
    assert store == {"anything": {"a": "x"}}


def test_to_on_a_declared_container_slot():
    store: dict = {"anything": {"a": 1}}
    ctx = nu.Context().bind(dict, store, State)
    as_shape = State.anything.to(nu.ShapeRef.slot(Order))
    assert type(as_shape) is nu.ShapeRef
    nu.run(as_shape.qty.set(2), ctx)
    assert store == {"anything": {"a": 1, "qty": 2}}


def test_to_on_a_shape_ref_slot():
    store: dict = {}
    ctx = nu.Context().bind(dict, store, State)
    order = State.orders["x"]
    assert isinstance(order, nu.ShapeRef)
    nu.run(order.to(nu.DictRef.slot(int))["n"].set(3), ctx)
    assert store == {"orders": {"x": {"n": 3}}}


def test_to_on_a_let_slot_after_a_container_kind(capsys):
    body = lambda x: x.to(nu.DictRef).to(nu.IntRef).set(12) >> nu.print(x)  # noqa: E731
    nu.run(nu.let(body, x={}))
    assert capsys.readouterr().out == "12\n"


def test_a_slot_named_to_is_refused():
    with pytest.raises(TypeError, match="slot 'to' clashes"):

        class Bad(nu.Shape):
            to = nu.IntRef.slot()
