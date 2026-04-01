from __future__ import annotations

from abc import ABC

from nu import Nu, Flow, Span, Nu, depth, find, map_nodes, preorder, size


# --- Test helpers ---


class ConcreteFlow(Flow):
    """Flow for testing."""

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


class SimpleSpan(Span):
    """Minimal span for testing."""

    def __init__(self, *children):
        super().__init__(*children)


# --- Tests ---


class TestFlowIsAbstract:
    def test_flow_is_abc(self):
        assert issubclass(Flow, ABC)

    def test_flow_is_exec(self):
        assert issubclass(Flow, Nu)


class TestFlowChildren:
    def test_flow_with_term_children(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteFlow(t1, t2)
        assert f.children == (t1, t2)

    def test_flow_with_flow_children(self):
        inner = ConcreteFlow()
        outer = ConcreteFlow(inner)
        assert outer.children == (inner,)

    def test_flow_with_span_children(self):
        s = SimpleSpan()
        f = ConcreteFlow(s)
        assert f.children == (s,)

    def test_flow_with_mixed_children(self):
        t = SimpleTerm()
        inner_f = ConcreteFlow()
        s = SimpleSpan()
        f = ConcreteFlow(t, inner_f, s)
        assert f.child_count == 3
        assert isinstance(f.children[0], Nu)
        assert isinstance(f.children[1], Flow)
        assert isinstance(f.children[2], Span)

    def test_empty_flow_is_leaf(self):
        f = ConcreteFlow()
        assert f.is_leaf is True


class TestFlowWithAstOperations:
    def test_preorder(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteFlow(t1, t2)
        nodes = list(preorder(f))
        assert len(nodes) == 3

    def test_map_nodes(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteFlow(t1, t2)

        def identity(n):
            return n

        result = map_nodes(f, identity)
        assert result.child_count == 2

    def test_find(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteFlow(t1, t2)
        terms = find(f, lambda n: isinstance(n, Nu))
        # Flow is now a Nu/Nu too, so all 3 nodes match
        assert len(terms) == 3

    def test_size(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteFlow(t1, t2)
        assert size(f) == 3

    def test_depth_nested(self):
        t = SimpleTerm()
        inner = ConcreteFlow(t)
        outer = ConcreteFlow(inner)
        assert depth(outer) == 2
