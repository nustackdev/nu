from __future__ import annotations

from abc import ABC

from everyast.defs import Exec, Flow, Span, Term

from everyast import depth, find, map_nodes, preorder, prune, size, unwrap


# --- Test helpers ---


class ConcreteSpan(Span):
    """Span for testing."""

    __slots__ = ("_children",)

    def __init__(self, *children):
        self._children = children

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        return ConcreteSpan(*children)


class SimpleTerm(Term):
    """Minimal term for testing."""

    __slots__ = ()

    @property
    def is_pure(self):
        return True

    def with_children(self, *children):
        return SimpleTerm()


class SimpleFlow(Flow):
    """Minimal flow for testing."""

    __slots__ = ("_children",)

    def __init__(self, *children):
        self._children = children

    @property
    def children(self):
        return self._children

    def with_children(self, *children):
        return SimpleFlow(*children)


# --- Tests ---


class TestSpanIsAbstract:
    def test_span_is_abc(self):
        assert issubclass(Span, ABC)

    def test_span_is_exec(self):
        assert issubclass(Span, Exec)


class TestSpanChildren:
    def test_span_with_term_children(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        s = ConcreteSpan(t1, t2)
        assert s.children == (t1, t2)

    def test_span_with_flow_children(self):
        f = SimpleFlow()
        s = ConcreteSpan(f)
        assert s.children == (f,)

    def test_span_with_span_children(self):
        inner = ConcreteSpan()
        outer = ConcreteSpan(inner)
        assert outer.children == (inner,)

    def test_span_with_mixed_children(self):
        t = SimpleTerm()
        f = SimpleFlow()
        inner_s = ConcreteSpan()
        s = ConcreteSpan(t, f, inner_s)
        assert s.child_count == 3
        assert isinstance(s.children[0], Term)
        assert isinstance(s.children[1], Flow)
        assert isinstance(s.children[2], Span)

    def test_empty_span_is_leaf(self):
        s = ConcreteSpan()
        assert s.is_leaf is True


class TestSpanWithAstOperations:
    def test_preorder(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        s = ConcreteSpan(t1, t2)
        nodes = list(preorder(s))
        assert len(nodes) == 3

    def test_map_nodes(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        s = ConcreteSpan(t1, t2)

        def identity(n):
            return n

        result = map_nodes(s, identity)
        assert result.child_count == 2

    def test_find(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        s = ConcreteSpan(t1, t2)
        terms = find(s, lambda n: isinstance(n, Term))
        assert len(terms) == 2

    def test_size(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        s = ConcreteSpan(t1, t2)
        assert size(s) == 3

    def test_depth_nested(self):
        t = SimpleTerm()
        inner = ConcreteSpan(t)
        outer = ConcreteSpan(inner)
        assert depth(outer) == 2


class TestSpanTransparency:
    def test_tree_with_and_without_span(self):
        """Span transparency: structure is equivalent with and without spans."""
        t1 = SimpleTerm()
        t2 = SimpleTerm()

        # With span
        span = ConcreteSpan(t1, t2)
        flow_with_span = SimpleFlow(span)

        # Without span -- terms directly in flow
        flow_without_span = SimpleFlow(t1, t2)

        # Both have the same leaf terms
        with_leaves = find(flow_with_span, lambda n: n.is_leaf)
        without_leaves = find(flow_without_span, lambda n: n.is_leaf)
        assert len(with_leaves) == len(without_leaves)

    def test_prune_spans(self):
        """Removing spans via prune."""
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        span = ConcreteSpan(t1, t2)
        flow = SimpleFlow(span)

        pruned = prune(flow, lambda n: isinstance(n, Span))
        # After pruning spans, the flow has no children
        assert pruned is not None
        assert pruned.child_count == 0

    def test_unwrap_single_child_span(self):
        """Unwrapping a single-child span splices child up."""
        t = SimpleTerm()
        span = ConcreteSpan(t)
        flow = SimpleFlow(span)

        result = unwrap(flow, lambda n: isinstance(n, Span))
        assert result.child_count == 1
        assert isinstance(result.children[0], Term)
