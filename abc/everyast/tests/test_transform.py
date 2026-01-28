from __future__ import annotations

from everyast import (
    apply,
    compose,
    graft,
    map_children,
    map_nodes,
    prune,
    replace,
    unwrap,
    wrap,
)

from .conftest import SimpleNode


class TestCompose:
    def test_compose_left_to_right(self):
        def add_x(node):
            return SimpleNode(node.label + "_x", *node.children)

        def add_y(node):
            return SimpleNode(node.label + "_y", *node.children)

        composed = compose(add_x, add_y)
        result = composed(SimpleNode("a"))
        assert result.label == "a_x_y"

    def test_compose_single(self):
        def add_x(node):
            return SimpleNode(node.label + "_x", *node.children)

        composed = compose(add_x)
        result = composed(SimpleNode("a"))
        assert result.label == "a_x"

    def test_compose_empty(self):
        composed = compose()
        node = SimpleNode("a")
        result = composed(node)
        assert result is node


class TestApply:
    def test_apply_in_order(self):
        def add_x(node):
            return SimpleNode(node.label + "_x", *node.children)

        def add_y(node):
            return SimpleNode(node.label + "_y", *node.children)

        result = apply(SimpleNode("a"), add_x, add_y)
        assert result.label == "a_x_y"

    def test_apply_no_transforms(self):
        node = SimpleNode("a")
        result = apply(node)
        assert result is node


class TestMapChildren:
    def test_map_children_shallow(self, tree):
        def upper(node):
            return SimpleNode(node.label.upper(), *node.children)

        result = map_children(tree, upper)
        # Only direct children (b, c) are transformed, not deeper
        assert result.label == "a"
        assert result.children[0].label == "B"
        assert result.children[1].label == "C"
        # Deeper nodes unchanged
        assert result.children[0].children[0].label == "d"
        assert result.children[0].children[1].label == "e"

    def test_map_children_leaf_returns_self(self):
        leaf = SimpleNode("x")
        result = map_children(leaf, lambda n: SimpleNode("should_not_appear"))
        assert result is leaf

    def test_map_children_preserves_parent_label(self, tree):
        result = map_children(tree, lambda c: SimpleNode("z"))
        assert result.label == "a"


class TestMapNodes:
    def test_map_nodes_bottom_up(self, tree):
        visited = []

        def track(node):
            visited.append(node.label)
            return node

        map_nodes(tree, track, order="bottom_up")
        # Children processed before parents
        assert visited == ["d", "e", "b", "f", "c", "a"]

    def test_map_nodes_top_down(self, tree):
        visited = []

        def track(node):
            visited.append(node.label)
            return node

        map_nodes(tree, track, order="top_down")
        # Parents processed before children
        assert visited == ["a", "b", "d", "e", "c", "f"]

    def test_map_nodes_transforms_all(self, tree):
        def upper(node):
            return SimpleNode(node.label.upper(), *node.children)

        result = map_nodes(tree, upper, order="bottom_up")
        assert result.label == "A"
        assert result.children[0].label == "B"
        assert result.children[0].children[0].label == "D"

    def test_map_nodes_default_is_bottom_up(self, tree):
        visited = []

        def track(node):
            visited.append(node.label)
            return node

        map_nodes(tree, track)
        assert visited == ["d", "e", "b", "f", "c", "a"]


class TestReplace:
    def test_replace_matching_nodes(self, tree):
        def is_leaf_d(node):
            return isinstance(node, SimpleNode) and node.label == "d"

        result = replace(tree, is_leaf_d, lambda n: SimpleNode("D_REPLACED"))
        assert result.children[0].children[0].label == "D_REPLACED"

    def test_replace_no_match_preserves_structure(self, tree):
        result = replace(tree, lambda n: False, lambda n: SimpleNode("X"))
        assert result == tree

    def test_replace_root(self):
        root = SimpleNode("root")
        result = replace(root, lambda n: n.label == "root", lambda n: SimpleNode("new_root"))
        assert result.label == "new_root"


class TestWrap:
    def test_wrap_matching_nodes(self):
        leaf = SimpleNode("x")
        root = SimpleNode("root", leaf)

        result = wrap(
            root,
            lambda n: isinstance(n, SimpleNode) and n.label == "x",
            lambda n: SimpleNode("wrapper", n),
        )

        # The leaf "x" should be wrapped
        wrapped_child = result.children[0]
        assert wrapped_child.label == "wrapper"
        assert wrapped_child.children[0].label == "x"

    def test_wrap_no_match(self):
        root = SimpleNode("root", SimpleNode("a"))
        result = wrap(root, lambda n: False, lambda n: SimpleNode("wrapper", n))
        assert result == root


class TestUnwrap:
    def test_unwrap_single_child_wrappers(self):
        inner = SimpleNode("inner")
        wrapper = SimpleNode("wrapper", inner)
        root = SimpleNode("root", wrapper)

        result = unwrap(
            root,
            lambda n: isinstance(n, SimpleNode) and n.label == "wrapper",
        )

        # The wrapper should be removed, inner spliced up
        assert result.children[0].label == "inner"
        assert result.children[0] is inner

    def test_unwrap_multi_child_not_unwrapped(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        wrapper = SimpleNode("wrapper", a, b)
        root = SimpleNode("root", wrapper)

        result = unwrap(
            root,
            lambda n: isinstance(n, SimpleNode) and n.label == "wrapper",
        )

        # Multi-child wrapper should NOT be unwrapped
        assert result.children[0].label == "wrapper"

    def test_unwrap_no_match(self):
        root = SimpleNode("root", SimpleNode("a"))
        result = unwrap(root, lambda n: False)
        assert result == root

    def test_unwrap_nested(self):
        inner = SimpleNode("inner")
        w1 = SimpleNode("w", inner)
        w2 = SimpleNode("w", w1)
        root = SimpleNode("root", w2)

        result = unwrap(
            root,
            lambda n: isinstance(n, SimpleNode) and n.label == "w",
        )

        assert result.children[0].label == "inner"


class TestGraft:
    def test_graft_replaces_by_identity(self, tree):
        d = tree.children[0].children[0]  # d node
        new_subtree = SimpleNode("D_NEW", SimpleNode("d1"), SimpleNode("d2"))

        result = graft(tree, d, new_subtree)
        # d should be replaced
        replaced = result.children[0].children[0]
        assert replaced.label == "D_NEW"
        assert replaced.child_count == 2

    def test_graft_does_not_match_equal_nodes(self, tree):
        fake_d = SimpleNode("d")  # same label, different identity
        new_subtree = SimpleNode("REPLACED")

        result = graft(tree, fake_d, new_subtree)
        # Nothing should change because identity does not match
        assert result.children[0].children[0].label == "d"

    def test_graft_root(self):
        root = SimpleNode("root")
        new = SimpleNode("new_root")
        result = graft(root, root, new)
        assert result.label == "new_root"


class TestPrune:
    def test_prune_removes_matching_subtrees(self, tree):
        def is_b(node):
            return isinstance(node, SimpleNode) and node.label == "b"

        result = prune(tree, is_b)
        assert result is not None
        # Only c remains as child of a
        assert len(result.children) == 1
        assert result.children[0].label == "c"

    def test_prune_returns_none_when_root_matches(self, tree):
        result = prune(tree, lambda n: isinstance(n, SimpleNode) and n.label == "a")
        assert result is None

    def test_prune_no_match_preserves_identity(self, tree):
        result = prune(tree, lambda n: False)
        assert result is tree

    def test_prune_preserves_unchanged_subtrees(self, tree):
        def is_d(node):
            return isinstance(node, SimpleNode) and node.label == "d"

        result = prune(tree, is_d)
        assert result is not None
        # c subtree should be unchanged by identity
        assert result.children[1] is tree.children[1]

    def test_prune_leaf(self):
        leaf = SimpleNode("x")
        result = prune(leaf, lambda n: False)
        assert result is leaf

    def test_prune_removes_multiple(self, tree):
        # Remove all leaves
        result = prune(tree, lambda n: n.is_leaf)
        assert result is not None
        # b and c lost their children
        assert result.children[0].label == "b"
        assert result.children[0].child_count == 0
        assert result.children[1].label == "c"
        assert result.children[1].child_count == 0


class TestIdentityPreservation:
    def test_map_children_unchanged_returns_new_parent_but_same_children(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        parent = SimpleNode("p", a, b)

        result = map_children(parent, lambda c: c)
        # Children are the same objects (identity fn)
        assert result.children[0] is a
        assert result.children[1] is b

    def test_prune_no_match_returns_same_root(self):
        a = SimpleNode("a")
        b = SimpleNode("b")
        root = SimpleNode("root", a, b)

        result = prune(root, lambda n: False)
        assert result is root

    def test_prune_partial_preserves_untouched_subtree(self):
        x = SimpleNode("x")
        y = SimpleNode("y")
        left = SimpleNode("left", x)
        right = SimpleNode("right", y)
        root = SimpleNode("root", left, right)

        result = prune(root, lambda n: isinstance(n, SimpleNode) and n.label == "x")
        assert result is not None
        # right subtree is untouched
        assert result.children[1] is right
