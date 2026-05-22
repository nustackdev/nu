"""Tests for Program: structure access, attribute sweeps, and the compile entry."""

from __future__ import annotations

import pytest

from nu2.engine import Attribute, Program, Schema, Term, compile


class Leaf(Term):
    weight = Attribute.declared(2)


class Branch(Term):
    weight = Attribute.declared(1)


def make_schema():
    schema = Schema()
    # synthesized: total weight of the subtree.
    schema.register(
        Attribute.synthesized(
            "total_weight",
            base=lambda p, path: p.attr(path, "weight"),
            combine=lambda own, children: own + sum(children),
            reads=("weight",),
        )
    )
    # inherited: depth from the root.
    schema.register(
        Attribute.inherited(
            "depth",
            root=lambda p, path: 0,
            derive=lambda p, parent, slot, up: up + 1,
        )
    )
    # synthesized reading another computed attribute -- exercises `reads`.
    schema.register(
        Attribute.synthesized(
            "heavy",
            base=lambda p, path: p.attr(path, "total_weight") > 5,
            combine=lambda own, children: own,
            reads=("total_weight",),
        )
    )
    return schema.finalize()


# --- structure ---


def test_structure_access():
    leaf = Leaf()
    term = Branch(leaf, Branch(Leaf()))
    program = Program(term, make_schema())
    assert program.term(()) is term
    assert program.term((0,)) is leaf
    assert program.kind((0,)) is Leaf
    assert program.parent((1, 0)) == (1,)
    assert program.parent(()) is None
    root_children = program.children[program.id_of[()]]
    assert [program.path_of[c] for c in root_children] == [(0,), (1,)]
    assert list(program.walk()) == [(), (0,), (1,), (1, 0)]


def test_payload():
    leaf = Leaf()
    leaf.payload["tag"] = "x"
    program = Program(leaf, make_schema())
    assert program.payload(()) == {"tag": "x"}


# --- compile / attribute sweeps ---


def test_synthesized_folds_bottom_up():
    program = compile(Branch(Leaf(), Leaf()), make_schema())
    # Branch weight 1 + two leaves at 2 each.
    assert program.attr(program.root, "total_weight") == 5
    assert program.attr((0,), "total_weight") == 2


def test_inherited_threads_top_down():
    program = compile(Branch(Branch(Leaf())), make_schema())
    assert program.attr((), "depth") == 0
    assert program.attr((0,), "depth") == 1
    assert program.attr((0, 0), "depth") == 2


def test_declared_is_read_off_the_class():
    program = compile(Leaf(), make_schema())
    assert program.attr(program.root, "weight") == 2


def test_attribute_reading_another_attribute():
    program = compile(Branch(Leaf(), Leaf(), Leaf()), make_schema())
    # total_weight 7 > 5 -> heavy True at the root.
    assert program.attr(program.root, "heavy") is True
    assert program.attr((0,), "heavy") is False


def test_shared_term_decorates_per_path():
    shared = Leaf()
    program = compile(Branch(shared, Branch(shared)), make_schema())
    # one Term, two paths, independent inherited values.
    assert program.term((0,)) is program.term((1, 0))
    assert program.attr((0,), "depth") == 1
    assert program.attr((1, 0), "depth") == 2


def test_compile_populates_every_column():
    program = compile(Branch(Leaf()), make_schema())
    # 2 nodes x 3 computed attributes (total_weight, depth, heavy).
    assert {name: len(col) for name, col in program.attrs.items()} == {
        "total_weight": 2,
        "depth": 2,
        "heavy": 2,
    }


def test_missing_attribute_raises():
    program = compile(Leaf(), make_schema())
    with pytest.raises(KeyError, match="no attribute"):
        program.attr(program.root, "nonsense")
