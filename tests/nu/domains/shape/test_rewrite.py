"""Tests for domains.shape.rewrite substrate optimizer helpers.

extract_static_address / walk_ref_chain / reconstruct_with_flat_ref are the
substrate inline-ref building blocks.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.rewrite import (
    extract_static_address,
    walk_ref_chain,
)


# ---------------------------------------------------------------------------
# Substrate optimizer helpers — extract_static_address / walk_ref_chain
# ---------------------------------------------------------------------------


def test_extract_static_address_returns_literal_for_string_key():
    # StructuredRef wraps plain Python literals as LiteralQuery via Nu.__init__
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
