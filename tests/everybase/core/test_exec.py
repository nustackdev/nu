from __future__ import annotations

from nu import Executable, Node, depth, find, map_nodes, preorder, size


class ConcreteExecutable(Executable):
    """Minimal Executable for testing."""

    def __init__(self, *children):
        super().__init__(*children)


class TestExecutableIsNode:
    def test_exec_subclass_of_node(self):
        assert issubclass(Executable, Node)

    def test_concrete_exec_is_node(self):
        e = ConcreteExecutable()
        assert isinstance(e, Node)

    def test_concrete_exec_is_exec(self):
        e = ConcreteExecutable()
        assert isinstance(e, Executable)


class TestExecutableInheritsNodeBehavior:
    def test_is_leaf_no_children(self):
        e = ConcreteExecutable()
        assert e.is_leaf is True

    def test_is_leaf_with_children(self):
        child = ConcreteExecutable()
        parent = ConcreteExecutable(child)
        assert parent.is_leaf is False

    def test_child_count(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(a, b)
        assert parent.child_count == 2

    def test_children_tuple(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(a, b)
        assert parent.children == (a, b)

    def test_append_child(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(a)
        new_parent = parent.append_child(b)
        assert new_parent.child_count == 2

    def test_prepend_child(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(b)
        new_parent = parent.prepend_child(a)
        assert new_parent.child_count == 2

    def test_get_child(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(a, b)
        assert parent.get_child(0) is a
        assert parent.get_child(1) is b

    def test_iter_children(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(a, b)
        assert list(parent.iter_children()) == [a, b]

    def test_has_child(self):
        a = ConcreteExecutable()
        b = ConcreteExecutable()
        parent = ConcreteExecutable(a)
        assert parent.has_child(a)
        assert not parent.has_child(b)


class TestExecutableWithAstOperations:
    def test_preorder(self):
        c1 = ConcreteExecutable()
        c2 = ConcreteExecutable()
        root = ConcreteExecutable(c1, c2)
        nodes = list(preorder(root))
        assert len(nodes) == 3
        assert nodes[0] is root
        assert nodes[1] is c1
        assert nodes[2] is c2

    def test_map_nodes(self):
        c1 = ConcreteExecutable()
        c2 = ConcreteExecutable()
        root = ConcreteExecutable(c1, c2)

        def identity(n):
            return n

        result = map_nodes(root, identity)
        assert result.child_count == 2

    def test_find(self):
        c1 = ConcreteExecutable()
        c2 = ConcreteExecutable()
        root = ConcreteExecutable(c1, c2)
        found = find(root, lambda n: n.is_leaf)
        assert len(found) == 2

    def test_size(self):
        c1 = ConcreteExecutable()
        c2 = ConcreteExecutable()
        root = ConcreteExecutable(c1, c2)
        assert size(root) == 3

    def test_depth(self):
        leaf = ConcreteExecutable()
        mid = ConcreteExecutable(leaf)
        root = ConcreteExecutable(mid)
        assert depth(root) == 2
