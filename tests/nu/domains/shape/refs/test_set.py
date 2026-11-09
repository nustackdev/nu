"""Tests for the SetLikeRef / MutableSetRef tiers and the set row's ReactiveSetRef on top."""

from __future__ import annotations

import pytest

import nu
from nu.core import Not
from nu.core.reactive import OnChange, OnChildrenChange
from nu.domains.shape.base import StructuredRef
from nu.domains.shape.collections import ReactiveSetRef
from nu.domains.shape.collections.abc.set_ import MutableSetRef, SetLikeRef
from nu.domains.shape.dsl import Shape
from nu.domains.shape.interactions import (
    Erase,
    Exists,
    SetCmd,
)
from nu.forms.primitives import Int


class MyShape(Shape):
    pass


def test_set_like_ref_is_structured_ref():
    assert issubclass(SetLikeRef, StructuredRef)


def test_set_like_ref_constructs_with_address():
    ref = SetLikeRef("my_set")
    assert nu.tree.children(ref)


def test_set_like_ref_parent_ref_none_by_default():
    ref = SetLikeRef("my_set")
    assert ref._parent is None


def test_set_like_ref_stores_owner_shape():
    ref = SetLikeRef("my_set", owner_shape=MyShape)
    assert ref._owner_shape is MyShape


def test_set_like_ref_has_no_subscript():
    ref = SetLikeRef("my_set")
    with pytest.raises((AttributeError, TypeError)):
        ref["element"]  # type: ignore[index]


# ---------------------------------------------------------------------------
# SetLikeRef Form surface (exists / missing / len)
# ---------------------------------------------------------------------------


def test_set_like_ref_exists_returns_exists_query():
    ref = SetLikeRef("my_set")
    assert isinstance(ref.exists(), nu.Bool)
    assert isinstance(ref.exists()._source, Exists)


def test_set_like_ref_missing_returns_missing_query():
    ref = SetLikeRef("my_set")
    assert isinstance(ref.exists().not_(), nu.Bool)
    assert isinstance(ref.exists().not_()._source, Not)


def test_set_like_ref_len_returns_int_form():
    ref = SetLikeRef("my_set")
    assert isinstance(ref.len(), Int)


# ---------------------------------------------------------------------------
# MutableSetRef tier
# ---------------------------------------------------------------------------


def test_mutable_set_ref_is_subclass_of_set_ref():
    assert issubclass(MutableSetRef, SetLikeRef)


def test_mutable_set_ref_constructs():
    ref = MutableSetRef("my_set")
    assert nu.tree.children(ref)


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
    assert isinstance(ref.exists(), nu.Bool)
    assert isinstance(ref.exists()._source, Exists)
    assert isinstance(ref.exists().not_(), nu.Bool)
    assert isinstance(ref.exists().not_()._source, Not)


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
    assert nu.tree.children(ref)


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
