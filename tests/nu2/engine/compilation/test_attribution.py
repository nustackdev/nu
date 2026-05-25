"""Unit tests for ``nu2.engine.compilation.attribution``.

Covers ``sweep_attributes`` and its two direction-specific helpers:
``_synthesize`` (leaves-up) and ``_inherit`` (root-down). Declared
attributes are not stored. Cross-attribute reads are scheduled by the
schema's topological order.
"""

from __future__ import annotations

import pytest
from _support.terms import Leaf, Node

from nu2.engine.compilation import Program, compile
from nu2.engine.compilation.attribution import sweep_attributes
from nu2.engine.compilation.index import build_index
from nu2.engine.structure import Declared, Inherited, Synthesized


# --- empty schema ---------------------------------------------------------


def test_an_empty_schema_produces_no_attribute_columns(schema):
    schema.finalize()
    term = Leaf()
    p = Program(term, schema)
    build_index(p, term)
    sweep_attributes(p)
    assert p.attrs == {}


# --- synthesized ----------------------------------------------------------


def test_synthesized_fills_leaves_first_then_parents(schema):
    schema.register(
        Synthesized(
            name="size",
            base=lambda program, path: 1,
            combine=lambda own, children: own + sum(children),
        ),
    )
    schema.finalize()
    p = compile(Node(Leaf(), Leaf()), schema)
    # leaves: 1; root: 1 + (1 + 1) = 3
    assert p.attrs["size"] == [3, 1, 1]


def test_synthesized_combine_at_a_leaf_sees_an_empty_child_list(schema):
    seen: list[list[object]] = []

    def combine(own, children):
        seen.append(list(children))
        return own

    schema.register(
        Synthesized(
            name="x",
            base=lambda program, path: 0,
            combine=combine,
        ),
    )
    schema.finalize()
    compile(Leaf(), schema)
    assert seen == [[]]


# --- inherited ------------------------------------------------------------


def test_inherited_threads_root_to_leaves(schema):
    schema.register(
        Inherited(
            name="depth",
            root=lambda program, path: 0,
            derive=lambda program, parent_path, slot, parent_value: parent_value + 1,
        ),
    )
    schema.finalize()
    p = compile(Node(Node(Leaf()), Leaf()), schema)
    # root 0, both children of root depth 1, the deeper leaf depth 2
    assert p.attrs["depth"] == [0, 1, 2, 1]


def test_inherited_derive_receives_the_slot_index(schema):
    schema.register(
        Inherited(
            name="slot",
            root=lambda program, path: -1,
            derive=lambda program, parent_path, slot, parent_value: slot,
        ),
    )
    schema.finalize()
    p = compile(Node(Leaf(), Leaf(), Leaf()), schema)
    assert p.attrs["slot"] == [-1, 0, 1, 2]


# --- cross-attribute dependencies ----------------------------------------


def test_topo_order_schedules_a_dependency_before_its_reader(schema):
    schema.register(
        Synthesized(
            name="a",
            base=lambda program, path: 1,
            combine=lambda own, children: own + sum(children),
        ),
    )
    schema.register(
        Synthesized(
            name="b",
            base=lambda program, path: program.attr(path, "a") * 10,
            combine=lambda own, children: own,
            reads=("a",),
        ),
    )
    schema.finalize()
    p = compile(Node(Leaf()), schema)
    # a at leaf: 1; a at root: 1 + 1 = 2
    # b reads a; at leaf 1*10 = 10; at root 2*10 = 20
    assert p.attrs["a"] == [2, 1]
    assert p.attrs["b"] == [20, 10]


# --- declared attributes are not stored ----------------------------------


def test_declared_attributes_do_not_appear_in_attrs(schema):
    schema.register(Declared(value=42, name="const"))
    schema.finalize()
    p = compile(Leaf(), schema)
    assert "const" not in p.attrs


# --- defensive: unknown attribute kind ----------------------------------


def test_an_unsupported_attribute_kind_raises_type_error(schema):
    from nu2.engine.structure import Computed

    class Strange(Computed):
        pass

    schema.register(Strange(name="weird"))
    schema.finalize()
    with pytest.raises(TypeError, match="unsupported attribute kind"):
        compile(Leaf(), schema)
