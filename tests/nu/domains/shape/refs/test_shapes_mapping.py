"""Tests for ShapesMappingRef / MutableShapesMappingRef / ReactiveShapesMappingRef."""

from __future__ import annotations

from nu.core.reactive import OnChangeQuery, OnChildChangeQuery
from nu.domains.shape.dsl import Shape, Slot
from nu.domains.shape.interactions import (
    EraseCommand,
    ExistsQuery,
    MissingQuery,
    StoreCommand,
)
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.shape import MutableShapeRef, ReactiveShapeRef, ShapeRef
from nu.domains.shape.refs.shapes_mapping import (
    MutableShapesMappingRef,
    ReactiveShapesMappingRef,
    ShapesMappingRef,
)


class Entry(Shape):
    value = Slot(ItemRef)


def test_shapes_mapping_ref_subscript_returns_shape_ref():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    child = m["key1"]
    assert isinstance(child, ShapeRef)


def test_shapes_mapping_ref_child_shape_type_matches():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    child = m["key1"]
    assert child._shape_type is Entry


def test_shapes_mapping_ref_child_parent_is_self():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    child = m["key1"]
    assert child.parent_ref is m


def test_shapes_mapping_ref_item_shape_type_property():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    assert m.item_shape_type is Entry


def test_shapes_mapping_ref_different_keys_distinct():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    a = m["a"]
    b = m["b"]
    assert a is not b


def test_shapes_mapping_ref_child_can_navigate_slots():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    child = m["k"]
    val_ref = child.value
    assert isinstance(val_ref, ItemRef)


# ---------------------------------------------------------------------------
# ShapesMappingRef Form surface (exists / missing)
# ---------------------------------------------------------------------------


def test_shapes_mapping_ref_exists_returns_exists_query():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.exists(), ExistsQuery)


def test_shapes_mapping_ref_missing_returns_missing_query():
    m = ShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.missing(), MissingQuery)


# ---------------------------------------------------------------------------
# MutableShapesMappingRef tier
# ---------------------------------------------------------------------------


def test_mutable_shapes_mapping_ref_is_subclass_of_shapes_mapping_ref():
    assert issubclass(MutableShapesMappingRef, ShapesMappingRef)


def test_mutable_shapes_mapping_ref_subscript_returns_mutable_shape_ref():
    m = MutableShapesMappingRef("entries", item_shape_type=Entry)
    child = m["k"]
    assert isinstance(child, MutableShapeRef)


def test_mutable_shapes_mapping_ref_child_shape_type_matches():
    m = MutableShapesMappingRef("entries", item_shape_type=Entry)
    assert m["k"]._shape_type is Entry


def test_mutable_shapes_mapping_ref_store_returns_store_command():
    m = MutableShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.store({}), StoreCommand)


def test_mutable_shapes_mapping_ref_erase_returns_erase_command():
    m = MutableShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.erase(), EraseCommand)


# ---------------------------------------------------------------------------
# ReactiveShapesMappingRef tier
# ---------------------------------------------------------------------------


def test_reactive_shapes_mapping_ref_is_subclass_of_mutable():
    assert issubclass(ReactiveShapesMappingRef, MutableShapesMappingRef)


def test_reactive_shapes_mapping_ref_subscript_returns_reactive_shape_ref():
    m = ReactiveShapesMappingRef("entries", item_shape_type=Entry)
    child = m["k"]
    assert isinstance(child, ReactiveShapeRef)


def test_reactive_shapes_mapping_ref_on_change_returns_on_change_action():
    m = ReactiveShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.on_change(), OnChangeQuery)


def test_reactive_shapes_mapping_ref_on_child_change_returns_action():
    m = ReactiveShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.on_child_change("k"), OnChildChangeQuery)


def test_reactive_shapes_mapping_ref_inherits_store_erase():
    m = ReactiveShapesMappingRef("entries", item_shape_type=Entry)
    assert isinstance(m.store({}), StoreCommand)
    assert isinstance(m.erase(), EraseCommand)
