"""Tests for _Node - the immutable tree data structure.

_Node is the structural backbone. Every Nu is a _Node. If immutability
breaks here, the entire transformation model collapses.
"""

from __future__ import annotations

from tests.conftest import StubNu


# ---------------------------------------------------------------------------
# Children access
# ---------------------------------------------------------------------------


def test_children_is_tuple():
    node = StubNu("a", StubNu("b"), StubNu("c"))
    assert isinstance(node.children, tuple)


def test_leaf_no_children():
    leaf = StubNu("x")
    assert leaf._is_leaf
    assert leaf._child_count == 0
    assert leaf.children == ()


def test_parent_has_children():
    a, b = StubNu("a"), StubNu("b")
    parent = StubNu("p", a, b)
    assert not parent._is_leaf
    assert parent._child_count == 2


def test_get_child():
    a, b = StubNu("a"), StubNu("b")
    parent = StubNu("p", a, b)
    assert parent._get_child(0) is a
    assert parent._get_child(1) is b


def test_iter_children():
    a, b, c = StubNu("a"), StubNu("b"), StubNu("c")
    parent = StubNu("p", a, b, c)
    assert list(parent._iter_children()) == [a, b, c]


def test_has_child_uses_identity():
    a = StubNu("a")
    a_equal = StubNu("a")  # same label, different object
    parent = StubNu("p", a)
    assert parent._has_child(a)
    assert not parent._has_child(a_equal)


# ---------------------------------------------------------------------------
# Immutability - every mutation returns a NEW node, original untouched
# ---------------------------------------------------------------------------


def test_append_child_returns_new():
    a = StubNu("a")
    parent = StubNu("p", a)
    new_child = StubNu("b")
    new_parent = parent._append_child(new_child)

    assert new_parent is not parent
    assert new_parent._child_count == 2
    assert parent._child_count == 1  # original untouched


def test_prepend_child_returns_new():
    a = StubNu("a")
    parent = StubNu("p", a)
    new_child = StubNu("b")
    new_parent = parent._prepend_child(new_child)

    assert new_parent is not parent
    assert new_parent._get_child(0) is new_child
    assert new_parent._get_child(1) is a
    assert parent._child_count == 1


def test_insert_child_returns_new():
    a, c = StubNu("a"), StubNu("c")
    parent = StubNu("p", a, c)
    b = StubNu("b")
    new_parent = parent._insert_child(1, b)

    assert new_parent is not parent
    assert new_parent._child_count == 3
    assert new_parent._get_child(1) is b
    assert parent._child_count == 2


def test_remove_child_returns_new():
    a, b = StubNu("a"), StubNu("b")
    parent = StubNu("p", a, b)
    new_parent = parent._remove_child(0)

    assert new_parent is not parent
    assert new_parent._child_count == 1
    assert new_parent._get_child(0) is b
    assert parent._child_count == 2


def test_replace_child_returns_new():
    a, b = StubNu("a"), StubNu("b")
    parent = StubNu("p", a)
    new_parent = parent._replace_child(0, b)

    assert new_parent is not parent
    assert new_parent._get_child(0) is b
    assert parent._get_child(0) is a


# ---------------------------------------------------------------------------
# with_children - reconstruction
# ---------------------------------------------------------------------------


def test_with_children_same_returns_self():
    """Identity optimization: same children -> same node."""
    a, b = StubNu("a"), StubNu("b")
    parent = StubNu("p", a, b)
    same = parent._with_children(a, b)
    assert same is parent


def test_with_children_different_returns_new():
    a, b = StubNu("a"), StubNu("b")
    parent = StubNu("p", a)
    new_parent = parent._with_children(a, b)
    assert new_parent is not parent
    assert new_parent._child_count == 2


def test_with_children_preserves_subclass_attrs():
    """copy.copy preserves _label and other instance state."""
    parent = StubNu("my_label", StubNu("a"))
    new_parent = parent._with_children(StubNu("b"))

    assert new_parent._label == "my_label"
    assert new_parent is not parent


# ---------------------------------------------------------------------------
# Bool
# ---------------------------------------------------------------------------


def test_bool_always_true():
    """A node always exists - prevents accidental falsy checks."""
    assert bool(StubNu()) is True
    assert bool(StubNu(None)) is True
    assert bool(StubNu("x", StubNu("a"))) is True
