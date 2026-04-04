from __future__ import annotations

from abc import ABC

from nu import Nu, Calculation, Span, Nu, depth, find, map_nodes, preorder, size


# --- Test helpers ---


class ConcreteCalc(Calculation):
    """Calculation for testing."""

    def __init__(self, *children):
        super().__init__(*children)

    async def execute(self, ctx):
        for child in self.children:
            await child.execute(ctx)


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


class TestCalculationIsAbstract:
    def test_flow_is_abc(self):
        assert issubclass(Calculation, ABC)

    def test_flow_is_exec(self):
        assert issubclass(Calculation, Nu)


class TestCalculationChildren:
    def test_flow_with_term_children(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteCalc(t1, t2)
        assert f.children == (t1, t2)

    def test_flow_with_flow_children(self):
        inner = ConcreteCalc()
        outer = ConcreteCalc(inner)
        assert outer.children == (inner,)

    def test_flow_with_span_children(self):
        s = SimpleSpan()
        f = ConcreteCalc(s)
        assert f.children == (s,)

    def test_flow_with_mixed_children(self):
        t = SimpleTerm()
        inner_f = ConcreteCalc()
        s = SimpleSpan()
        f = ConcreteCalc(t, inner_f, s)
        assert f.child_count == 3
        assert isinstance(f.children[0], Nu)
        assert isinstance(f.children[1], Calculation)
        assert isinstance(f.children[2], Span)

    def test_empty_flow_is_leaf(self):
        f = ConcreteCalc()
        assert f.is_leaf is True


class TestCalculationWithAstOperations:
    def test_preorder(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteCalc(t1, t2)
        nodes = list(preorder(f))
        assert len(nodes) == 3

    def test_map_nodes(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteCalc(t1, t2)

        def identity(n):
            return n

        result = map_nodes(f, identity)
        assert result.child_count == 2

    def test_find(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteCalc(t1, t2)
        terms = find(f, lambda n: isinstance(n, Nu))
        # Calculation is now a Nu/Nu too, so all 3 nodes match
        assert len(terms) == 3

    def test_size(self):
        t1 = SimpleTerm()
        t2 = SimpleTerm()
        f = ConcreteCalc(t1, t2)
        assert size(f) == 3

    def test_depth_nested(self):
        t = SimpleTerm()
        inner = ConcreteCalc(t)
        outer = ConcreteCalc(inner)
        assert depth(outer) == 2
