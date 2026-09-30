"""Tests for nu.tree.effects: pre-compile effect analysis.

iter_effects, is_pure, reads, writes, fabrics. The fabric predicates
(touches_fabric / has_write_on_fabric) are covered in test_tree.py.
"""

from __future__ import annotations

import nu.mem
from nu.context import Attr
from nu.core.flows import Sequential
from nu.domains.shape import Shape
from nu.lang import Literal
from nu.tree import fabrics, is_pure, reads, writes


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
