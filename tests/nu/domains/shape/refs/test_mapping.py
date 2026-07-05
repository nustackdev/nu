"""Tests for MappingRef / MutableMappingRef / ReactiveMappingRef hierarchy."""

from __future__ import annotations

from nu.core.reactive import (
    OnChangeQuery,
    OnChildChangeQuery,
    OnChildrenChangeQuery,
    OnDescendantsChangeQuery,
)
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    EraseCommand,
    ExistsQuery,
    MissingQuery,
    StoreCommand,
)
from nu.domains.shape.refs.item import ItemRef, MutableItemRef, ReactiveItemRef
from nu.domains.shape.refs.mapping import MappingRef, MutableMappingRef, ReactiveMappingRef
from nu.forms.primitives import IntForm


class MyShape(Shape):
    pass


def test_mapping_ref_subscript_returns_item_ref():
    m = MappingRef("my_map")
    child = m["key"]
    assert isinstance(child, ItemRef)


def test_mapping_ref_subscript_key_is_address():
    m = MappingRef("my_map")
    child = m["abc"]
    # address is children[0] of the child ref
    assert child._children  # non-empty


def test_mapping_ref_child_has_self_as_parent():
    m = MappingRef("my_map")
    child = m["k"]
    assert child._parent is m


def test_mapping_ref_child_inherits_owner_shape():
    m = MappingRef("my_map", owner_shape=MyShape)
    child = m["k"]
    assert child._owner_shape is MyShape


def test_mapping_ref_different_keys_produce_different_refs():
    m = MappingRef("my_map")
    a = m["a"]
    b = m["b"]
    assert a is not b


def test_mapping_ref_same_key_produces_equal_structure():
    m = MappingRef("my_map")
    a1 = m["a"]
    a2 = m["a"]
    assert type(a1) is type(a2)
    assert a1._parent is a2._parent


# ---------------------------------------------------------------------------
# MappingRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_mapping_ref_exists_returns_exists_query():
    m = MappingRef("my_map")
    assert isinstance(m.exists(), ExistsQuery)


def test_mapping_ref_missing_returns_missing_query():
    m = MappingRef("my_map")
    assert isinstance(m.missing(), MissingQuery)


def test_mapping_ref_len_returns_int_form():
    m = MappingRef("my_map")
    assert isinstance(m.len(), IntForm)


# ---------------------------------------------------------------------------
# MutableMappingRef tier
# ---------------------------------------------------------------------------


def test_mutable_mapping_ref_is_subclass_of_mapping_ref():
    assert issubclass(MutableMappingRef, MappingRef)


def test_mutable_mapping_ref_subscript_returns_mutable_item_ref():
    m = MutableMappingRef("my_map")
    child = m["k"]
    assert isinstance(child, MutableItemRef)


def test_mutable_mapping_ref_child_parent_is_self():
    m = MutableMappingRef("my_map")
    assert m["k"]._parent is m


def test_mutable_mapping_ref_has_store():
    m = MutableMappingRef("my_map")
    assert hasattr(m, "store")


def test_mutable_mapping_ref_store_returns_store_command():
    m = MutableMappingRef("my_map")
    assert isinstance(m.store({"a": 1}), StoreCommand)


def test_mutable_mapping_ref_erase_returns_erase_command():
    m = MutableMappingRef("my_map")
    assert isinstance(m.erase(), EraseCommand)


def test_mutable_mapping_ref_inherits_exists_missing_len():
    m = MutableMappingRef("my_map")
    assert isinstance(m.exists(), ExistsQuery)
    assert isinstance(m.missing(), MissingQuery)
    assert isinstance(m.len(), IntForm)


# ---------------------------------------------------------------------------
# ReactiveMappingRef tier
# ---------------------------------------------------------------------------


def test_reactive_mapping_ref_is_subclass_of_mutable_mapping_ref():
    assert issubclass(ReactiveMappingRef, MutableMappingRef)


def test_reactive_mapping_ref_subscript_returns_reactive_item_ref():
    m = ReactiveMappingRef("my_map")
    child = m["k"]
    assert isinstance(child, ReactiveItemRef)


def test_reactive_mapping_ref_child_parent_is_self():
    m = ReactiveMappingRef("my_map")
    assert m["k"]._parent is m


def test_reactive_mapping_ref_on_change_returns_on_change_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_change(), OnChangeQuery)


def test_reactive_mapping_ref_on_child_change_returns_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_child_change("key"), OnChildChangeQuery)


def test_reactive_mapping_ref_on_children_change_returns_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_children_change(), OnChildrenChangeQuery)


def test_reactive_mapping_ref_on_descendants_change_returns_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_descendants_change("a", "b"), OnDescendantsChangeQuery)


def test_reactive_mapping_ref_inherits_store_erase():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.store({}), StoreCommand)
    assert isinstance(m.erase(), EraseCommand)
