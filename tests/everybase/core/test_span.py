from __future__ import annotations

from abc import ABC

from nu import (
    Nu,
    Calculation,
    Span,
    Nu,
    depth,
    find,
    map_nodes,
    preorder,
    prune,
    size,
    unwrap,
)


# --- Test helpers ---


class ConcreteSpan(Span):
    """Span for testing."""

    def __init__(self, *children):
        super().__init__(*children)


class SimpleTerm(Nu):
    """Minimal term for testing."""

    def __init__(self, *children):
        super().__init__(*children)

    @property
    def is_self_pure(self):
        return True

    async def execute(self, ctx):
        return None


class SimpleCalculation(Calculation):
    """Minimal flow for testing."""

    def __init__(self, *children):
        super().__init__(*children)

    async def execute(self, ctx):
        for child in self.children:
            await child.execute(ctx)


# --- Tests ---


class TestSpanIsAbstract:
    def test_span_is_abc(self):
        assert issubclass(Span, ABC)

    def test_span_is_exec(self):
        assert issubclass(Span, Nu)


class TestSpanChildren:
    def test_span_with_term_children(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        s = ConcreteSpan(t1, t2)
        assert s.children == (t1, t2)

    def test_span_with_flow_children(self):
        f = SimpleCalculation()
        s = ConcreteSpan(f)
        assert s.children == (f,)

    def test_span_with_span_children(self):
        inner = ConcreteSpan()
        outer = ConcreteSpan(inner)
        assert outer.children == (inner,)

    def test_span_with_mixed_children(self):
        t = SimpleTerm()
        f = SimpleCalculation()
        inner_s = ConcreteSpan()
        s = ConcreteSpan(t, f, inner_s)
        assert s.child_count == 3
        assert isinstance(s.children[0], Nu)
        assert isinstance(s.children[1], Calculation)
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
        terms = find(s, lambda n: isinstance(n, Nu))
        # Span is now a Nu/Nu too, so all 3 nodes match
        assert len(terms) == 3

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
        flow_with_span = SimpleCalculation(span)

        # Without span -- terms directly in flow
        flow_without_span = SimpleCalculation(t1, t2)

        # Both have the same leaf terms
        with_leaves = find(flow_with_span, lambda n: n.is_leaf)
        without_leaves = find(flow_without_span, lambda n: n.is_leaf)
        assert len(with_leaves) == len(without_leaves)

    def test_prune_spans(self):
        """Removing spans via prune."""
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        span = ConcreteSpan(t1, t2)
        flow = SimpleCalculation(span)

        pruned = prune(flow, lambda n: isinstance(n, Span))
        # After pruning spans, the flow has no children
        assert pruned is not None
        assert pruned.child_count == 0

    def test_unwrap_single_child_span(self):
        """Unwrapping a single-child span splices child up."""
        t = SimpleTerm()
        span = ConcreteSpan(t)
        flow = SimpleCalculation(span)

        result = unwrap(flow, lambda n: isinstance(n, Span))
        assert result.child_count == 1
        assert isinstance(result.children[0], Nu)
