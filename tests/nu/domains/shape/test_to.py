"""``ItemRef.to``: the same address, read as another kind, so the chain goes on in it."""

from __future__ import annotations

import pytest

import nu
from nu.domains.shape import ItemRef, Slot, with_parent


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
    assert nu.tree.payload(nu.tree.children(as_int)[1]) == {"value": "a"}
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
    assert as_dict._payload["type_info"] is spec._resolve_type_info()
    assert type(as_dict["k"]) is nu.IntRef


def test_to_drops_the_old_kind_declaration():
    item = State.anything["a"]
    assert "type_info" in item._payload
    assert "type_info" not in item.to(nu.IntRef)._payload


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
