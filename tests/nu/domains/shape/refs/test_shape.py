"""Tests for ShapeRef / MutableShapeRef / ReactiveShapeRef hierarchy."""

from __future__ import annotations

import pytest

from nu.domains.shape.dsl import Shape, Slot
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    Missing,
    SetCmd,
)
from nu.domains.shape.refs.base import StructuredRef
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.shape import MutableShapeRef, ReactiveShapeRef, ShapeRef
from nu.reactive import OnChange, OnChildChange


class Inner(Shape):
    x = Slot(ItemRef)
    y = Slot(ItemRef)


class Outer(Shape):
    inner = Slot(ShapeRef, shape_type=Inner)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_shape_ref_requires_shape_type():
    ref = ShapeRef("loc", shape_type=Inner)
    assert ref._payload["shape_type"] is Inner


def test_shape_ref_is_structured_ref():
    assert issubclass(ShapeRef, StructuredRef)


def test_shape_ref_shape_type_property():
    ref = ShapeRef("loc", shape_type=Inner)
    assert ref._payload["shape_type"] is Inner


# ---------------------------------------------------------------------------
# Attribute descent
# ---------------------------------------------------------------------------


def test_shape_ref_getattr_known_slot_returns_ref():
    ref = ShapeRef("loc", shape_type=Inner)
    child = ref.x
    assert isinstance(child, StructuredRef)


def test_shape_ref_getattr_child_parent_is_self():
    ref = ShapeRef("loc", shape_type=Inner)
    child = ref.x
    assert child._parent is ref


def test_shape_ref_getattr_unknown_slot_raises():
    ref = ShapeRef("loc", shape_type=Inner)
    with pytest.raises(AttributeError):
        _ = ref.nonexistent


def test_shape_ref_private_attr_raises():
    ref = ShapeRef("loc", shape_type=Inner)
    with pytest.raises(AttributeError):
        _ = ref._private


def test_shape_ref_different_slots_produce_different_refs():
    ref = ShapeRef("loc", shape_type=Inner)
    rx = ref.x
    ry = ref.y
    assert rx is not ry


# ---------------------------------------------------------------------------
# Pickle support
# ---------------------------------------------------------------------------


def test_shape_ref_getstate_setstate_roundtrip():
    ref = ShapeRef("loc", shape_type=Inner)
    state = ref.__getstate__()
    new_ref = object.__new__(ShapeRef)
    new_ref.__setstate__(state)
    assert new_ref._payload["shape_type"] is Inner


# ---------------------------------------------------------------------------
# ShapeRef Form surface (exists / missing)
# ---------------------------------------------------------------------------


def test_shape_ref_exists_returns_exists_query():
    ref = ShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.exists(), Exists)


def test_shape_ref_missing_returns_missing_query():
    ref = ShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.missing(), Missing)


# ---------------------------------------------------------------------------
# MutableShapeRef tier
# ---------------------------------------------------------------------------


def test_mutable_shape_ref_is_subclass_of_shape_ref():
    assert issubclass(MutableShapeRef, ShapeRef)


def test_mutable_shape_ref_constructs():
    ref = MutableShapeRef("loc", shape_type=Inner)
    assert ref._payload["shape_type"] is Inner


def test_mutable_shape_ref_set_returns_set_command():
    ref = MutableShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.set({"x": 1}), SetCmd)


def test_mutable_shape_ref_erase_returns_erase_command():
    ref = MutableShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.erase(), Erase)


def test_mutable_shape_ref_inherits_slot_navigation():
    ref = MutableShapeRef("loc", shape_type=Inner)
    child = ref.x
    assert isinstance(child, StructuredRef)


def test_mutable_shape_ref_inherits_exists_missing():
    ref = MutableShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.exists(), Exists)
    assert isinstance(ref.missing(), Missing)


# ---------------------------------------------------------------------------
# ReactiveShapeRef tier
# ---------------------------------------------------------------------------


def test_reactive_shape_ref_is_subclass_of_mutable_shape_ref():
    assert issubclass(ReactiveShapeRef, MutableShapeRef)


def test_reactive_shape_ref_constructs():
    ref = ReactiveShapeRef("loc", shape_type=Inner)
    assert ref._payload["shape_type"] is Inner


def test_reactive_shape_ref_on_change_returns_on_change_action():
    ref = ReactiveShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.on_change(), OnChange)


def test_reactive_shape_ref_on_child_change_returns_action():
    ref = ReactiveShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.on_child_change("x"), OnChildChange)


def test_reactive_shape_ref_inherits_set_erase():
    ref = ReactiveShapeRef("loc", shape_type=Inner)
    assert isinstance(ref.set({}), SetCmd)
    assert isinstance(ref.erase(), Erase)


def test_reactive_shape_ref_inherits_slot_navigation():
    ref = ReactiveShapeRef("loc", shape_type=Inner)
    child = ref.x
    assert isinstance(child, StructuredRef)


# ---------------------------------------------------------------------------
# ShapeRef mapping surface (#6 — v1 parity)
# ---------------------------------------------------------------------------


def test_shape_ref_has_mapping_surface():
    ref = ShapeRef("loc", shape_type=Inner)
    # Keys/values/items come from MappingForm; exists/missing come from
    # CollectionForm inside MappingForm.
    assert hasattr(ref, "keys")
    assert hasattr(ref, "values")
    assert hasattr(ref, "items")
    assert hasattr(ref, "exists")
    assert hasattr(ref, "missing")
    assert hasattr(ref, "extract")


def test_shape_ref_getitem_known_slot_returns_ref():
    ref = ShapeRef("loc", shape_type=Inner)
    child = ref["x"]
    assert isinstance(child, StructuredRef)


def test_shape_ref_getitem_child_parent_is_self():
    ref = ShapeRef("loc", shape_type=Inner)
    child = ref["y"]
    assert child._parent is ref


def test_shape_ref_getitem_unknown_slot_raises_key_error():
    ref = ShapeRef("loc", shape_type=Inner)
    import pytest as _pytest

    with _pytest.raises(KeyError):
        _ = ref["nonexistent"]


def test_shape_ref_getattr_and_getitem_produce_equivalent_refs():
    ref = ShapeRef("loc", shape_type=Inner)
    by_attr = ref.x
    by_item = ref["x"]
    # Both should be of the same type and share the same parent
    assert type(by_attr) is type(by_item)
    assert by_attr._parent is ref
    assert by_item._parent is ref


def test_mutable_shape_ref_has_mutable_mapping_surface():
    ref = MutableShapeRef("loc", shape_type=Inner)
    assert hasattr(ref, "set")
    assert hasattr(ref, "erase")
    assert hasattr(ref, "keys")
    assert hasattr(ref, "values")
    assert hasattr(ref, "exists")


def test_mutable_shape_ref_getitem_known_slot():
    ref = MutableShapeRef("loc", shape_type=Inner)
    child = ref["x"]
    assert isinstance(child, StructuredRef)
    assert child._parent is ref
