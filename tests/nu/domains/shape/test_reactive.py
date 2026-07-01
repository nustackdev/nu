"""Tests for shape fabric reactive subscription queries.

Covers class hierarchy, construction, and domain placement. Full subscription
(view.on_change() with a real substrate) is deferred to substrate integration.

Reactive queries all live in ``nu.core.reactive`` -- unified interface across
substrates. Shape Form mixins reach into that module.
"""

from __future__ import annotations

import pytest

from nu.core.reactive import (
    OnChangeQuery,
    OnChildChangeQuery,
    OnChildrenChangeQuery,
    OnDescendantsChangeQuery,
    OnPrimitiveChangeQuery,
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
    assert issubclass(OnChangeQuery, ScalarQuery)


def test_on_child_change_query_is_scalar_query():
    assert issubclass(OnChildChangeQuery, ScalarQuery)


def test_on_children_change_query_is_scalar_query():
    assert issubclass(OnChildrenChangeQuery, ScalarQuery)


def test_on_descendants_change_query_is_scalar_query():
    assert issubclass(OnDescendantsChangeQuery, ScalarQuery)


def test_on_primitive_change_query_is_scalar_query():
    assert issubclass(OnPrimitiveChangeQuery, ScalarQuery)


# ---------------------------------------------------------------------------
# Domain placement: all reactive queries live in nu.core.reactive
# ---------------------------------------------------------------------------


def test_all_reactive_queries_exported_from_core():
    """Every reactive query is reachable via ``nu.core.reactive`` (one namespace)."""
    import nu.core.reactive as core_reactive

    for name in (
        "OnChangeQuery",
        "OnChildChangeQuery",
        "OnChildrenChangeQuery",
        "OnDescendantsChangeQuery",
        "OnPrimitiveChangeQuery",
    ):
        assert hasattr(core_reactive, name)


def test_all_reactive_queries_also_flat_on_nu_core():
    """The core-flat re-exports include the reactive queries."""
    import nu.core as core

    for name in (
        "OnChangeQuery",
        "OnChildChangeQuery",
        "OnChildrenChangeQuery",
        "OnDescendantsChangeQuery",
        "OnPrimitiveChangeQuery",
    ):
        assert hasattr(core, name)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_on_change_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = OnChangeQuery(ref)
    assert q.children


def test_on_child_change_query_constructs_with_two_children():
    ref = ItemRef("slot")
    address = ItemRef("addr")
    q = OnChildChangeQuery(ref, address)
    assert len(q.children) == 2


def test_on_children_change_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = OnChildrenChangeQuery(ref)
    assert q.children


def test_on_descendants_change_query_constructs_with_ref_and_pattern():
    ref = ItemRef("slot")
    q = OnDescendantsChangeQuery(ref, ItemRef("pattern"))
    assert len(q.children) == 2


def test_on_primitive_change_query_constructs_with_ref():
    ref = ReactiveItemRef("slot")
    q = OnPrimitiveChangeQuery(ref)
    assert q.children


# ---------------------------------------------------------------------------
# Reactive Refs expose tree-aware methods that return core reactive queries
# ---------------------------------------------------------------------------


def test_reactive_mapping_ref_on_child_change_returns_shape_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_child_change("k"), OnChildChangeQuery)


def test_reactive_mapping_ref_on_children_change_returns_shape_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_children_change(), OnChildrenChangeQuery)


def test_reactive_mapping_ref_on_descendants_change_returns_shape_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_descendants_change("a"), OnDescendantsChangeQuery)


def test_reactive_mapping_ref_on_change_returns_generic_query():
    r = ReactiveMappingRef("m")
    assert isinstance(r.on_change(), OnChangeQuery)


def test_reactive_sequence_ref_on_child_change_returns_shape_query():
    s = ReactiveSequenceRef("s")
    assert isinstance(s.on_child_change(0), OnChildChangeQuery)


def test_reactive_sequence_ref_on_children_change_returns_shape_query():
    s = ReactiveSequenceRef("s")
    assert isinstance(s.on_children_change(), OnChildrenChangeQuery)


def test_reactive_sequence_ref_on_change_returns_generic_query():
    s = ReactiveSequenceRef("s")
    assert isinstance(s.on_change(), OnChangeQuery)


def test_reactive_set_ref_on_children_change_returns_shape_query():
    r = ReactiveSetRef("s")
    assert isinstance(r.on_children_change(), OnChildrenChangeQuery)


def test_reactive_set_ref_on_change_returns_generic_query():
    r = ReactiveSetRef("s")
    assert isinstance(r.on_change(), OnChangeQuery)


def test_reactive_item_ref_on_change_returns_primitive_query():
    r = ReactiveItemRef("slot")
    assert isinstance(r.on_change(), OnPrimitiveChangeQuery)


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
    mutates = OnChangeQuery.attributes.get("mutates")
    assert mutates is None


def test_on_child_change_query_has_no_mutates():
    mutates = OnChildChangeQuery.attributes.get("mutates")
    assert mutates is None


def test_on_children_change_query_has_no_mutates():
    mutates = OnChildrenChangeQuery.attributes.get("mutates")
    assert mutates is None


def test_on_primitive_change_query_has_no_mutates():
    mutates = OnPrimitiveChangeQuery.attributes.get("mutates")
    assert mutates is None


# ---------------------------------------------------------------------------
# Substrate deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — view.on_change() needs real backing store")
def test_on_change_returns_subscription_handle():
    pass
