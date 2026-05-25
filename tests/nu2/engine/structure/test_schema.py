"""Unit tests for ``nu2.engine.structure.schema``.

Covers :class:`Schema` -- registration, resolution, finalize and its
topological order, plus the two failure modes
(:exc:`CycleError`, :exc:`NotFinalizedError`).
"""

from __future__ import annotations

import pytest
from _support.terms import HeavyNode, Leaf, Node

from nu2.engine.structure import (
    CycleError,
    Declared,
    NotFinalizedError,
    Synthesized,
)


# --- helpers --------------------------------------------------------------


def _noop_synth(name: str, reads: tuple[str, ...] = ()) -> Synthesized:
    """A synthesized attribute that does nothing; only its ``reads`` matter."""
    return Synthesized(
        name=name,
        base=lambda p, path: 0,
        combine=lambda own, children: own,
        reads=reads,
    )


# --- registration ---------------------------------------------------------


def test_a_fresh_schema_contains_nothing(schema):
    assert "anything" not in schema
    with pytest.raises(KeyError):
        schema["missing"]


def test_register_adds_an_attribute_by_name(schema):
    schema.register(Declared(value=42, name="answer"))
    assert "answer" in schema
    assert schema["answer"].value == 42


def test_register_without_a_name_raises(schema):
    with pytest.raises(ValueError, match="must have a name"):
        schema.register(Declared(value=1))


def test_register_replaces_a_prior_entry_of_the_same_name(schema):
    schema.register(Declared(value=1, name="x"))
    schema.register(Declared(value=2, name="x"))
    assert schema["x"].value == 2


# --- resolve --------------------------------------------------------------


def test_resolve_finds_a_per_class_attribute(schema):
    # ``Leaf.sort`` is class-declared; the schema has no tree-wide ``sort``.
    assert schema.resolve(Leaf, "sort").value == "Leaf"


def test_resolve_finds_a_tree_wide_attribute(schema):
    schema.register(Declared(value="default", name="origin"))
    assert schema.resolve(Leaf, "origin").value == "default"


def test_per_class_overrides_tree_wide(schema):
    # ``Leaf`` declares ``sort`` itself; a tree-wide default must lose.
    schema.register(Declared(value="default", name="sort"))
    assert schema.resolve(Leaf, "sort").value == "Leaf"


def test_subclass_override_wins_over_parent(schema):
    # ``HeavyNode`` overrides ``weight``; the parent's value must not surface.
    assert schema.resolve(Node, "weight").value == 1
    assert schema.resolve(HeavyNode, "weight").value == 9


def test_resolve_returns_none_when_unknown(schema):
    assert schema.resolve(Leaf, "missing") is None


# --- finalize and topo order ----------------------------------------------


def test_finalize_returns_the_schema_for_chaining(schema):
    assert schema.finalize() is schema


def test_finalize_orders_reads_before_consumers(schema):
    schema.register(_noop_synth("c", reads=("b",)))
    schema.register(_noop_synth("b", reads=("a",)))
    schema.register(_noop_synth("a"))
    schema.finalize()
    order = schema.topo_order()
    assert order.index("a") < order.index("b") < order.index("c")


def test_topo_order_skips_declared_dependencies(schema):
    # ``computed`` reads a declared (non-computed) attribute; declared
    # attributes are class constants and do not appear in the order.
    schema.register(Declared(value=0, name="konst"))
    schema.register(_noop_synth("computed", reads=("konst",)))
    schema.finalize()
    assert schema.topo_order() == ["computed"]


def test_topo_order_skips_unknown_dependencies(schema):
    # Reads that refer to nothing registered are silently dropped; the
    # ordering is built on edges that exist.
    schema.register(_noop_synth("solo", reads=("ghost",)))
    schema.finalize()
    assert schema.topo_order() == ["solo"]


def test_finalize_detects_a_two_node_cycle(schema):
    schema.register(_noop_synth("x", reads=("y",)))
    schema.register(_noop_synth("y", reads=("x",)))
    with pytest.raises(CycleError, match="cyclic attribute dependency"):
        schema.finalize()


def test_finalize_detects_a_self_cycle(schema):
    schema.register(_noop_synth("x", reads=("x",)))
    with pytest.raises(CycleError):
        schema.finalize()


def test_finalize_detects_a_long_cycle(schema):
    schema.register(_noop_synth("a", reads=("b",)))
    schema.register(_noop_synth("b", reads=("c",)))
    schema.register(_noop_synth("c", reads=("a",)))
    with pytest.raises(CycleError):
        schema.finalize()


# --- finalize lifecycle ---------------------------------------------------


def test_topo_order_before_finalize_raises(schema):
    with pytest.raises(NotFinalizedError, match="not finalized"):
        schema.topo_order()


def test_register_invalidates_a_prior_finalize(schema):
    schema.register(_noop_synth("a"))
    schema.finalize()
    schema.register(_noop_synth("b"))
    with pytest.raises(NotFinalizedError):
        schema.topo_order()


def test_finalize_can_be_called_again_after_register(schema):
    schema.register(_noop_synth("a"))
    schema.finalize()
    schema.register(_noop_synth("b", reads=("a",)))
    schema.finalize()
    order = schema.topo_order()
    assert order.index("a") < order.index("b")


def test_empty_schema_finalizes_to_empty_order(schema):
    schema.finalize()
    assert schema.topo_order() == []
