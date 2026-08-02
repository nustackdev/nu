"""Tests for shape fabric reactive subscription queries.

Covers class hierarchy, construction, and domain placement. Full subscription
(view.on_change() with a real substrate) is deferred to substrate integration.

Reactive queries all live in ``nu.core.reactive`` -- unified interface across
substrates. Shape Form mixins reach into that module.
"""

from __future__ import annotations

import pytest

from nu.core.reactive import (
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
    OnPrimitiveChange,
)
from nu.domains.shape.refs.item import ItemRef, ReactiveItemRef
from nu.domains.shape.refs.mapping import ReactiveMappingRef
from nu.domains.shape.refs.sequence import ReactiveSequenceRef
from nu.domains.shape.refs.set_ import ReactiveSetRef
from nu.lang import ScalarQuery


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_on_change_query_is_scalar_query():
    assert issubclass(OnChange, ScalarQuery)


def test_on_child_change_query_is_scalar_query():
    assert issubclass(OnChildChange, ScalarQuery)


def test_on_children_change_query_is_scalar_query():
    assert issubclass(OnChildrenChange, ScalarQuery)


def test_on_descendants_change_query_is_scalar_query():
    assert issubclass(OnDescendantsChange, ScalarQuery)


def test_on_primitive_change_query_is_scalar_query():
    assert issubclass(OnPrimitiveChange, ScalarQuery)


# ---------------------------------------------------------------------------
# Domain placement: all reactive queries live in nu.core.reactive
# ---------------------------------------------------------------------------


def test_all_reactive_queries_exported_from_core():
    """Every reactive query is reachable via ``nu.core.reactive`` (one namespace)."""
    import nu.core.reactive as core_reactive

    for name in (
        "OnChange",
        "OnChildChange",
        "OnChildrenChange",
        "OnDescendantsChange",
        "OnPrimitiveChange",
    ):
        assert hasattr(core_reactive, name)


def test_all_reactive_queries_also_flat_on_nu_core():
    """The core-flat re-exports include the reactive queries."""
    import nu.core as core

    for name in (
        "OnChange",
        "OnChildChange",
        "OnChildrenChange",
        "OnDescendantsChange",
        "OnPrimitiveChange",
    ):
        assert hasattr(core, name)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_on_change_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = OnChange(ref)
    assert q._children


def test_on_child_change_query_constructs_with_two_children():
    ref = ItemRef("slot")
    address = ItemRef("addr")
    q = OnChildChange(ref, address)
    assert len(q._children) == 2


def test_on_children_change_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = OnChildrenChange(ref)
    assert q._children


def test_on_descendants_change_query_constructs_with_ref_and_pattern():
    ref = ItemRef("slot")
    q = OnDescendantsChange(ref, ItemRef("pattern"))
    assert len(q._children) == 2


def test_on_primitive_change_query_constructs_with_ref():
    ref = ReactiveItemRef("slot")
    q = OnPrimitiveChange(ref)
    assert q._children


# ---------------------------------------------------------------------------
# Reactive Refs expose tree-aware methods that return core reactive queries
# ---------------------------------------------------------------------------


def test_reactive_mapping_ref_on_child_change_returns_shape_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_child_change("k"), OnChildChange)


def test_reactive_mapping_ref_on_children_change_returns_shape_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_children_change(), OnChildrenChange)


def test_reactive_mapping_ref_on_descendants_change_returns_shape_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_descendants_change("a"), OnDescendantsChange)


def test_reactive_mapping_ref_on_change_returns_generic_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_change(), OnChange)


def test_reactive_sequence_ref_on_child_change_returns_shape_query():
    s = ReactiveSequenceRef("s")
    assert isinstance(s.on_child_change(0), OnChildChange)


def test_reactive_sequence_ref_on_children_change_returns_shape_query():
    s = ReactiveSequenceRef("s")
    assert isinstance(s.on_children_change(), OnChildrenChange)


def test_reactive_sequence_ref_on_change_returns_generic_query():
    s = ReactiveSequenceRef("s")
    assert isinstance(s.on_change(), OnChange)


def test_reactive_set_ref_on_children_change_returns_shape_query():
    r = ReactiveSetRef("s")
    assert isinstance(r.on_children_change(), OnChildrenChange)


def test_reactive_set_ref_on_change_returns_generic_query():
    r = ReactiveSetRef("s")
    assert isinstance(r.on_change(), OnChange)


def test_reactive_item_ref_on_change_returns_primitive_query():
    r = ReactiveItemRef("slot")
    assert isinstance(r.on_change(), OnPrimitiveChange)


# ---------------------------------------------------------------------------
# ReactiveCollectionForm is in the MRO of reactive Refs
# ---------------------------------------------------------------------------


def test_reactive_collection_form_in_mapping_ref_mro():
    from nu.domains.shape.forms.collection import ReactiveCollectionForm

    assert issubclass(ReactiveMappingRef, ReactiveCollectionForm)


def test_reactive_collection_form_in_sequence_ref_mro():
    from nu.domains.shape.forms.collection import ReactiveCollectionForm

    assert issubclass(ReactiveSequenceRef, ReactiveCollectionForm)


def test_reactive_collection_form_in_set_ref_mro():
    from nu.domains.shape.forms.collection import ReactiveCollectionForm

    assert issubclass(ReactiveSetRef, ReactiveCollectionForm)


# ---------------------------------------------------------------------------
# No mutates declaration (observer registry, not fabric write)
# ---------------------------------------------------------------------------


def test_on_change_query_has_no_mutates():
    mutates = OnChange._attributes.get("mutates")
    assert mutates is None


def test_on_child_change_query_has_no_mutates():
    mutates = OnChildChange._attributes.get("mutates")
    assert mutates is None


def test_on_children_change_query_has_no_mutates():
    mutates = OnChildrenChange._attributes.get("mutates")
    assert mutates is None


def test_on_primitive_change_query_has_no_mutates():
    mutates = OnPrimitiveChange._attributes.get("mutates")
    assert mutates is None


# ---------------------------------------------------------------------------
# Substrate deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — view.on_change() needs real backing store")
def test_on_change_returns_subscription_handle():
    pass
