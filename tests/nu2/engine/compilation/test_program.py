"""Unit tests for ``nu2.engine.compilation.program``.

Covers :class:`Program` -- construction (which runs ``build_index``
immediately), the path-keyed read API (``walk``, ``attr``), the
:class:`UnknownAttributeError` shape, and the documented column store
defaults.
"""

from __future__ import annotations

import pytest
from _support.terms import HeavyNode, Leaf, Node

from nu2.engine.compilation import Program, UnknownAttributeError, compile
from nu2.engine.structure import Synthesized


# --- construction ----------------------------------------------------------


def test_construction_initializes_every_column_empty(schema):
    # ``Program(term, schema)`` is a dumb constructor: no phase runs. The
    # ``compile`` driver fills the columns by calling ``build_index``,
    # ``sweep_attributes``, and ``emit_thunks`` in order.
    p = Program(Leaf(), schema)
    assert p.terms == []
    assert p.children == []
    assert p.parent_id == []
    assert p.path_of == []
    assert p.id_of == {}
    assert p.attrs == {}
    assert p.thunks == []
    assert p.athunks == []


def test_root_is_the_empty_path():
    assert Program.root == ()


def test_repr_includes_the_root_term(schema):
    leaf = Leaf()
    p = Program(leaf, schema)
    assert repr(p) == f"Program({leaf!r})"


# --- walk ------------------------------------------------------------------


def test_walk_root_yields_every_path_in_preorder(schema):
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    assert list(p.walk()) == [(), (0,), (1,)]


def test_walk_under_a_subtree_yields_only_that_subtree(schema):
    schema.finalize()
    p = compile(Node(Node(Leaf(), Leaf()), Leaf()), schema)
    assert list(p.walk((0,))) == [(0,), (0, 0), (0, 1)]


def test_walk_a_leaf_yields_just_itself(schema):
    schema.finalize()
    p = compile(Node(Leaf()), schema)
    assert list(p.walk((0,))) == [(0,)]


# --- attr ------------------------------------------------------------------


def test_attr_reads_a_computed_column(schema):
    schema.register(
        Synthesized(
            name="size",
            base=lambda program, path: 1,
            combine=lambda own, children: own + sum(children),
        ),
    )
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    assert p.attr((), "size") == 3
    assert p.attr((0,), "size") == 1


def test_attr_resolves_a_class_level_declared_attribute_via_the_schema(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    # ``Leaf.sort`` is a class-declared attribute, never stored in attrs.
    assert p.attr((), "sort") == "Leaf"


def test_attr_finds_a_subclass_override_via_the_schema(schema):
    schema.finalize()
    p = compile(HeavyNode(), schema)
    assert p.attr((), "weight") == 9


def test_attr_raises_unknown_attribute_for_a_missing_name(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    with pytest.raises(UnknownAttributeError, match="Leaf has no attribute 'missing'"):
        p.attr((), "missing")


def test_unknown_attribute_error_is_a_keyerror_subclass(schema):
    schema.finalize()
    p = compile(Leaf(), schema)
    with pytest.raises(KeyError):
        p.attr((), "missing")
