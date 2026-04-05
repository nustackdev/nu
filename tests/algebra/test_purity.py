"""Tests for purity propagation through trees.

is_self_pure is a per-Nu classification. is_subtree_pure propagates
through the tree: one impure Nu at any depth taints the entire path
up to root. This property is the foundation for algebraic transformations
(reordering, parallelization, caching).
"""

from __future__ import annotations

from tests.conftest import FailingNu, StubNu

from nu import Value


# ---------------------------------------------------------------------------
# Leaf purity
# ---------------------------------------------------------------------------


def test_value_is_pure():
    assert Value(42).is_self_pure is True
    assert Value(42).is_subtree_pure is True


def test_stub_nu_is_pure():
    assert StubNu("x").is_self_pure is True
    assert StubNu("x").is_subtree_pure is True


def test_failing_nu_is_impure():
    assert FailingNu().is_self_pure is False
    assert FailingNu().is_subtree_pure is False


# ---------------------------------------------------------------------------
# Subtree propagation
# ---------------------------------------------------------------------------


def test_all_pure_children():
    """Tree of pure leaves -> subtree pure."""
    tree = StubNu("root", StubNu("a"), StubNu("b"), StubNu("c"))
    assert tree.is_subtree_pure is True


def test_one_impure_child():
    """Single impure child taints the parent."""
    tree = StubNu("root", StubNu("a"), FailingNu())
    assert tree.is_self_pure is True  # parent itself is pure
    assert tree.is_subtree_pure is False  # but subtree is not


def test_deep_impure_propagation():
    """Impure leaf at depth 3 poisons the entire path to root."""
    impure_leaf = FailingNu()
    depth2 = StubNu("d2", impure_leaf)
    depth1 = StubNu("d1", depth2)
    root = StubNu("root", depth1, StubNu("clean"))

    assert root.is_subtree_pure is False
    assert depth1.is_subtree_pure is False
    assert depth2.is_subtree_pure is False


def test_pure_sibling_unaffected():
    """A pure sibling subtree remains pure even if another sibling is impure."""
    clean_branch = StubNu("clean", StubNu("a"), StubNu("b"))
    dirty_branch = StubNu("dirty", FailingNu())

    assert clean_branch.is_subtree_pure is True
    assert dirty_branch.is_subtree_pure is False


def test_leaf_subtree_equals_self():
    """For a leaf, is_subtree_pure == is_self_pure (no children to check)."""
    pure = StubNu("p")
    impure = FailingNu()
    assert pure.is_subtree_pure == pure.is_self_pure
    assert impure.is_subtree_pure == impure.is_self_pure
