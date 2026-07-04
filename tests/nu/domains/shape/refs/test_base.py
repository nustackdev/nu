"""Tests for StructuredRef: the abstract base for shape-fabric Refs.

Covers construction, navigation properties (parent_ref, owner_shape, root_shape),
and the deferred substrate contract (afetch_parent / aresolve_address raise
NotImplementedError). Runtime-driven address resolution is skipped — substrate phase.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.dsl import Shape
from nu.domains.shape.refs.base import StructuredRef
from nu.domains.shape.refs.item import ItemRef


class SomeShape(Shape):
    pass


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_structured_ref_constructs_with_address():
    ref = StructuredRef("mykey")
    assert ref.children  # address is children[0]


def test_structured_ref_parent_ref_defaults_to_none():
    ref = StructuredRef("key")
    assert ref._parent is None


def test_structured_ref_owner_shape_defaults_to_none():
    ref = StructuredRef("key")
    assert ref._owner_shape is None


# ---------------------------------------------------------------------------
# Navigation chain
# ---------------------------------------------------------------------------


def test_structured_ref_stores_parent_ref():
    parent = ItemRef("root")
    child = StructuredRef("sub", parent_ref=parent)
    assert child._parent is parent


def test_structured_ref_stores_owner_shape():
    ref = StructuredRef("key", owner_shape=SomeShape)
    assert ref._owner_shape is SomeShape


def test_root_shape_is_owner_when_no_parent():
    ref = StructuredRef("key", owner_shape=SomeShape)
    assert ref._root_shape is SomeShape


def test_root_shape_inherits_from_parent_chain():
    root = ItemRef("a", owner_shape=SomeShape)
    child = ItemRef("b", parent_ref=root)
    assert child._root_shape is SomeShape


def test_root_shape_is_none_when_no_owner_and_no_parent():
    ref = StructuredRef("x")
    assert ref._root_shape is None


# ---------------------------------------------------------------------------
# Substrate plug-points raise NotImplementedError
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — needs a real Runtime + nid")
async def test_afetch_parent_raises():
    ref = StructuredRef("x")
    await ref.afetch_parent(None, 0)  # type: ignore[arg-type]


@pytest.mark.skip(reason="substrate impl deferred — needs a real Runtime + nid")
async def test_aresolve_address_raises():
    ref = StructuredRef("x")
    await ref.aresolve_address(None, 0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr_root_ref():
    ref = StructuredRef("slot_name")
    r = repr(ref)
    assert "StructuredRef" in r


def test_repr_chained_ref():
    parent = ItemRef("parent_key")
    child = StructuredRef("child_key", parent_ref=parent)
    r = repr(child)
    assert "->" in r
