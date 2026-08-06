"""Tests for SetRef / MutableSetRef / ReactiveSetRef hierarchy."""

from __future__ import annotations

import pytest

from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    Missing,
    SetCmd,
)
from nu.domains.shape.refs.base import StructuredRef
from nu.domains.shape.refs.set_ import MutableSetRef, ReactiveSetRef, SetRef
from nu.forms.primitives import Int
from nu.reactive import OnChange, OnChildrenChange


class MyShape(Shape):
    pass


def test_set_ref_is_structured_ref():
    assert issubclass(SetRef, StructuredRef)


def test_set_ref_constructs_with_address():
    ref = SetRef("my_set")
    assert ref._children


def test_set_ref_parent_ref_none_by_default():
    ref = SetRef("my_set")
    assert ref._parent is None


def test_set_ref_stores_owner_shape():
    ref = SetRef("my_set", owner_shape=MyShape)
    assert ref._owner_shape is MyShape


def test_set_ref_has_no_subscript():
    ref = SetRef("my_set")
    with pytest.raises((AttributeError, TypeError)):
        ref["element"]  # type: ignore[index]


# ---------------------------------------------------------------------------
# SetRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_set_ref_exists_returns_exists_query():
    ref = SetRef("my_set")
    assert isinstance(ref.exists(), Exists)


def test_set_ref_missing_returns_missing_query():
    ref = SetRef("my_set")
    assert isinstance(ref.missing(), Missing)


def test_set_ref_len_returns_int_form():
    ref = SetRef("my_set")
    assert isinstance(ref.len(), Int)


# ---------------------------------------------------------------------------
# MutableSetRef tier
# ---------------------------------------------------------------------------


def test_mutable_set_ref_is_subclass_of_set_ref():
    assert issubclass(MutableSetRef, SetRef)


def test_mutable_set_ref_constructs():
    ref = MutableSetRef("my_set")
    assert ref._children


def test_mutable_set_ref_has_set():
    ref = MutableSetRef("my_set")
    assert hasattr(ref, "set")


def test_mutable_set_ref_set_returns_set_command():
    ref = MutableSetRef("my_set")
    assert isinstance(ref.set({1, 2, 3}), SetCmd)


def test_mutable_set_ref_erase_returns_erase_command():
    ref = MutableSetRef("my_set")
    assert isinstance(ref.erase(), Erase)


def test_mutable_set_ref_inherits_exists_missing():
    ref = MutableSetRef("my_set")
    assert isinstance(ref.exists(), Exists)
    assert isinstance(ref.missing(), Missing)


def test_mutable_set_ref_has_no_subscript():
    ref = MutableSetRef("my_set")
    with pytest.raises((AttributeError, TypeError)):
        ref["element"]  # type: ignore[index]


# ---------------------------------------------------------------------------
# ReactiveSetRef tier
# ---------------------------------------------------------------------------


def test_reactive_set_ref_is_subclass_of_mutable_set_ref():
    assert issubclass(ReactiveSetRef, MutableSetRef)


def test_reactive_set_ref_constructs():
    ref = ReactiveSetRef("my_set")
    assert ref._children


def test_reactive_set_ref_on_change_returns_on_change_action():
    ref = ReactiveSetRef("my_set")
    assert isinstance(ref.on_change(), OnChange)


def test_reactive_set_ref_on_children_change_returns_action():
    ref = ReactiveSetRef("my_set")
    assert isinstance(ref.on_children_change(), OnChildrenChange)


def test_reactive_set_ref_inherits_set_erase():
    ref = ReactiveSetRef("my_set")
    assert isinstance(ref.set(set()), SetCmd)
    assert isinstance(ref.erase(), Erase)
