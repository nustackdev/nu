"""Tests for nu.tree.effects: pre-compile effect analysis.

iter_effects, is_pure, reads, writes, fabrics. The fabric predicates
(touches_fabric / has_write_on_fabric) are covered in test_tree.py.
"""

from __future__ import annotations

import nu.mem
from nu.context import Attr
from nu.core.flows import Sequential
from nu.domains.shape import Shape
from nu.lang import Effect, Literal
from nu.tree import (
    fabrics,
    is_dynamic,
    is_pure,
    iter_effects,
    mutated_slots,
    node_effects,
    reads,
    writes,
)


class State(Shape):
    y = nu.mem.ObjectRef.slot()


def _read_ref():
    return Attr("x")


def _write_tree():
    """A set writes the mem slot ``y``; also reads ``Attr('x')``."""
    target = State.y
    source = Attr("x")
    return target.set(source), target, source


def test_pure_tree_has_no_effects():
    assert is_pure(Sequential(Literal(1), Literal(2)))


def test_tree_with_a_ref_is_not_pure():
    assert not is_pure(Sequential(_read_ref(), Literal(1)))


def test_reads_collects_read_refs():
    cmd, _target, source = _write_tree()
    assert source in reads(cmd)


def test_writes_collects_the_mutation_slot_ref():
    cmd, target, _source = _write_tree()
    assert target in writes(cmd)


def test_write_ref_is_not_also_a_read():
    cmd, target, _source = _write_tree()
    assert target not in reads(cmd)


def test_fabrics_folds_refs_to_their_types():
    cmd, _target, _source = _write_tree()
    assert {nu.mem.ObjectRef, Attr} <= fabrics(cmd)


def test_node_effects_reads_one_level():
    cmd, target, source = _write_tree()
    assert list(node_effects(cmd)) == [(target, Effect.WRITE), (source, Effect.READ)]
    nested = Sequential(cmd)
    assert list(node_effects(nested)) == []  # the refs sit one level down
    assert set(iter_effects(nested)) == {(target, Effect.WRITE), (source, Effect.READ)}


def test_node_effects_skips_a_structural_slot():
    class Inner(Shape):
        y = nu.mem.ObjectRef.slot()

    class Outer(Shape):
        inner = nu.mem.ShapeRef.slot(Inner)

    leaf = Outer.inner.y
    assert list(node_effects(leaf)) == []  # the parent ref is address, not a read
    assert Outer.inner not in reads(leaf.set(1))


def test_mutated_slots():
    cmd, _target, _source = _write_tree()
    assert mutated_slots(cmd) == frozenset({0})
    assert mutated_slots(Literal(1)) == frozenset()


def test_is_dynamic():
    from nu.prog import Eval

    assert is_dynamic(Eval(Literal(1)))
    assert not is_dynamic(Sequential(Literal(1)))
