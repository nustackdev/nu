"""Tests for ShapesSequenceRef / MutableShapesSequenceRef / ReactiveShapesSequenceRef."""

from __future__ import annotations

from nu.core.reactive import OnChangeQuery, OnChildrenChangeQuery
from nu.domains.shape.dsl import Shape, Slot
from nu.domains.shape.interactions import (
    EraseCommand,
    ExistsQuery,
    MissingQuery,
    StoreCommand,
)
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.shape import MutableShapeRef, ReactiveShapeRef, ShapeRef
from nu.domains.shape.refs.shapes_sequence import (
    MutableShapesSequenceRef,
    ReactiveShapesSequenceRef,
    ShapesSequenceRef,
)


class Row(Shape):
    name = Slot(ItemRef)


def test_shapes_sequence_ref_subscript_returns_shape_ref():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    child = s[0]
    assert isinstance(child, ShapeRef)


def test_shapes_sequence_ref_child_shape_type_matches():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    child = s[0]
    assert child._shape_type is Row


def test_shapes_sequence_ref_child_parent_is_self():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    child = s[0]
    assert child._parent is s


def test_shapes_sequence_ref_item_shape_type_property():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    assert s._item_shape_type is Row


def test_shapes_sequence_ref_different_indices_distinct():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    a = s[0]
    b = s[1]
    assert a is not b


def test_shapes_sequence_ref_child_can_navigate_slots():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    child = s[0]
    name_ref = child.name
    assert isinstance(name_ref, ItemRef)


# ---------------------------------------------------------------------------
# ShapesSequenceRef Form surface (exists / missing)
# ---------------------------------------------------------------------------


def test_shapes_sequence_ref_exists_returns_exists_query():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.exists(), ExistsQuery)


def test_shapes_sequence_ref_missing_returns_missing_query():
    s = ShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.missing(), MissingQuery)


# ---------------------------------------------------------------------------
# MutableShapesSequenceRef tier
# ---------------------------------------------------------------------------


def test_mutable_shapes_sequence_ref_is_subclass_of_shapes_sequence_ref():
    assert issubclass(MutableShapesSequenceRef, ShapesSequenceRef)


def test_mutable_shapes_sequence_ref_subscript_returns_mutable_shape_ref():
    s = MutableShapesSequenceRef("rows", item_shape_type=Row)
    child = s[0]
    assert isinstance(child, MutableShapeRef)


def test_mutable_shapes_sequence_ref_child_shape_type_matches():
    s = MutableShapesSequenceRef("rows", item_shape_type=Row)
    assert s[0]._shape_type is Row


def test_mutable_shapes_sequence_ref_store_returns_store_command():
    s = MutableShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.store([]), StoreCommand)


def test_mutable_shapes_sequence_ref_erase_returns_erase_command():
    s = MutableShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.erase(), EraseCommand)


# ---------------------------------------------------------------------------
# ReactiveShapesSequenceRef tier
# ---------------------------------------------------------------------------


def test_reactive_shapes_sequence_ref_is_subclass_of_mutable():
    assert issubclass(ReactiveShapesSequenceRef, MutableShapesSequenceRef)


def test_reactive_shapes_sequence_ref_subscript_returns_reactive_shape_ref():
    s = ReactiveShapesSequenceRef("rows", item_shape_type=Row)
    child = s[0]
    assert isinstance(child, ReactiveShapeRef)


def test_reactive_shapes_sequence_ref_on_change_returns_on_change_action():
    s = ReactiveShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.on_change(), OnChangeQuery)


def test_reactive_shapes_sequence_ref_on_children_change_returns_action():
    s = ReactiveShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.on_children_change(), OnChildrenChangeQuery)


def test_reactive_shapes_sequence_ref_inherits_store_erase():
    s = ReactiveShapesSequenceRef("rows", item_shape_type=Row)
    assert isinstance(s.store([]), StoreCommand)
    assert isinstance(s.erase(), EraseCommand)
