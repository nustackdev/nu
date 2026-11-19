"""Tests for nu.tree.query: read-only inspection.

children, fields, payload, find, find_first, count, size, depth, equal.
"""

from __future__ import annotations

import nu
from nu.core.flows import Sequential
from nu.lang import Literal
from nu.tree import count, depth, find, find_first, size


def _is_leaf(n):
    return isinstance(n, Literal)


def _val(v):
    return lambda n: isinstance(n, Literal) and nu.tree.fields(n)["value"] == v


def _tree():
    """root[ 1, mid[ 2, 3 ], 4 ] -- 6 nodes, depth 2."""
    return Sequential(
        Literal(1),
        Sequential(Literal(2), Literal(3)),
        Literal(4),
    )


def test_find_returns_all_matches_in_preorder():
    root = _tree()
    found = find(root, _is_leaf)
    assert [nu.tree.fields(n)["value"] for n in found] == [1, 2, 3, 4]


def test_find_first_returns_first_preorder_match():
    root = _tree()
    node = find_first(root, _is_leaf)
    assert nu.tree.fields(node)["value"] == 1


def test_find_first_returns_none_when_no_match():
    root = _tree()
    assert find_first(root, _val(99)) is None


def test_count_with_predicate():
    root = _tree()
    assert count(root, _is_leaf) == 4


def test_count_none_counts_all_nodes():
    root = _tree()
    assert count(root) == 6


def test_size_is_total_node_count():
    root = _tree()
    assert size(root) == 6


def test_depth_of_leaf_is_zero():
    assert depth(Literal(1)) == 0


def test_depth_counts_deepest_path():
    root = _tree()
    assert depth(root) == 2


# --- children / payload / equal -------------------------------------------------


def test_children_are_the_direct_children_in_slot_order():
    root = _tree()
    kids = nu.tree.children(root)
    assert len(kids) == 3
    assert [nu.tree.fields(k).get("value") for k in kids] == [1, None, 4]


def test_field_values_are_shared_by_a_rewrite_that_keeps_them():
    held = object()
    lit = Literal(held)
    variant = nu.tree.map_children(lit, lambda c: c)
    assert variant.value is held


def test_equal_compares_kinds_fields_and_children():
    assert nu.tree.equal(_tree(), _tree())
    assert nu.tree.equal(nu.Int(1) + 2, nu.Int(1) + 2)
    assert not nu.tree.equal(nu.Add(1, 2), nu.Add(1, 3))
    assert not nu.tree.equal(nu.Add(1, 2), nu.Sub(1, 2))
    assert not nu.tree.equal(nu.Add(1, 2), nu.Add(1, 2, 3))


def test_equal_tells_literal_types_apart():
    assert not nu.tree.equal(Literal(1), Literal(1.0))
    assert not nu.tree.equal(Literal(1), Literal(True))


def test_equal_descends_into_terms_held_as_values():
    a = nu.TryCatch(nu.print("x"), catch=nu.print("a"))
    b = nu.TryCatch(nu.print("x"), catch=nu.print("a"))
    c = nu.TryCatch(nu.print("x"), catch=nu.print("b"))
    assert nu.tree.equal(a, b)
    assert not nu.tree.equal(a, c)


def test_fields_are_instance_attributes_minus_the_children():
    assert nu.tree.fields(Literal(7)) == {"value": 7}
    assert "_children" not in nu.tree.fields(_tree())


def test_fields_is_a_snapshot():
    lit = Literal(7)
    nu.tree.fields(lit)["value"] = 8
    assert lit.value == 7


def test_equal_descends_into_a_term_held_in_a_literal():
    assert nu.tree.equal(Literal(nu.Add(1, 2)), Literal(nu.Add(1, 2)))
    assert not nu.tree.equal(Literal(nu.Add(1, 2)), Literal(nu.Add(1, 3)))
