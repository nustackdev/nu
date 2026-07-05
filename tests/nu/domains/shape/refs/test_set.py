"""Tests for SetRef / MutableSetRef / ReactiveSetRef hierarchy."""

from __future__ import annotations

import pytest

from nu.core.reactive import OnChangeQuery, OnChildrenChangeQuery
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    EraseCommand,
    ExistsQuery,
    MissingQuery,
    StoreCommand,
)
from nu.domains.shape.refs.base import StructuredRef
from nu.domains.shape.refs.set_ import MutableSetRef, ReactiveSetRef, SetRef
from nu.forms.primitives import IntForm


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
    assert isinstance(ref.exists(), ExistsQuery)


def test_set_ref_missing_returns_missing_query():
    ref = SetRef("my_set")
    assert isinstance(ref.missing(), MissingQuery)


def test_set_ref_len_returns_int_form():
    ref = SetRef("my_set")
    assert isinstance(ref.len(), IntForm)


# ---------------------------------------------------------------------------
# MutableSetRef tier
# ---------------------------------------------------------------------------


def test_mutable_set_ref_is_subclass_of_set_ref():
    assert issubclass(MutableSetRef, SetRef)


def test_mutable_set_ref_constructs():
    ref = MutableSetRef("my_set")
    assert ref._children


def test_mutable_set_ref_has_store():
    ref = MutableSetRef("my_set")
    assert hasattr(ref, "store")


def test_mutable_set_ref_store_returns_store_command():
    ref = MutableSetRef("my_set")
    assert isinstance(ref.store({1, 2, 3}), StoreCommand)


def test_mutable_set_ref_erase_returns_erase_command():
    ref = MutableSetRef("my_set")
    assert isinstance(ref.erase(), EraseCommand)


def test_mutable_set_ref_inherits_exists_missing():
    ref = MutableSetRef("my_set")
    assert isinstance(ref.exists(), ExistsQuery)
    assert isinstance(ref.missing(), MissingQuery)


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
    assert isinstance(ref.on_change(), OnChangeQuery)


def test_reactive_set_ref_on_children_change_returns_action():
    ref = ReactiveSetRef("my_set")
    assert isinstance(ref.on_children_change(), OnChildrenChangeQuery)


def test_reactive_set_ref_inherits_store_erase():
    ref = ReactiveSetRef("my_set")
    assert isinstance(ref.store(set()), StoreCommand)
    assert isinstance(ref.erase(), EraseCommand)
