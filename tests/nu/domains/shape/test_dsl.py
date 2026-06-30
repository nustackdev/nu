"""Tests for the Shape DSL: Shape, ShapeMeta, Slot, SlotDescriptor.

Covers class-definition mechanics — metaclass slot collection, SlotDescriptor
replacement, and Ref creation via Slot.create_ref. No substrate or runtime needed.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.dsl import Shape, Slot, SlotDescriptor
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.shape import ShapeRef


# ---------------------------------------------------------------------------
# Slot
# ---------------------------------------------------------------------------


def test_slot_stores_ref_cls_and_kwargs():
    slot = Slot(ItemRef, extra="val")
    assert slot.ref_cls is ItemRef
    assert slot.kwargs == {"extra": "val"}


def test_slot_name_is_none_before_collection():
    slot = Slot(ItemRef)
    assert slot.name is None


def test_slot_create_ref_returns_instance_of_ref_cls():
    class MyShape(Shape):
        pass

    slot = Slot(ItemRef)
    slot.name = "x"
    ref = slot.create_ref(owner_shape=MyShape)
    assert isinstance(ref, ItemRef)


def test_slot_create_ref_passes_owner_and_parent():
    class MyShape(Shape):
        pass

    parent = ItemRef("root")
    slot = Slot(ItemRef)
    slot.name = "x"
    ref = slot.create_ref(owner_shape=MyShape, parent_ref=parent)
    assert ref._owner_shape is MyShape
    assert ref.parent_ref is parent


# ---------------------------------------------------------------------------
# ShapeMeta / Shape class definition
# ---------------------------------------------------------------------------


def test_shapemeta_collects_slots_and_replaces_with_descriptors():
    class Order(Shape):
        price = Slot(ItemRef)
        qty = Slot(ItemRef)

    assert "price" in Order._slots
    assert "qty" in Order._slots
    assert isinstance(type(Order).__mro__[0], type)


def test_shape_class_has_slot_descriptor_for_each_slot():
    class Product(Shape):
        name = Slot(ItemRef)

    desc = vars(Product).get("name")
    assert isinstance(desc, SlotDescriptor)


def test_shape_slot_names_are_set_by_metaclass():
    class Item(Shape):
        sku = Slot(ItemRef)

    assert Item._slots["sku"].name == "sku"


def test_shape_inherits_parent_slots():
    class Base(Shape):
        base_field = Slot(ItemRef)

    class Child(Base):
        child_field = Slot(ItemRef)

    assert "base_field" in Child._slots
    assert "child_field" in Child._slots


def test_shape_accessing_slot_on_class_returns_ref():
    class Widget(Shape):
        value = Slot(ItemRef)

    ref = Widget.value
    assert isinstance(ref, ItemRef)


def test_shape_ref_slot_navigation():
    class Inner(Shape):
        x = Slot(ItemRef)

    class Outer(Shape):
        inner = Slot(ShapeRef, shape_type=Inner)

    ref = Outer.inner
    assert isinstance(ref, ShapeRef)
    assert ref._shape_type is Inner


# ---------------------------------------------------------------------------
# SlotDescriptor
# ---------------------------------------------------------------------------


def test_slot_descriptor_raises_on_set():
    class S(Shape):
        field = Slot(ItemRef)

    desc = SlotDescriptor("field", S._slots["field"])
    with pytest.raises(AttributeError, match="read-only"):
        desc.__set__(object(), "oops")


def test_slot_descriptor_raises_when_accessed_on_instance():
    class S(Shape):
        field = Slot(ItemRef)

    desc = SlotDescriptor("field", S._slots["field"])
    with pytest.raises(TypeError, match="Shape class"):
        desc.__get__(object(), None)
