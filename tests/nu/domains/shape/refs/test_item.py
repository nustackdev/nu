"""Tests for ItemRef / MutableItemRef / ReactiveItemRef: leaf Ref hierarchy."""

from __future__ import annotations

from nu.core.reactive import OnPrimitiveChangeQuery
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    EraseCommand,
    ExistsQuery,
    MissingQuery,
    StoreCommand,
)
from nu.domains.shape.refs.base import _StructuredRef
from nu.domains.shape.refs.item import ItemRef, MutableItemRef, ReactiveItemRef


class MyShape(Shape):
    pass


def test_item_ref_is_structured_ref():
    assert issubclass(ItemRef, _StructuredRef)


def test_item_ref_constructs_with_address():
    ref = ItemRef("field_name")
    assert ref.children  # address stored as children[0]


def test_item_ref_parent_ref_none_by_default():
    ref = ItemRef("slot")
    assert ref.parent_ref is None


def test_item_ref_stores_owner_shape():
    ref = ItemRef("slot", owner_shape=MyShape)
    assert ref.owner_shape is MyShape


def test_item_ref_stores_parent_ref():
    parent = ItemRef("parent")
    child = ItemRef("child", parent_ref=parent)
    assert child.parent_ref is parent
    assert child.get_root_shape() is None  # parent has no owner_shape


def test_item_ref_root_shape_from_parent():
    parent = ItemRef("root", owner_shape=MyShape)
    child = ItemRef("leaf", parent_ref=parent)
    assert child.get_root_shape() is MyShape


# ---------------------------------------------------------------------------
# ItemRef tier — Form surface (exists / missing)
# ---------------------------------------------------------------------------


def test_item_ref_exists_returns_exists_query():
    ref = ItemRef("field")
    result = ref.exists()
    assert isinstance(result, ExistsQuery)


def test_item_ref_missing_returns_missing_query():
    ref = ItemRef("field")
    result = ref.missing()
    assert isinstance(result, MissingQuery)


# ---------------------------------------------------------------------------
# MutableItemRef tier
# ---------------------------------------------------------------------------


def test_mutable_item_ref_is_subclass_of_item_ref():
    assert issubclass(MutableItemRef, ItemRef)


def test_mutable_item_ref_constructs():
    ref = MutableItemRef("field")
    assert ref.children


def test_mutable_item_ref_has_store():
    ref = MutableItemRef("field")
    assert hasattr(ref, "store")


def test_mutable_item_ref_store_returns_store_command():
    ref = MutableItemRef("field")
    result = ref.store(42)
    assert isinstance(result, StoreCommand)


def test_mutable_item_ref_has_erase():
    ref = MutableItemRef("field")
    assert hasattr(ref, "erase")


def test_mutable_item_ref_erase_returns_erase_command():
    ref = MutableItemRef("field")
    result = ref.erase()
    assert isinstance(result, EraseCommand)


def test_mutable_item_ref_inherits_exists_missing():
    ref = MutableItemRef("field")
    assert isinstance(ref.exists(), ExistsQuery)
    assert isinstance(ref.missing(), MissingQuery)


# ---------------------------------------------------------------------------
# ReactiveItemRef tier
# ---------------------------------------------------------------------------


def test_reactive_item_ref_is_subclass_of_mutable_item_ref():
    assert issubclass(ReactiveItemRef, MutableItemRef)


def test_reactive_item_ref_constructs():
    ref = ReactiveItemRef("field")
    assert ref.children


def test_reactive_item_ref_has_on_change():
    ref = ReactiveItemRef("field")
    assert hasattr(ref, "on_change")


def test_reactive_item_ref_on_change_returns_on_primitive_change_query():
    # v1 parity: on_change() on a leaf subscribes on the PARENT's child-change
    # channel for this item's address. In v2 this is expressed as a
    # substrate-uniform OnPrimitiveChangeQuery -- the query carries the leaf
    # ref (slot 0) and resolves parent + address at runtime.
    ref = ReactiveItemRef("field")
    result = ref.on_change()
    assert isinstance(result, OnPrimitiveChangeQuery)


def test_reactive_item_ref_on_change_carries_self_as_slot_zero():
    ref = ReactiveItemRef("field")
    result = ref.on_change()
    # OnPrimitiveChangeQuery carries the leaf ref as its sole child; at runtime
    # ``ref.afetch_parent`` + ``ref.aaddress`` reconstruct the parent view and
    # address, regardless of whether ``parent_ref`` is wired.
    assert len(result.children) == 1
    assert result.children[0] is ref


def test_reactive_item_ref_inherits_store_erase():
    ref = ReactiveItemRef("field")
    assert isinstance(ref.store("v"), StoreCommand)
    assert isinstance(ref.erase(), EraseCommand)


def test_reactive_item_ref_parent_chain_works():
    parent = ReactiveItemRef("root", owner_shape=MyShape)
    child = ReactiveItemRef("leaf", parent_ref=parent)
    assert child.parent_ref is parent
    assert child.get_root_shape() is MyShape
