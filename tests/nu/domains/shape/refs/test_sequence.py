"""Tests for SequenceRef / MutableSequenceRef / ReactiveSequenceRef hierarchy."""

from __future__ import annotations

from nu.core.reactive import OnChange, OnChildChange, OnChildrenChange
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    Missing,
    SetCmd,
)
from nu.domains.shape.refs.item import ItemRef, MutableItemRef, ReactiveItemRef
from nu.domains.shape.refs.sequence import MutableSequenceRef, ReactiveSequenceRef, SequenceRef
from nu.forms.primitives import Int


class MyShape(Shape):
    pass


def test_sequence_ref_subscript_returns_item_ref():
    s = SequenceRef("my_seq")
    child = s[0]
    assert isinstance(child, ItemRef)


def test_sequence_ref_child_has_self_as_parent():
    s = SequenceRef("my_seq")
    child = s[3]
    assert child._parent is s


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
    assert isinstance(getitem._children[1], Slice)


# ---------------------------------------------------------------------------
# SequenceRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_sequence_ref_exists_returns_exists_query():
    s = SequenceRef("my_seq")
    assert isinstance(s.exists(), Exists)


def test_sequence_ref_missing_returns_missing_query():
    s = SequenceRef("my_seq")
    assert isinstance(s.missing(), Missing)


def test_sequence_ref_len_returns_int_form():
    s = SequenceRef("my_seq")
    assert isinstance(s.len(), Int)


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
    assert s[0]._parent is s


def test_mutable_sequence_ref_set_returns_set_command():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.set([1, 2, 3]), SetCmd)


def test_mutable_sequence_ref_erase_returns_erase_command():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.erase(), Erase)


def test_mutable_sequence_ref_inherits_exists_missing():
    s = MutableSequenceRef("my_seq")
    assert isinstance(s.exists(), Exists)
    assert isinstance(s.missing(), Missing)


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
