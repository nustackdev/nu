from __future__ import annotations

from everybase import ancestors, bfs, leaves, postorder, preorder

from .conftest import SimpleNode


class TestPreorder:
    def test_preorder_traversal(self, tree):
        labels = [n.label for n in preorder(tree)]
        assert labels == ["a", "b", "d", "e", "c", "f"]

    def test_preorder_single_node(self):
        leaf = SimpleNode("x")
        assert [n.label for n in preorder(leaf)] == ["x"]

    def test_preorder_is_lazy(self, tree):
        gen = preorder(tree)
        first = next(gen)
        assert first.label == "a"


class TestPostorder:
    def test_postorder_traversal(self, tree):
        labels = [n.label for n in postorder(tree)]
        assert labels == ["d", "e", "b", "f", "c", "a"]

    def test_postorder_single_node(self):
        leaf = SimpleNode("x")
        assert [n.label for n in postorder(leaf)] == ["x"]

    def test_postorder_root_is_last(self, tree):
        nodes = list(postorder(tree))
        assert nodes[-1].label == "a"


class TestBfs:
    def test_bfs_traversal(self, tree):
        labels = [n.label for n in bfs(tree)]
        assert labels == ["a", "b", "c", "d", "e", "f"]

    def test_bfs_single_node(self):
        leaf = SimpleNode("x")
        assert [n.label for n in bfs(leaf)] == ["x"]

    def test_bfs_root_is_first(self, tree):
        gen = bfs(tree)
        first = next(gen)
        assert first.label == "a"


class TestLeaves:
    def test_leaves_traversal(self, tree):
        labels = [n.label for n in leaves(tree)]
        assert labels == ["d", "e", "f"]

    def test_single_leaf_node(self):
        leaf = SimpleNode("x")
        result = list(leaves(leaf))
        assert len(result) == 1
        assert result[0] is leaf

    def test_leaves_skips_branches(self, tree):
        for node in leaves(tree):
            assert node.is_leaf


class TestAncestors:
    def test_ancestors_of_leaf(self, tree):
        # tree = a(b(d, e), c(f))
        d = tree.children[0].children[0]  # d
        path = ancestors(d, tree)
        assert path is not None
        labels = [n.label for n in path]
        assert labels == ["a", "b"]

    def test_ancestors_of_root(self, tree):
        path = ancestors(tree, tree)
        assert path == []

    def test_ancestors_of_direct_child(self, tree):
        b = tree.children[0]  # b
        path = ancestors(b, tree)
        assert path is not None
        labels = [n.label for n in path]
        assert labels == ["a"]

    def test_ancestors_not_found(self, tree):
        missing = SimpleNode("z")
        path = ancestors(missing, tree)
        assert path is None

    def test_ancestors_uses_identity(self, tree):
        # Create a node with same label but different identity
        fake_d = SimpleNode("d")
        path = ancestors(fake_d, tree)
        assert path is None

    def test_ancestors_single_node_root(self):
        leaf = SimpleNode("x")
        path = ancestors(leaf, leaf)
        assert path == []

    def test_ancestors_single_node_not_found(self):
        leaf = SimpleNode("x")
        other = SimpleNode("y")
        path = ancestors(other, leaf)
        assert path is None

    def test_ancestors_deep_node(self, tree):
        f = tree.children[1].children[0]  # f
        path = ancestors(f, tree)
        assert path is not None
        labels = [n.label for n in path]
        assert labels == ["a", "c"]
