"""Structural tests for the iteration atoms.

These atoms are declared structurally (subclass + Declared attrs, no compile)
because the StreamQuery sources and the one Action all need a fabric/stream
runtime that is not wired yet. So the tests assert sort, cardinality, declared
mutation, and synthesized effects - the facts the language attributes onto a
compiled description - and never evaluate.
"""

from __future__ import annotations

import pytest

from nu2.core.iteration import Enumerate, Iter, Next, Range, Reversed, Zip
from nu2.lang import LAWS, Attr, Cardinality, Effect, Ref, Sort, compile, gate, validate


_SOURCES = (Iter, Range, Enumerate, Zip, Reversed)


# --- sort ----------------------------------------------------------------


@pytest.mark.parametrize("source", _SOURCES)
def test_a_source_is_a_stream_query(source):
    program = compile(source(Ref("xs")))
    assert program.attr(program.root, Attr.SORT) is Sort.STREAM_QUERY


def test_next_is_a_scalar_action():
    program = compile(Next(Ref("it")))
    assert program.attr(program.root, Attr.SORT) is Sort.SCALAR_ACTION


# --- cardinality ---------------------------------------------------------


@pytest.mark.parametrize("source", _SOURCES)
def test_a_source_yields_a_stream(source):
    program = compile(source(Ref("xs")))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


def test_next_yields_a_scalar():
    program = compile(Next(Ref("it")))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR


# --- effects -------------------------------------------------------------


def test_next_declares_a_write_on_its_iterator():
    # Slot 0 is the mutation slot, so a Ref there binds as a WRITE.
    program = compile(Next(Ref("it")))
    assert program.attr(program.root, Attr.MUTATES) == frozenset({0})
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset({("it", Effect.WRITE)})


def test_a_source_only_reads_its_children():
    # A StreamQuery source declares no mutation, so a Ref child is a READ.
    program = compile(Iter(Ref("xs")))
    assert program.attr(program.root, Attr.MUTATES) == frozenset()
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset({("xs", Effect.READ)})


# --- laws ----------------------------------------------------------------


@pytest.mark.parametrize("source", _SOURCES)
def test_a_source_validates(source):
    program = compile(source(Ref("xs")))
    assert validate(program, *LAWS) is program


def test_next_validates():
    program = compile(Next(Ref("it")))
    assert validate(program, *LAWS) is program


def test_an_action_yields_so_it_fits_a_query_slot():
    # Next is a dual-citizen: it mutates AND yields, so unlike a void Command
    # it composes inside a Query. A Command in the same slot would be refused.
    from nu2.core import Add, Literal, Set

    assert gate(compile(Add(Next(Ref("it")), Literal(1))), *LAWS) == []
    verdict = gate(compile(Add(Set(Ref("x"), Literal(1)), Literal(2))), *LAWS)
    assert any(v.law == "composition" for v in verdict)
