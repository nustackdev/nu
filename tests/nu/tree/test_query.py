"""Tests for nu.tree.query: read-only inspection.

find, find_first, count, size, depth.
"""

from __future__ import annotations

from nu.core import Literal
from nu.flows import Sequential
from nu.tree import count, depth, find, find_first, size


def _is_leaf(n):
    return isinstance(n, Literal)


def _val(v):
    return lambda n: isinstance(n, Literal) and n._payload["value"] == v


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
    assert [n._payload["value"] for n in found] == [1, 2, 3, 4]


def test_find_first_returns_first_preorder_match():
    root = _tree()
    node = find_first(root, _is_leaf)
    assert node._payload["value"] == 1


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
