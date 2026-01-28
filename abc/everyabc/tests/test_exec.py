from __future__ import annotations

from everyabc import Node
from everyabc.tree import Exec, depth, find, map_nodes, preorder, size


class ConcreteExec(Exec):
    """Minimal Exec for testing."""

    def __init__(self, *children):
        super().__init__(*children)


class TestExecIsNode:
    def test_exec_subclass_of_node(self):
        assert issubclass(Exec, Node)

    def test_concrete_exec_is_node(self):
        e = ConcreteExec()
        assert isinstance(e, Node)

    def test_concrete_exec_is_exec(self):
        e = ConcreteExec()
        assert isinstance(e, Exec)


class TestExecInheritsNodeBehavior:
    def test_is_leaf_no_children(self):
        e = ConcreteExec()
        assert e.is_leaf is True

    def test_is_leaf_with_children(self):
        child = ConcreteExec()
        parent = ConcreteExec(child)
        assert parent.is_leaf is False

    def test_child_count(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a, b)
        assert parent.child_count == 2

    def test_children_tuple(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a, b)
        assert parent.children == (a, b)

    def test_append(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a)
        new_parent = parent.append(b)
        assert new_parent.child_count == 2

    def test_prepend(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(b)
        new_parent = parent.prepend(a)
        assert new_parent.child_count == 2

    def test_len(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a, b)
        assert len(parent) == 2

    def test_iter(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a, b)
        assert list(parent) == [a, b]

    def test_getitem(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a, b)
        assert parent[0] is a
        assert parent[1] is b

    def test_contains(self):
        a = ConcreteExec()
        b = ConcreteExec()
        parent = ConcreteExec(a)
        assert a in parent
        assert b not in parent


class TestExecWithAstOperations:
    def test_preorder(self):
        c1 = ConcreteExec()
        c2 = ConcreteExec()
        root = ConcreteExec(c1, c2)
        nodes = list(preorder(root))
        assert len(nodes) == 3
        assert nodes[0] is root
        assert nodes[1] is c1
        assert nodes[2] is c2

    def test_map_nodes(self):
        c1 = ConcreteExec()
        c2 = ConcreteExec()
        root = ConcreteExec(c1, c2)

        def identity(n):
            return n

        result = map_nodes(root, identity)
        assert result.child_count == 2

    def test_find(self):
        c1 = ConcreteExec()
        c2 = ConcreteExec()
        root = ConcreteExec(c1, c2)
        found = find(root, lambda n: n.is_leaf)
        assert len(found) == 2

    def test_size(self):
        c1 = ConcreteExec()
        c2 = ConcreteExec()
        root = ConcreteExec(c1, c2)
        assert size(root) == 3

    def test_depth(self):
        leaf = ConcreteExec()
        mid = ConcreteExec(leaf)
        root = ConcreteExec(mid)
        assert depth(root) == 2
