"""Tests for shape fabric reactive subscription queries.

Covers class hierarchy, construction, and domain placement. Full subscription
(view.on_change() with a real substrate) is deferred to substrate integration.
"""

from __future__ import annotations

import pytest

from nu2.domains.shape.interactions import (
    OnChildChangeQuery,
    OnChildrenChangeQuery,
    OnDescendantsChangeQuery,
)
from nu2.domains.shape.refs.item import ItemRef
from nu2.domains.shape.refs.mapping import ReactiveMappingRef
from nu2.domains.shape.refs.sequence import ReactiveSequenceRef
from nu2.domains.shape.refs.set_ import ReactiveSetRef
from nu2.forms.reactive import OnChangeQuery
from nu2.lang import ScalarQuery


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


# ---------------------------------------------------------------------------
# Domain placement: shape queries live in interactions, not forms.reactive
# ---------------------------------------------------------------------------


def test_on_child_change_query_not_in_forms_reactive():
    """OnChildChangeQuery must NOT be importable from nu2.forms.reactive."""
    import nu2.forms.reactive as generic_reactive

    assert not hasattr(generic_reactive, "OnChildChangeQuery")


def test_on_children_change_query_not_in_forms_reactive():
    import nu2.forms.reactive as generic_reactive

    assert not hasattr(generic_reactive, "OnChildrenChangeQuery")


def test_on_descendants_change_query_not_in_forms_reactive():
    import nu2.forms.reactive as generic_reactive

    assert not hasattr(generic_reactive, "OnDescendantsChangeQuery")


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


# ---------------------------------------------------------------------------
# Reactive Refs expose tree-aware methods that return shape-domain queries
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


# ---------------------------------------------------------------------------
# ReactiveCollectionForm is in the MRO of reactive Refs
# ---------------------------------------------------------------------------


def test_reactive_collection_form_in_mapping_ref_mro():
    from nu2.domains.shape.forms.collection import ReactiveCollectionForm

    assert issubclass(ReactiveMappingRef, ReactiveCollectionForm)


def test_reactive_collection_form_in_sequence_ref_mro():
    from nu2.domains.shape.forms.collection import ReactiveCollectionForm

    assert issubclass(ReactiveSequenceRef, ReactiveCollectionForm)


def test_reactive_collection_form_in_set_ref_mro():
    from nu2.domains.shape.forms.collection import ReactiveCollectionForm

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


# ---------------------------------------------------------------------------
# Substrate deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — view.on_change() needs real backing store")
def test_on_change_returns_subscription_handle():
    pass
