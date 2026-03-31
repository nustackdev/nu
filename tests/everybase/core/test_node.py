from __future__ import annotations

import pytest

from nu import Node

from .conftest import SimpleNode


class TestChildren:
    def test_base_node_children_is_empty_tuple(self):
        node = Node()
        assert node.children == ()
        assert isinstance(node.children, tuple)

    def test_simple_node_leaf_children(self):
        leaf = SimpleNode("x")
        assert leaf.children == ()

    def test_simple_node_branch_children(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        assert parent.children == (a, b)
        assert isinstance(parent.children, tuple)


class TestIsLeaf:
    def test_leaf_is_leaf(self):
        leaf = SimpleNode("x")
        assert leaf.is_leaf is True

    def test_branch_is_not_leaf(self):
        child = SimpleNode("c")
        parent = SimpleNode("p", child)
        assert parent.is_leaf is False

    def test_base_node_is_leaf(self):
        node = Node()
        assert node.is_leaf is True


class TestChildCount:
    def test_leaf_child_count(self):
        leaf = SimpleNode("x")
        assert leaf.child_count == 0

    def test_branch_child_count(self):
        parent = SimpleNode("p", SimpleNode("a"), SimpleNode("b"), SimpleNode("c"))
        assert parent.child_count == 3


class TestWithChildren:
    def test_leaf_with_no_args_returns_self(self):
        leaf = SimpleNode("x")
        result = leaf.with_children()
        assert result is leaf

    def test_base_node_leaf_with_no_args_returns_self(self):
        node = Node()
        result = node.with_children()
        assert result is node

    def test_base_node_with_children_works(self):
        node = Node()
        child = Node()
        result = node.with_children(child)
        assert result.children == (child,)
        assert isinstance(result, Node)

    def test_with_children_rebuilds_node(self):
        parent = SimpleNode("p", SimpleNode("a"))
        new_child = SimpleNode("b")
        result = parent.with_children(new_child)
        assert result.children == (new_child,)
        assert result.label == "p"

    def test_with_children_preserves_label(self):
        parent = SimpleNode("original", SimpleNode("a"))
        result = parent.with_children(SimpleNode("b"))
        assert result.label == "original"


class TestGetChild:
    def test_get_child_int(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        assert parent.get_child(0) is a
        assert parent.get_child(1) is b

    def test_get_child_negative(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        assert parent.get_child(-1) is b

    def test_get_child_out_of_range(self):
        parent = SimpleNode("p", SimpleNode("a"))
        with pytest.raises(IndexError):
            parent.get_child(5)


class TestIterChildren:
    def test_iter_children_leaf(self):
        leaf = SimpleNode("x")
        assert list(leaf.iter_children()) == []

    def test_iter_children_branch(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        assert list(parent.iter_children()) == [a, b]

    def test_iter_children_for_loop(self):
        children = [SimpleNode("a"), SimpleNode("b"), SimpleNode("c")]
        parent = SimpleNode("p", *children)
        collected = []
        for child in parent.iter_children():
            collected.append(child)
        assert collected == children


class TestHasChild:
    def test_has_child_by_identity(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        assert parent.has_child(a)
        assert parent.has_child(b)

    def test_has_child_not_found(self):
        a = SimpleNode("a")
        other = SimpleNode("a")  # same label, different object
        parent = SimpleNode("p", a)
        assert not parent.has_child(other)

    def test_has_child_uses_identity_not_equality(self):
        a = SimpleNode("a")
        equal_a = SimpleNode("a")
        parent = SimpleNode("p", a)
        assert a == equal_a  # they are equal
        assert not parent.has_child(equal_a)  # but different identity


class TestAppendChild:
    def test_append_child_to_leaf(self):
        leaf = SimpleNode("p")
        child = SimpleNode("a")
        result = leaf.append_child(child)
        assert result.children == (child,)
        assert result.label == "p"

    def test_append_child_to_branch(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a)
        result = parent.append_child(b)
        assert result.children == (a, b)

    def test_append_child_does_not_mutate_original(self):
        a = SimpleNode("a")
        parent = SimpleNode("p", a)
        parent.append_child(SimpleNode("b"))
        assert parent.children == (a,)


class TestPrependChild:
    def test_prepend_child_to_leaf(self):
        leaf = SimpleNode("p")
        child = SimpleNode("a")
        result = leaf.prepend_child(child)
        assert result.children == (child,)

    def test_prepend_child_to_branch(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", b)
        result = parent.prepend_child(a)
        assert result.children == (a, b)


class TestInsertChild:
    def test_insert_child_at_beginning(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", b)
        result = parent.insert_child(0, a)
        assert result.children == (a, b)

    def test_insert_child_in_middle(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        c = SimpleNode("c")
        parent = SimpleNode("p", a, c)
        result = parent.insert_child(1, b)
        assert result.children == (a, b, c)

    def test_insert_child_at_end(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a)
        result = parent.insert_child(1, b)
        assert result.children == (a, b)


class TestRemoveChild:
    def test_remove_child_first(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        result = parent.remove_child(0)
        assert result.children == (b,)

    def test_remove_child_last(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        result = parent.remove_child(1)
        assert result.children == (a,)

    def test_remove_child_does_not_mutate_original(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        parent.remove_child(0)
        assert parent.children == (a, b)


class TestReplaceChild:
    def test_replace_child(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        c = SimpleNode("c")
        parent = SimpleNode("p", a, b)
        result = parent.replace_child(1, c)
        assert result.children == (a, c)

    def test_replace_child_does_not_mutate_original(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a)
        parent.replace_child(0, b)
        assert parent.children == (a,)


class TestBool:
    def test_leaf_is_truthy(self):
        assert bool(SimpleNode("x")) is True

    def test_branch_is_truthy(self):
        assert bool(SimpleNode("p", SimpleNode("a"))) is True

    def test_base_node_is_truthy(self):
        assert bool(Node()) is True


class TestRepr:
    def test_repr_base_node_leaf(self):
        node = Node()
        assert repr(node) == "Node()"

    def test_repr_simple_node_leaf(self):
        node = SimpleNode("x")
        assert repr(node) == "SimpleNode('x')"

    def test_repr_simple_node_branch(self):
        parent = SimpleNode("p", SimpleNode("a"), SimpleNode("b"))
        assert repr(parent) == "SimpleNode('p', ...2)"


class TestImmutability:
    def test_append_child_does_not_mutate(self):
        a = SimpleNode("a")
        parent = SimpleNode("p", a)
        original_children = parent.children
        parent.append_child(SimpleNode("b"))
        assert parent.children is original_children

    def test_prepend_child_does_not_mutate(self):
        a = SimpleNode("a")
        parent = SimpleNode("p", a)
        original_children = parent.children
        parent.prepend_child(SimpleNode("b"))
        assert parent.children is original_children

    def test_insert_child_does_not_mutate(self):
        a = SimpleNode("a")
        parent = SimpleNode("p", a)
        original_children = parent.children
        parent.insert_child(0, SimpleNode("b"))
        assert parent.children is original_children

    def test_remove_child_does_not_mutate(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)
        original_children = parent.children
        parent.remove_child(0)
        assert parent.children is original_children

    def test_replace_child_does_not_mutate(self):
        a = SimpleNode("a")
        parent = SimpleNode("p", a)
        original_children = parent.children
        parent.replace_child(0, SimpleNode("b"))
        assert parent.children is original_children
