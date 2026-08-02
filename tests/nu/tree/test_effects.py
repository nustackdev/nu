"""Tests for nu.tree.effects: pre-compile effect analysis.

iter_effects, is_pure, reads, writes, fabrics. The fabric predicates
(touches_fabric / has_write_on_fabric) are covered in test_tree.py.
"""

from __future__ import annotations

from nu.context import AttrRef, SetCmd
from nu.core import Literal
from nu.flows import Sequential
from nu.tree import fabrics, is_pure, reads, writes


def _read_ref():
    return AttrRef("x")


def _write_tree():
    """SetCmd writes AttrRef('y'); also reads AttrRef('x')."""
    target = AttrRef("y")
    source = AttrRef("x")
    return SetCmd(target, source), target, source


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
    assert AttrRef in fabrics(cmd)
