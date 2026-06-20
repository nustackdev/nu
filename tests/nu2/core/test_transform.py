"""Structural tests for the transform atoms (stream-to-stream lenses).

These atoms are declared structurally - StreamQuery subclasses with no
``compile`` yet (the stream runtime is not wired). So coverage is
attribute/law conformance only: assert each is STREAM-carded, takes a stream
source, and a query-only program over them compiles and validates. No eval.
"""

from __future__ import annotations

import pytest

from nu2.core.literal import Literal
from nu2.core.transform import Filter, Flatten, Map, Sorted, Unique
from nu2.lang import LAWS, Attr, Cardinality, compile, gate, validate


ATOMS = [Map, Filter, Sorted, Flatten, Unique]


@pytest.mark.parametrize("atom", ATOMS)
def test_atom_is_a_stream(atom):
    program = compile(atom(Literal([1, 2, 3])))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


@pytest.mark.parametrize("atom", ATOMS)
def test_atom_validates(atom):
    program = compile(atom(Literal([1, 2, 3])))
    assert validate(program, *LAWS) is program


def test_a_lens_chain_stays_a_stream():
    # Lenses compose: a Filter over a Map over a source is still one stream.
    program = compile(Filter(Map(Literal([1, 2, 3]))))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM
    assert validate(program, *LAWS) is program


def test_lenses_carry_no_effects():
    # Pure shape over a constant source - no Context reads or writes.
    program = compile(Map(Literal([1, 2, 3])))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


def test_a_lens_program_does_no_mutation():
    # Query-only, so the program_mutates law warns (it never writes Context).
    program = compile(Sorted(Literal([3, 1, 2])))
    assert any(v.law == "program_mutates" for v in gate(program, *LAWS))
