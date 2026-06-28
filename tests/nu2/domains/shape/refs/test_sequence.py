"""Tests for SequenceRef / MutableSequenceRef / ReactiveSequenceRef hierarchy."""

from __future__ import annotations

from nu2.domains.shape.dsl import Shape
from nu2.domains.shape.interactions import (
    EraseCommand,
    ExistsQuery,
    MissingQuery,
    OnChildChangeQuery,
    OnChildrenChangeQuery,
    StoreCommand,
)
from nu2.domains.shape.refs.item import ItemRef, MutableItemRef, ReactiveItemRef
from nu2.domains.shape.refs.sequence import MutableSequenceRef, ReactiveSequenceRef, SequenceRef
from nu2.forms.primitives import IntForm
from nu2.forms.reactive import OnChangeQuery


class MyShape(Shape):
    pass


def test_sequence_ref_subscript_returns_item_ref():
    s = SequenceRef("my_seq")
    child = s[0]
    assert isinstance(child, ItemRef)


def test_sequence_ref_child_has_self_as_parent():
    s = SequenceRef("my_seq")
    child = s[3]
    assert child.parent_ref is s


def test_sequence_ref_child_inherits_owner_shape():
    s = SequenceRef("my_seq", owner_shape=MyShape)
    child = s[0]
    assert child._owner_shape is MyShape


def test_sequence_ref_different_indices_produce_different_refs():
    s = SequenceRef("my_seq")
    a = s[0]
    b = s[1]
    assert a is not b


def test_sequence_ref_string_index_is_accepted():
    # subscript is typed as object — string keys are valid for some substrates
    s = SequenceRef("my_seq")
    child = s["log_key_0"]
    assert isinstance(child, ItemRef)


# ---------------------------------------------------------------------------
# SequenceRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_sequence_ref_exists_returns_exists_query():
    s = SequenceRef("my_seq")
    assert isinstance(s.exists(), ExistsQuery)


def test_sequence_ref_missing_returns_missing_query():
    s = SequenceRef("my_seq")
    assert isinstance(s.missing(), MissingQuery)


def test_sequence_ref_len_returns_int_form():
    s = SequenceRef("my_seq")
    assert isinstance(s.len(), IntForm)


# ---------------------------------------------------------------------------
# MutableSequenceRef tier
# ---------------------------------------------------------------------------


def test_mutable_sequence_ref_is_subclass_of_sequence_ref():
    assert issubclass(MutableSequenceRef, SequenceRef)


def test_mutable_sequence_ref_subscript_returns_mutable_item_ref():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s[0], MutableItemRef)


def test_mutable_sequence_ref_child_parent_is_self():
    s = MutableSequenceRef("my_seq")
    assert s[0].parent_ref is s


def test_mutable_sequence_ref_store_returns_store_command():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.store([1, 2, 3]), StoreCommand)


def test_mutable_sequence_ref_erase_returns_erase_command():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.erase(), EraseCommand)


def test_mutable_sequence_ref_inherits_exists_missing():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.exists(), ExistsQuery)
    assert isinstance(s.missing(), MissingQuery)


# ---------------------------------------------------------------------------
# ReactiveSequenceRef tier
# ---------------------------------------------------------------------------


def test_reactive_sequence_ref_is_subclass_of_mutable_sequence_ref():
    assert issubclass(ReactiveSequenceRef, MutableSequenceRef)


def test_reactive_sequence_ref_subscript_returns_reactive_item_ref():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s[0], ReactiveItemRef)


def test_reactive_sequence_ref_on_change_returns_on_change_action():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.on_change(), OnChangeQuery)


def test_reactive_sequence_ref_on_child_change_returns_action():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.on_child_change(0), OnChildChangeQuery)


def test_reactive_sequence_ref_on_children_change_returns_action():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.on_children_change(), OnChildrenChangeQuery)


def test_reactive_sequence_ref_inherits_store_erase():
    s = ReactiveSequenceRef("my_seq")
    assert isinstance(s.store([]), StoreCommand)
    assert isinstance(s.erase(), EraseCommand)
