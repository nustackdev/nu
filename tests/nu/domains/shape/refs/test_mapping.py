"""Tests for MappingRef / MutableMappingRef / ReactiveMappingRef hierarchy."""

from __future__ import annotations

import pytest

import nu
from nu.core import Not
from nu.core.flows.control import IfDo
from nu.core.reactive import (
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
)
from nu.domains.shape.collections.abc.mapping import (
    MappingRef,
    MutableMappingRef,
    MutableOrderedMappingRef,
    OrderedMappingRef,
    ReactiveMappingRef,
    ReactiveOrderedMappingRef,
)
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    SetCmd,
)
from nu.domains.shape.item import ItemRef
from nu.forms import DictKeys, DictValues, Int, Object, Str
from nu.forms.collections.abc.mapping_interactions import (
    KeysPage,
    ReversedKeys,
    ReversedKeysPage,
)
from nu.lang import TypeInfo


class MyShape(Shape):
    pass


class StubMappingRef(ReactiveMappingRef):
    """A substrate stand-in: descends to a bare core leaf, as a fabric would to its own."""

    def _wrap_item_ref(self, address):
        return ItemRef(address, parent_ref=self, owner_shape=self._owner_shape)


def _declared(ref, key, value):
    ref._payload["type_info"] = TypeInfo(type(ref), key=TypeInfo(key), elem=TypeInfo(value))
    return ref


def test_mapping_ref_subscript_needs_a_substrate():
    with pytest.raises(NotImplementedError, match="_wrap_item_ref"):
        MappingRef("my_map")["k"]


def test_mapping_ref_subscript_routes_through_wrap_item_ref():
    m = StubMappingRef("my_map")
    assert isinstance(m["key"], ItemRef)


def test_mapping_ref_child_has_self_as_parent():
    m = StubMappingRef("my_map")
    child = m["k"]
    assert child._parent is m


def test_mapping_ref_child_inherits_owner_shape():
    m = StubMappingRef("my_map", owner_shape=MyShape)
    child = m["k"]
    assert child._owner_shape is MyShape


def test_mapping_ref_different_keys_produce_different_refs():
    m = StubMappingRef("my_map")
    assert m["a"] is not m["b"]


# ---------------------------------------------------------------------------
# Results typed by the declaration
# ---------------------------------------------------------------------------


def test_mapping_ref_value_results_take_the_declared_value_form():
    m = _declared(MutableMappingRef("my_map"), str, int)
    assert type(m.get_item("a", 0)) is Int
    assert type(m.pop("a")) is Int
    assert type(m.setdefault("a", 0)) is Int


def test_mapping_ref_undeclared_value_results_are_object():
    m = MutableMappingRef("my_map")
    assert type(m.get_item("a")) is Object
    assert type(m.pop("a")) is Object


def test_mapping_ref_collection_results_carry_the_declaration():
    m = _declared(MutableMappingRef("my_map"), str, int)
    assert type(m.get_item("a")) is Int
    assert not hasattr(m, "copy")
    items = nu.tree.payload(m.items())["type_info"]
    assert (items.key, items.elem) == (TypeInfo(str), TypeInfo(int))
    assert nu.tree.payload(m.keys())["type_info"].elem == TypeInfo(str)
    assert nu.tree.payload(m.values())["type_info"].elem == TypeInfo(int)
    assert isinstance(m.keys(), DictKeys)
    assert isinstance(m.values(), DictValues)


def test_mapping_ref_element_results_take_the_declared_key_form():
    m = _declared(MappingRef("my_map"), str, int)
    assert type(m._wrap_element_result(nu.Literal("k"))) is Str


# ---------------------------------------------------------------------------
# MappingRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_mapping_ref_exists_returns_exists_query():
    m = MappingRef("my_map")
    assert isinstance(m.exists(), nu.Bool)
    assert isinstance(m.exists()._source, Exists)


def test_mapping_ref_missing_returns_missing_query():
    m = MappingRef("my_map")
    assert isinstance(m.exists().not_(), nu.Bool)
    assert isinstance(m.exists().not_()._source, Not)


def test_mapping_ref_len_returns_int_form():
    m = MappingRef("my_map")
    assert isinstance(m.len(), Int)


# ---------------------------------------------------------------------------
# MutableMappingRef tier
# ---------------------------------------------------------------------------


def test_mutable_mapping_ref_is_subclass_of_mapping_ref():
    assert issubclass(MutableMappingRef, MappingRef)


def test_mutable_mapping_ref_has_set():
    m = MutableMappingRef("my_map")
    assert hasattr(m, "set")


def test_mutable_mapping_ref_set_returns_set_command():
    m = MutableMappingRef("my_map")
    assert isinstance(m.set({"a": 1}), SetCmd)


def test_mutable_mapping_ref_erase_returns_erase_command():
    m = MutableMappingRef("my_map")
    assert isinstance(m.erase(), Erase)


def test_mutable_mapping_ref_inherits_exists_missing_len():
    m = MutableMappingRef("my_map")
    assert isinstance(m.exists(), nu.Bool)
    assert isinstance(m.exists()._source, Exists)
    assert isinstance(m.exists().not_(), nu.Bool)
    assert isinstance(m.exists().not_()._source, Not)
    assert isinstance(m.len(), Int)


def test_mutable_mapping_ref_init_returns_ifdo_of_missing_and_set():
    m = MutableMappingRef("my_map")
    result = m.init({})
    assert isinstance(result, IfDo)
    cond, body = nu.tree.children(result)
    assert isinstance(cond, nu.Bool)
    assert isinstance(cond._source, Not)
    assert isinstance(body, SetCmd)


# ---------------------------------------------------------------------------
# ReactiveMappingRef tier
# ---------------------------------------------------------------------------


def test_reactive_mapping_ref_is_subclass_of_mutable_mapping_ref():
    assert issubclass(ReactiveMappingRef, MutableMappingRef)


def test_reactive_mapping_ref_on_change_returns_on_change_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_change(), OnChange)


def test_reactive_mapping_ref_on_child_change_returns_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_child_change("key"), OnChildChange)


def test_reactive_mapping_ref_on_children_change_returns_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_children_change(), OnChildrenChange)


def test_reactive_mapping_ref_on_descendants_change_returns_action():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.on_descendants_change("a", "b"), OnDescendantsChange)


def test_reactive_mapping_ref_inherits_set_erase():
    m = ReactiveMappingRef("my_map")
    assert isinstance(m.set({}), SetCmd)
    assert isinstance(m.erase(), Erase)


# ---------------------------------------------------------------------------
# Ordered tier: OrderedMappingRef -> MutableOrderedMappingRef -> ReactiveOrderedMappingRef
# ---------------------------------------------------------------------------


def test_ordered_mapping_refs_stack_on_the_plain_ones():
    assert issubclass(OrderedMappingRef, MappingRef)
    assert issubclass(MutableOrderedMappingRef, OrderedMappingRef)
    assert issubclass(MutableOrderedMappingRef, MutableMappingRef)
    assert issubclass(ReactiveOrderedMappingRef, MutableOrderedMappingRef)
    assert issubclass(ReactiveOrderedMappingRef, ReactiveMappingRef)


def test_ordered_mapping_refs_are_exported():
    assert nu.shape.OrderedMappingRef is OrderedMappingRef
    assert nu.shape.MutableOrderedMappingRef is MutableOrderedMappingRef
    assert nu.shape.ReactiveOrderedMappingRef is ReactiveOrderedMappingRef


def test_plain_mapping_refs_have_no_reversed_reads():
    for ref in (MappingRef("m"), MutableMappingRef("m"), ReactiveMappingRef("m")):
        assert not hasattr(ref, "reversed_keys")
        with pytest.raises(TypeError, match="after"):
            ref.keys(after="a")  # type: ignore[call-arg]


def test_ordered_mapping_ref_reads_back_to_front_typed_by_the_declaration():
    m = _declared(ReactiveOrderedMappingRef("m"), str, int)
    assert isinstance(nu.tree.children(m.reversed_keys())[0], ReversedKeys)
    assert isinstance(nu.tree.children(m.keys(limit=2))[0], KeysPage)
    assert isinstance(nu.tree.children(m.reversed_keys(before="a"))[0], ReversedKeysPage)
    assert nu.tree.payload(m.reversed_keys())["type_info"].elem == TypeInfo(str)
    assert nu.tree.payload(m.reversed_values())["type_info"].elem == TypeInfo(int)
    assert isinstance(m.on_change(), OnChange)
    assert isinstance(m.on_children_change(), OnChildrenChange)


def test_shape_ref_stays_on_the_plain_mapping():
    assert not issubclass(nu.shape.ShapeRef, OrderedMappingRef)


def test_mem_dict_ref_is_a_mutable_ordered_mapping():
    class Port(Shape):
        meta = nu.DictRef.slot(int)

    assert isinstance(Port.meta, MutableOrderedMappingRef)
    ctx = nu.Context().bind(dict, {"meta": {"a": 1, "b": 2}}, Port)
    assert list(nu.run(Port.meta.reversed_keys(), ctx)[0]) == ["b", "a"]
    assert list(nu.run(Port.meta.reversed_items(), ctx)[0]) == [("b", 2), ("a", 1)]
