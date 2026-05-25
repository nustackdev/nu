"""Unit tests for ``nu2.engine.compilation.index``.

Covers ``build_index`` -- the preorder walk that assigns dense nids and
lays the structural columns. Each test constructs a Program (an empty
shell) and calls ``build_index`` directly so the pass is exercised in
isolation, without the attribute sweeps or the emit pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from _support.terms import Leaf, Node

from nu2.engine.compilation import Program
from nu2.engine.compilation.index import build_index


if TYPE_CHECKING:
    from nu2.engine.structure import Term


def _indexed(term: Term, schema) -> Program:
    """Construct a Program and run ``build_index`` against it."""
    program = Program(term, schema)
    build_index(program, term)
    return program


# --- a single node --------------------------------------------------------


def test_a_leaf_becomes_one_nid_with_empty_children(schema):
    p = _indexed(Leaf(), schema)
    assert len(p.terms) == 1
    assert p.children == [()]
    assert p.parent_id == [-1]
    assert p.path_of == [()]
    assert p.id_of == {(): 0}


# --- preorder layout ------------------------------------------------------


def test_preorder_assigns_root_first_then_children_in_slot_order(schema):
    p = _indexed(Node(Leaf(), Leaf()), schema)
    assert p.path_of == [(), (0,), (1,)]
    assert p.parent_id == [-1, 0, 0]
    assert p.children == [(1, 2), (), ()]


def test_slot_order_preserves_child_identity(schema):
    a, b, c = Leaf(), Leaf(), Leaf()
    p = _indexed(Node(a, b, c), schema)
    assert p.terms[1] is a
    assert p.terms[2] is b
    assert p.terms[3] is c


def test_a_deep_path_extends_its_parents_path_by_one_slot(schema):
    p = _indexed(Node(Node(Leaf()), Leaf()), schema)
    assert p.path_of == [(), (0,), (0, 0), (1,)]


# --- column invariants ----------------------------------------------------


def test_id_of_is_the_inverse_of_path_of(schema):
    p = _indexed(Node(Node(Leaf()), Leaf(), Leaf()), schema)
    for nid, path in enumerate(p.path_of):
        assert p.id_of[path] == nid


def test_children_entries_are_tuples_not_lists(schema):
    p = _indexed(Node(Leaf(), Leaf()), schema)
    assert all(isinstance(c, tuple) for c in p.children)


def test_parent_id_is_minus_one_at_root_and_points_at_an_ancestor_below_it(schema):
    p = _indexed(Node(Node(Leaf()), Leaf()), schema)
    assert p.parent_id[0] == -1
    for nid in range(1, len(p.terms)):
        # Parent nid must be strictly smaller (preorder) and a real index.
        assert 0 <= p.parent_id[nid] < nid


# --- DAG sharing ----------------------------------------------------------


def test_a_shared_term_becomes_two_distinct_nids_with_one_term_object(schema):
    # The canonical Add(x, x) shape: one Term, two nids.
    x = Leaf()
    p = _indexed(Node(x, x), schema)
    assert p.terms[1] is x
    assert p.terms[2] is x
    assert p.terms[1] is p.terms[2]
    assert p.path_of[1] != p.path_of[2]
    assert p.id_of[(0,)] != p.id_of[(1,)]


def test_a_shared_interior_subtree_indexes_independently_per_occurrence(schema):
    sub = Node(Leaf(), Leaf())
    p = _indexed(Node(sub, sub), schema)
    # The two occurrences of ``sub`` get distinct nids
    assert p.id_of[(0,)] != p.id_of[(1,)]
    # And each of sub's own children appears under both occurrences
    assert p.id_of[(0, 0)] != p.id_of[(1, 0)]
    assert p.id_of[(0, 1)] != p.id_of[(1, 1)]
