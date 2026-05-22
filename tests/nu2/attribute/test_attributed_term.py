"""Tests for AttributedTerm, Attr, Rows, and attribute."""

from __future__ import annotations

import pytest

from nu2.engine import Attribute, AttributedTerm, Rows, Schema, Term, attribute


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
            combine=lambda own, kids: own + sum(kids),
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
            combine=lambda own, kids: own,
            reads=("total_weight",),
        )
    )
    return schema.finalize()


# --- structure ---


def test_structure_access():
    leaf = Leaf()
    desc = Branch(leaf, Branch(Leaf()))
    program = AttributedTerm(desc, make_schema())
    assert program.term(()) is desc
    assert program.term((0,)) is leaf
    assert program.kind((0,)) is Leaf
    assert program.parent((1, 0)) == (1,)
    assert program.parent(()) is None
    assert program.children(()) == [(0,), (1,)]
    assert list(program.walk()) == [(), (0,), (1,), (1, 0)]


def test_payload():
    leaf = Leaf()
    leaf.payload["tag"] = "x"
    program = AttributedTerm(leaf, make_schema())
    assert program.payload(()) == {"tag": "x"}


# --- evaluation ---


def test_synthesized_folds_bottom_up():
    program = attribute(Branch(Leaf(), Leaf()), make_schema())
    # Branch weight 1 + two leaves at 2 each.
    assert program.attr(program.root, "total_weight") == 5
    assert program.attr((0,), "total_weight") == 2


def test_inherited_threads_top_down():
    program = attribute(Branch(Branch(Leaf())), make_schema())
    assert program.attr((), "depth") == 0
    assert program.attr((0,), "depth") == 1
    assert program.attr((0, 0), "depth") == 2


def test_declared_is_read_off_the_class():
    program = attribute(Leaf(), make_schema())
    assert program.attr(program.root, "weight") == 2


def test_attribute_reading_another_attribute():
    program = attribute(Branch(Leaf(), Leaf(), Leaf()), make_schema())
    # total_weight 7 > 5 -> heavy True at the root.
    assert program.attr(program.root, "heavy") is True
    assert program.attr((0,), "heavy") is False


def test_shared_term_decorates_per_path():
    shared = Leaf()
    program = attribute(Branch(shared, Branch(shared)), make_schema())
    # one Term, two paths, independent inherited values.
    assert program.term((0,)) is program.term((1, 0))
    assert program.attr((0,), "depth") == 1
    assert program.attr((1, 0), "depth") == 2


def test_attribute_populates_attr_fully():
    program = attribute(Branch(Leaf()), make_schema())
    # 2 nodes x 2 computed attributes (total_weight, depth, heavy = 3).
    assert len(program.attr.rows()) == 2 * 3


def test_missing_attribute_raises():
    program = attribute(Leaf(), make_schema())
    with pytest.raises(KeyError, match="no attribute"):
        program.attr(program.root, "nonsense")


# --- queries ---


def test_rows_filter_by_name():
    program = attribute(Branch(Leaf(), Leaf()), make_schema())
    rows = program.attr.rows(name="depth")
    assert len(rows) == 3
    assert all(r["name"] == "depth" for r in rows)


def test_rows_filter_by_subtree():
    program = attribute(Branch(Branch(Leaf()), Leaf()), make_schema())
    rows = program.attr.rows(name="depth", under=(0,))
    assert sorted(rows.paths()) == [(0,), (0, 0)]


def test_rows_where_and_values():
    program = attribute(Branch(Leaf(), Leaf(), Leaf()), make_schema())
    heavy = program.attr.rows(name="heavy").where(lambda r: r["value"] is True)
    assert heavy.paths() == [()]
    assert heavy.values() == [True]
    assert isinstance(heavy, Rows)
