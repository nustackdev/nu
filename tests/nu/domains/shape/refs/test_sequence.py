"""Tests for SequenceRef / MutableSequenceRef / ReactiveSequenceRef hierarchy."""

from __future__ import annotations

import pytest

import nu
from nu.core.flows.control import IfDo
from nu.core.reactive import OnChange, OnChildChange, OnChildrenChange
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    Missing,
    SetCmd,
)
from nu.domains.shape.item import ItemRef
from nu.domains.shape.sequence import MutableSequenceRef, ReactiveSequenceRef, SequenceRef
from nu.forms import Int, List, Object, Str
from nu.lang import TypeInfo


class MyShape(Shape):
    pass


class StubSequenceRef(ReactiveSequenceRef):
    """A substrate stand-in: descends to a bare core leaf, as a fabric would to its own."""

    def _wrap_item_ref(self, address):
        return ItemRef(address, parent_ref=self, owner_shape=self._owner_shape)


def _declared(ref, value):
    ref._payload["type_info"] = TypeInfo(type(ref), elem=TypeInfo(value))
    return ref


def test_sequence_ref_subscript_needs_a_substrate():
    with pytest.raises(NotImplementedError, match="_wrap_item_ref"):
        SequenceRef("my_seq")[0]


def test_sequence_ref_subscript_routes_through_wrap_item_ref():
    s = StubSequenceRef("my_seq")
    assert isinstance(s[0], ItemRef)


def test_sequence_ref_child_has_self_as_parent():
    s = StubSequenceRef("my_seq")
    child = s[3]
    assert child._parent is s


def test_sequence_ref_child_inherits_owner_shape():
    s = StubSequenceRef("my_seq", owner_shape=MyShape)
    child = s[0]
    assert child._owner_shape is MyShape


def test_sequence_ref_different_indices_produce_different_refs():
    s = StubSequenceRef("my_seq")
    assert s[0] is not s[1]


def test_sequence_ref_string_index_is_accepted():
    # subscript is typed as object — string keys are valid for some substrates
    s = StubSequenceRef("my_seq")
    child = s["log_key_0"]
    assert isinstance(child, ItemRef)


# ---------------------------------------------------------------------------
# Results typed by the declaration
# ---------------------------------------------------------------------------


def test_sequence_ref_element_results_take_the_declared_value_form():
    s = _declared(MutableSequenceRef("my_seq"), str)
    assert type(s.first_elem()) is Str
    assert type(s.last_elem()) is Str
    assert type(s.pop()) is Str


def test_sequence_ref_undeclared_element_results_are_object():
    s = MutableSequenceRef("my_seq")
    assert type(s.first_elem()) is Object


def test_sequence_ref_slice_carries_the_declared_element_type():
    s = _declared(SequenceRef("my_seq"), int)
    sliced = s[0:2]
    assert type(sliced) is List
    assert type(sliced.first_elem()) is Int
    assert type(sliced[0]) is Int


def test_sequence_ref_slice_routes_to_slice_op():
    # Slice subscript goes through SliceableForm.slice(), not _wrap_item_ref.
    # Without the slice guard, ref[:2] would return an ItemRef addressed by
    # a `slice` object, which is nonsense.
    from nu.core import GetItem, Slice

    sentinel = object()

    class StubSeq(SequenceRef):
        def _wrap_sliceable_result(self, operand):
            return (sentinel, operand)

    s = StubSeq("my_seq")
    result = s[1:4]
    assert isinstance(result, tuple) and result[0] is sentinel
    getitem = result[1]
    assert isinstance(getitem, GetItem)
    assert isinstance(nu.tree.children(getitem)[1], Slice)


# ---------------------------------------------------------------------------
# SequenceRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_sequence_ref_exists_returns_exists_query():
    s = SequenceRef("my_seq")
    assert isinstance(s.exists(), nu.Bool)
    assert isinstance(s.exists()._source, Exists)


def test_sequence_ref_missing_returns_missing_query():
    s = SequenceRef("my_seq")
    assert isinstance(s.missing(), nu.Bool)
    assert isinstance(s.missing()._source, Missing)


def test_sequence_ref_len_returns_int_form():
    s = SequenceRef("my_seq")
    assert isinstance(s.len(), Int)


# ---------------------------------------------------------------------------
# MutableSequenceRef tier
# ---------------------------------------------------------------------------


def test_mutable_sequence_ref_is_subclass_of_sequence_ref():
    assert issubclass(MutableSequenceRef, SequenceRef)


def test_mutable_sequence_ref_set_returns_set_command():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.set([1, 2, 3]), SetCmd)


def test_mutable_sequence_ref_erase_returns_erase_command():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.erase(), Erase)


def test_mutable_sequence_ref_inherits_exists_missing():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.exists(), nu.Bool)
    assert isinstance(s.exists()._source, Exists)
    assert isinstance(s.missing(), nu.Bool)
    assert isinstance(s.missing()._source, Missing)


def test_mutable_sequence_ref_init_returns_ifdo_of_missing_and_set():
    s = MutableSequenceRef("my_seq")
    result = s.init([])
    assert isinstance(result, IfDo)
    cond, body = nu.tree.children(result)
    assert isinstance(cond, nu.Bool)
    assert isinstance(cond._source, Missing)
    assert isinstance(body, SetCmd)


# ---------------------------------------------------------------------------
# ReactiveSequenceRef tier
# ---------------------------------------------------------------------------


def test_reactive_sequence_ref_is_subclass_of_mutable_sequence_ref():
    assert issubclass(ReactiveSequenceRef, MutableSequenceRef)


def test_reactive_sequence_ref_on_change_returns_on_change_action():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.on_change(), OnChange)


def test_reactive_sequence_ref_on_child_change_returns_action():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.on_child_change(0), OnChildChange)


def test_reactive_sequence_ref_on_children_change_returns_action():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.on_children_change(), OnChildrenChange)


def test_reactive_sequence_ref_inherits_set_erase():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.set([]), SetCmd)
    assert isinstance(s.erase(), Erase)
