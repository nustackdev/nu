from __future__ import annotations

from everyast.defs import Exec, Flow, Span, Term

from everyast import (
    bfs,
    depth,
    find,
    map_nodes,
    postorder,
    preorder,
    prune,
    size,
)


# --- Test helpers ---


class Add(Term):
    """Compound pure term."""

    __slots__ = ("_children",)

    def __init__(self, *children):
        self._children = children

    @property
    def is_pure(self):
        return True

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        return Add(*children)


class Lit(Term):
    """Leaf pure term."""

    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    @property
    def is_pure(self):
        return True

    def with_children(self, *children):
        return self


class Seq(Flow):
    """Sequential flow."""

    __slots__ = ("_children",)

    def __init__(self, *children):
        self._children = children

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        return Seq(*children)


class Par(Flow):
    """Parallel flow."""

    __slots__ = ("_children",)

    def __init__(self, *children):
        self._children = children

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        return Par(*children)


class Boundary(Span):
    """Cohesion boundary."""

    __slots__ = ("_children",)

    def __init__(self, *children):
        self._children = children

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        return Boundary(*children)


# --- Integration Tests ---


class TestTopologyTree:
    """Build a topology tree mixing Terms, Flows, Spans."""

    def _make_tree(self):
        """Build:

        Seq
        +-- Boundary
        |   +-- Add
        |   |   +-- Lit(1)
        |   |   +-- Lit(2)
        |   +-- Lit(3)
        +-- Par
            +-- Lit(4)
            +-- Lit(5)
        """
        lit1 = Lit(1)
        lit2 = Lit(2)
        lit3 = Lit(3)
        lit4 = Lit(4)
        lit5 = Lit(5)
        add = Add(lit1, lit2)
        boundary = Boundary(add, lit3)
        par = Par(lit4, lit5)
        seq = Seq(boundary, par)
        return seq

    def test_preorder(self):
        tree = self._make_tree()
        nodes = list(preorder(tree))
        assert len(nodes) == 9
        assert isinstance(nodes[0], Seq)
        assert isinstance(nodes[1], Boundary)

    def test_postorder(self):
        tree = self._make_tree()
        nodes = list(postorder(tree))
        assert len(nodes) == 9
        # Leaves come first in postorder
        assert isinstance(nodes[-1], Seq)

    def test_bfs(self):
        tree = self._make_tree()
        nodes = list(bfs(tree))
        assert len(nodes) == 9
        # Level 0: Seq
        assert isinstance(nodes[0], Seq)
        # Level 1: Boundary, Par
        assert isinstance(nodes[1], Boundary)
        assert isinstance(nodes[2], Par)

    def test_size(self):
        tree = self._make_tree()
        assert size(tree) == 9

    def test_depth(self):
        tree = self._make_tree()
        # Seq -> Boundary -> Add -> Lit = depth 3
        assert depth(tree) == 3

    def test_find_terms(self):
        tree = self._make_tree()
        terms = find(tree, lambda n: isinstance(n, Term))
        # Add + 5 Lits = 6 terms
        assert len(terms) == 6

    def test_find_flows(self):
        tree = self._make_tree()
        flows = find(tree, lambda n: isinstance(n, Flow))
        # Seq + Par = 2 flows
        assert len(flows) == 2

    def test_find_spans(self):
        tree = self._make_tree()
        spans = find(tree, lambda n: isinstance(n, Span))
        # 1 Boundary
        assert len(spans) == 1

    def test_find_execs(self):
        tree = self._make_tree()
        execs = find(tree, lambda n: isinstance(n, Exec))
        # All nodes are Execs
        assert len(execs) == 9


class TestTransformTopology:
    """Transform topology trees."""

    def test_map_nodes_identity(self):
        lit = Lit(1)
        seq = Seq(lit)

        def identity(n):
            return n

        result = map_nodes(seq, identity)
        assert size(result) == 2

    def test_map_nodes_replace_leaf(self):
        lit1 = Lit(1)
        lit2 = Lit(2)
        add = Add(lit1, lit2)

        def replace_with_zero(n):
            if isinstance(n, Lit):
                return Lit(0)
            return n

        result = map_nodes(add, replace_with_zero)
        assert isinstance(result, Add)
        assert result.child_count == 2


class TestSpanTransparency:
    """Removing spans doesn't change computation (transparency test)."""

    def test_prune_spans(self):
        lit1 = Lit(1)
        lit2 = Lit(2)
        boundary = Boundary(lit1, lit2)
        seq = Seq(boundary, Lit(3))

        # Prune all spans
        pruned = prune(seq, lambda n: isinstance(n, Span))

        # The boundary (with its children) is gone, only Lit(3) remains
        assert pruned is not None
        assert isinstance(pruned, Seq)
        assert pruned.child_count == 1

    def test_find_terms_ignoring_spans(self):
        """Find all terms whether or not wrapped in spans."""
        lit1 = Lit(1)
        lit2 = Lit(2)
        lit3 = Lit(3)

        # With span wrapping
        boundary = Boundary(lit1, lit2)
        tree = Seq(boundary, lit3)

        terms = find(tree, lambda n: isinstance(n, Term))
        assert len(terms) == 3

    def test_structure_equivalence(self):
        """Tree with and without spans has same leaf count."""
        lit1 = Lit(1)
        lit2 = Lit(2)
        lit3 = Lit(3)

        with_span = Seq(Boundary(lit1, lit2), lit3)
        without_span = Seq(lit1, lit2, lit3)

        with_leaves = find(with_span, lambda n: n.is_leaf)
        without_leaves = find(without_span, lambda n: n.is_leaf)
        assert len(with_leaves) == len(without_leaves)
