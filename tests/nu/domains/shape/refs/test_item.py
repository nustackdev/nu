"""Tests for ItemRef / MutableItemRef / ReactiveItemRef: leaf Ref hierarchy."""

from __future__ import annotations

from nu.core.reactive import OnPrimitiveChange
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    Missing,
    SetCmd,
)
from nu.domains.shape.refs.base import StructuredRef
from nu.domains.shape.refs.item import ItemRef, MutableItemRef, ReactiveItemRef


class MyShape(Shape):
    pass


def test_item_ref_is_structured_ref():
    assert issubclass(ItemRef, StructuredRef)


def test_item_ref_constructs_with_address():
    ref = ItemRef("field_name")
    assert ref._children  # address stored as children[0]


def test_item_ref_parent_ref_none_by_default():
    ref = ItemRef("slot")
    assert ref._parent is None


def test_item_ref_stores_owner_shape():
    ref = ItemRef("slot", owner_shape=MyShape)
    assert ref._owner_shape is MyShape


def test_item_ref_stores_parent_ref():
    parent = ItemRef("parent")
    child = ItemRef("child", parent_ref=parent)
    assert child._parent is parent
    assert child._root_shape is None  # parent has no owner_shape


def test_item_ref_root_shape_from_parent():
    parent = ItemRef("root", owner_shape=MyShape)
    child = ItemRef("leaf", parent_ref=parent)
    assert child._root_shape is MyShape


# ---------------------------------------------------------------------------
# ItemRef tier — Form surface (exists / missing)
# ---------------------------------------------------------------------------


def test_item_ref_exists_returns_exists_query():
    ref = ItemRef("field")
    result = ref.exists()
    assert isinstance(result, Exists)


def test_item_ref_missing_returns_missing_query():
    ref = ItemRef("field")
    result = ref.missing()
    assert isinstance(result, Missing)


# ---------------------------------------------------------------------------
# MutableItemRef tier
# ---------------------------------------------------------------------------


def test_mutable_item_ref_is_subclass_of_item_ref():
    assert issubclass(MutableItemRef, ItemRef)


def test_mutable_item_ref_constructs():
    ref = MutableItemRef("field")
    assert ref._children


def test_mutable_item_ref_has_set():
    ref = MutableItemRef("field")
    assert hasattr(ref, "set")


def test_mutable_item_ref_set_returns_set_command():
    ref = MutableItemRef("field")
    result = ref.set(42)
    assert isinstance(result, SetCmd)


def test_mutable_item_ref_has_erase():
    ref = MutableItemRef("field")
    assert hasattr(ref, "erase")


def test_mutable_item_ref_erase_returns_erase_command():
    ref = MutableItemRef("field")
    result = ref.erase()
    assert isinstance(result, Erase)


def test_mutable_item_ref_inherits_exists_missing():
    ref = MutableItemRef("field")
    assert isinstance(ref.exists(), Exists)
    assert isinstance(ref.missing(), Missing)


# ---------------------------------------------------------------------------
# ReactiveItemRef tier
# ---------------------------------------------------------------------------


def test_reactive_item_ref_is_subclass_of_mutable_item_ref():
    assert issubclass(ReactiveItemRef, MutableItemRef)


def test_reactive_item_ref_constructs():
    ref = ReactiveItemRef("field")
    assert ref._children


def test_reactive_item_ref_has_on_change():
    ref = ReactiveItemRef("field")
    assert hasattr(ref, "on_change")


def test_reactive_item_ref_on_change_returns_on_primitive_change_query():
    # v1 parity: on_change() on a leaf subscribes on the PARENT's child-change
    # channel for this item's address. In v2 this is expressed as a
    # substrate-uniform OnPrimitiveChange -- the query carries the leaf
    # ref (slot 0) and resolves parent + address at runtime.
    ref = ReactiveItemRef("field")
    result = ref.on_change()
    assert isinstance(result, OnPrimitiveChange)


def test_reactive_item_ref_on_change_carries_self_as_slot_zero():
    ref = ReactiveItemRef("field")
    result = ref.on_change()
    # OnPrimitiveChange carries the leaf ref as its sole child; at runtime
    # ``ref._afetch_parent`` + ``ref._aaddress`` reconstruct the parent view and
    # address, regardless of whether ``parent_ref`` is wired.
    assert len(result._children) == 1
    assert result._children[0] is ref


def test_reactive_item_ref_inherits_set_erase():
    ref = ReactiveItemRef("field")
    assert isinstance(ref.set("v"), SetCmd)
    assert isinstance(ref.erase(), Erase)


def test_reactive_item_ref_parent_chain_works():
    parent = ReactiveItemRef("root", owner_shape=MyShape)
    child = ReactiveItemRef("leaf", parent_ref=parent)
    assert child._parent is parent
    assert child._root_shape is MyShape
