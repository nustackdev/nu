from __future__ import annotations

import pytest

from everybase import Executable, Term, find, map_nodes, preorder, size


class PureTerm(Term):
    """Pure term for testing."""

    def __init__(self, *children):
        super().__init__(*children)

    @property
    def is_self_pure(self):
        return True

    async def execute(self, ctx):
        return None


class ImpureTerm(Term):
    """Impure term for testing."""

    def __init__(self, *children):
        super().__init__(*children)

    @property
    def is_self_pure(self):
        return False

    async def execute(self, ctx):
        return None


class CompoundTerm(Term):
    """Term with children and extra state for testing."""

    def __init__(self, label, *children, pure=True):
        super().__init__(*children)
        self._label = label
        self._pure = pure

    @property
    def is_self_pure(self):
        return self._pure

    async def execute(self, ctx):
        return None

    def with_children(self, *children):
        """Preserve label and purity when reconstructing."""
        if children == self._children:
            return self
        return CompoundTerm(self._label, *children, pure=self._pure)


class TestTermIsAbstract:
    def test_cannot_instantiate_term(self):
        with pytest.raises(TypeError):
            Term()

    def test_term_is_exec(self):
        assert issubclass(Term, Executable)


class TestTermPurity:
    def test_pure_term(self):
        t = PureTerm()
        assert t.is_self_pure is True

    def test_impure_term(self):
        t = ImpureTerm()
        assert t.is_self_pure is False

    def test_compound_term_pure(self):
        t = CompoundTerm("add", pure=True)
        assert t.is_self_pure is True

    def test_compound_term_impure(self):
        t = CompoundTerm("write", pure=False)
        assert t.is_self_pure is False


class TestTermChildren:
    def test_default_children_empty(self):
        t = PureTerm()
        assert t.children == ()

    def test_leaf_by_default(self):
        t = PureTerm()
        assert t.is_leaf is True

    def test_compound_term_children(self):
        a = CompoundTerm("a")
        b = CompoundTerm("b")
        parent = CompoundTerm("add", a, b)
        assert parent.children == (a, b)
        assert parent.child_count == 2

    def test_compound_term_not_leaf(self):
        a = CompoundTerm("a")
        parent = CompoundTerm("add", a)
        assert parent.is_leaf is False


class TestTermWithAstOperations:
    def test_preorder(self):
        a = CompoundTerm("a")
        b = CompoundTerm("b")
        root = CompoundTerm("add", a, b)
        nodes = list(preorder(root))
        assert len(nodes) == 3
        assert nodes[0] is root

    def test_map_nodes(self):
        a = CompoundTerm("a")
        b = CompoundTerm("b")
        root = CompoundTerm("add", a, b)

        def identity(n):
            return n

        result = map_nodes(root, identity)
        assert result.child_count == 2

    def test_find_terms(self):
        a = CompoundTerm("a")
        b = CompoundTerm("b")
        root = CompoundTerm("add", a, b)
        found = find(root, lambda n: isinstance(n, Term))
        assert len(found) == 3

    def test_size(self):
        a = CompoundTerm("a")
        b = CompoundTerm("b")
        root = CompoundTerm("add", a, b)
        assert size(root) == 3

    def test_with_children_preserves_purity(self):
        a = CompoundTerm("a")
        b = CompoundTerm("b")
        root = CompoundTerm("add", a, b, pure=False)
        new_root = root.with_children(a)
        assert new_root.is_self_pure is False
