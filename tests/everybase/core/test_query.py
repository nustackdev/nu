from __future__ import annotations

from nu import count, depth, find, find_first, size

from .conftest import SimpleNode


class TestFind:
    def test_find_all_matching(self, tree):
        result = find(tree, lambda n: n.is_leaf)
        labels = [n.label for n in result]
        assert labels == ["d", "e", "f"]

    def test_find_returns_empty_when_no_match(self, tree):
        result = find(tree, lambda n: False)
        assert result == []

    def test_find_returns_list(self, tree):
        result = find(tree, lambda n: True)
        assert isinstance(result, list)

    def test_find_preorder(self, tree):
        result = find(tree, lambda n: True)
        labels = [n.label for n in result]
        assert labels == ["a", "b", "d", "e", "c", "f"]

    def test_find_single_match(self, tree):
        result = find(tree, lambda n: isinstance(n, SimpleNode) and n.label == "c")
        assert len(result) == 1
        assert result[0].label == "c"


class TestFindFirst:
    def test_find_first_returns_first_match(self, tree):
        result = find_first(tree, lambda n: n.is_leaf)
        assert result is not None
        assert result.label == "d"

    def test_find_first_returns_none_when_no_match(self, tree):
        result = find_first(tree, lambda n: False)
        assert result is None

    def test_find_first_root(self, tree):
        result = find_first(tree, lambda n: isinstance(n, SimpleNode) and n.label == "a")
        assert result is not None
        assert result.label == "a"

    def test_find_first_preorder(self, tree):
        result = find_first(tree, lambda n: not n.is_leaf)
        assert result is not None
        # First non-leaf in preorder is root "a"
        assert result.label == "a"


class TestCount:
    def test_count_all_nodes(self, tree):
        assert count(tree) == 6

    def test_count_with_predicate(self, tree):
        assert count(tree, lambda n: n.is_leaf) == 3

    def test_count_no_match(self, tree):
        assert count(tree, lambda n: False) == 0

    def test_count_single_node(self):
        leaf = SimpleNode("x")
        assert count(leaf) == 1

    def test_count_predicate_none_means_all(self, tree):
        assert count(tree, None) == 6


class TestSize:
    def test_size_of_tree(self, tree):
        assert size(tree) == 6

    def test_size_of_leaf(self):
        assert size(SimpleNode("x")) == 1

    def test_size_of_small_tree(self):
        root = SimpleNode("r", SimpleNode("a"), SimpleNode("b"))
        assert size(root) == 3


class TestDepth:
    def test_depth_of_leaf(self):
        assert depth(SimpleNode("x")) == 0

    def test_depth_of_tree(self, tree):
        # a -> b -> d (depth 2)
        assert depth(tree) == 2

    def test_depth_of_shallow_tree(self):
        root = SimpleNode("r", SimpleNode("a"), SimpleNode("b"))
        assert depth(root) == 1

    def test_depth_of_deep_tree(self):
        node = SimpleNode("d")
        node = SimpleNode("c", node)
        node = SimpleNode("b", node)
        node = SimpleNode("a", node)
        assert depth(node) == 3

    def test_depth_of_unbalanced_tree(self):
        # Left side deeper than right
        deep = SimpleNode("deep", SimpleNode("deeper", SimpleNode("deepest")))
        shallow = SimpleNode("shallow")
        root = SimpleNode("root", deep, shallow)
        assert depth(root) == 3
