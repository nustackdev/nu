"""Tests for nu.tree.walk: lazy traversal iterators.

preorder, postorder, bfs, leaves, ancestors. Pure structural -- built on
Sequential branches + Literal leaves, never compiled.
"""

from __future__ import annotations

from nu.core import Literal
from nu.flows import Sequential
from nu.tree import ancestors, bfs, leaves, postorder, preorder


def _vals(nodes):
    """Leaf values in iteration order; branches collapse to 'S'."""
    return [n._payload["value"] if isinstance(n, Literal) else "S" for n in nodes]


def _tree():
    """root[ 1, mid[ 2, 3 ], 4 ]."""
    a = Literal(1)
    b = Literal(2)
    c = Literal(3)
    d = Literal(4)
    mid = Sequential(b, c)
    root = Sequential(a, mid, d)
    return root, mid, b


def test_preorder_root_before_children():
    root, _, _ = _tree()
    assert _vals(preorder(root)) == ["S", 1, "S", 2, 3, 4]


def test_postorder_children_before_root():
    root, _, _ = _tree()
    assert _vals(postorder(root)) == [1, 2, 3, "S", 4, "S"]


def test_bfs_level_order():
    root, _, _ = _tree()
    assert _vals(bfs(root)) == ["S", 1, "S", 4, 2, 3]


def test_leaves_only():
    root, _, _ = _tree()
    assert _vals(leaves(root)) == [1, 2, 3, 4]


def test_leaves_of_a_single_leaf_is_itself():
    leaf = Literal(7)
    assert list(leaves(leaf)) == [leaf]


def test_ancestors_path_root_to_target_exclusive():
    root, mid, b = _tree()
    assert ancestors(b, root) == [root, mid]


def test_ancestors_of_root_is_empty():
    root, _, _ = _tree()
    assert ancestors(root, root) == []


def test_ancestors_returns_none_when_not_found():
    root, _, _ = _tree()
    assert ancestors(Literal(99), root) is None
