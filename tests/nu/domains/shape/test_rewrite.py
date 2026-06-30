"""Tests for domains.shape.rewrite: annotate_ref_loads and substrate optimizer helpers.

annotate_ref_loads wraps bare shape Refs with LoadQuery and is testable
with the base nu tree. extract_static_address / walk_ref_chain /
reconstruct_with_flat_ref are substrate optimizer helpers that require
substrate-specific Ref attributes (_raw_address, parent as property); those
are skipped here.
"""

from __future__ import annotations

import pytest

from nu.core import LiteralQuery
from nu.domains.shape.interactions import LoadQuery
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.rewrite import (
    annotate_ref_loads,
    extract_static_address,
    walk_ref_chain,
)


# ---------------------------------------------------------------------------
# annotate_ref_loads
# ---------------------------------------------------------------------------


def test_annotate_wraps_bare_shape_ref_child():
    ref = ItemRef("slot")
    # build a LoadQuery so we have a non-leaf node with a shape Ref child
    # then use a LiteralQuery wrapping the ref as a proxy node
    # Actually, let's use a LoadQuery wrapping the ref — its child IS the ref
    # annotate_ref_loads skips nodes that are already LoadQuery, so use a proxy
    from nu.domains.shape.interactions import ExistsQuery

    node = ExistsQuery(ref)
    result = annotate_ref_loads(node)
    # The child ref should now be wrapped in LoadQuery
    # ExistsQuery child[0] should be a LoadQuery wrapping the ItemRef
    assert isinstance(result.children[0], LoadQuery)


def test_annotate_does_not_double_wrap_load_query():
    ref = ItemRef("slot")
    already_wrapped = LoadQuery(ref)
    result = annotate_ref_loads(already_wrapped)
    # The LoadQuery itself should be unchanged
    assert isinstance(result, LoadQuery)
    # And its child should still be the ItemRef, not a double-wrapped LoadQuery
    assert not isinstance(result.children[0], LoadQuery)


def test_annotate_is_idempotent():
    from nu.domains.shape.interactions import ExistsQuery

    ref = ItemRef("slot")
    node = ExistsQuery(ref)
    once = annotate_ref_loads(node)
    twice = annotate_ref_loads(once)
    # After two passes, child should still be a single LoadQuery
    assert isinstance(twice.children[0], LoadQuery)
    assert not isinstance(twice.children[0].children[0], LoadQuery)


def test_annotate_leaves_literal_children_untouched():
    q = LiteralQuery(42)
    result = annotate_ref_loads(q)
    assert result is q


# ---------------------------------------------------------------------------
# Substrate optimizer helpers — extract_static_address / walk_ref_chain
# ---------------------------------------------------------------------------


def test_extract_static_address_returns_literal_for_string_key():
    # _StructuredRef wraps plain Python literals as LiteralQuery via Nu.__init__
    ref = ItemRef("my_slot")
    result = extract_static_address(ref)
    assert result == "my_slot"


def test_extract_static_address_returns_literal_for_int_key():
    ref = ItemRef(42)
    result = extract_static_address(ref)
    assert result == 42


def test_extract_static_address_returns_none_for_dynamic_address():
    # A Nu node (e.g. another ItemRef) as the address is dynamic
    dyn = ItemRef("cursor")
    ref = ItemRef(dyn)  # dyn is a Term, not wrapped in LiteralQuery
    result = extract_static_address(ref)
    assert result is None


def test_walk_ref_chain_single_ref_returns_one_entry():
    ref = ItemRef("slot")
    addresses, address_terms = walk_ref_chain(ref)
    assert addresses == ["slot"]
    assert address_terms == [None]  # static → no address term


def test_walk_ref_chain_two_deep_root_to_leaf_order():
    root = ItemRef("root_addr")
    child = ItemRef("child_addr", parent_ref=root)
    addresses, address_terms = walk_ref_chain(child)
    # returned in root-to-leaf order
    assert addresses == ["root_addr", "child_addr"]
    assert address_terms == [None, None]


def test_walk_ref_chain_dynamic_address_has_address_term():
    cursor = ItemRef("cursor")
    ref = ItemRef(cursor)  # dynamic address
    addresses, address_terms = walk_ref_chain(ref)
    assert addresses == [None]
    assert address_terms[0] is cursor  # the Nu node passed as address


@pytest.mark.skip(reason="substrate impl deferred — requires node.ref attribute on substrate nodes")
def test_reconstruct_with_flat_ref_swaps_ref_child():
    pass
