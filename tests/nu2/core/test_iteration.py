"""Structural tests for the iteration atoms.

These atoms are declared structurally (subclass + Declared attrs, no compile)
because the StreamQuery sources and the one Action all need a fabric/stream
runtime that is not wired yet. So the tests assert sort, cardinality, declared
mutation, and synthesized effects - the facts the language attributes onto a
compiled description - and never evaluate.
"""

from __future__ import annotations

import pytest

from nu2.core.iteration import EnumerateQuery, IterQuery, NextAction, ReversedQuery, ZipQuery
from nu2.lang import LAWS, Attr, Cardinality, Effect, Ref, Sort, compile, gate, validate


_SOURCES = (IterQuery, EnumerateQuery, ZipQuery, ReversedQuery)


# --- sort ----------------------------------------------------------------


@pytest.mark.parametrize("source", _SOURCES)
def test_a_source_is_a_stream_query(source):
    program = compile(source(Ref("xs")))
    assert program.attr(program.root, Attr.SORT) is Sort.STREAM_QUERY


def test_next_is_a_scalar_action():
    program = compile(NextAction(Ref("it")))
    assert program.attr(program.root, Attr.SORT) is Sort.SCALAR_ACTION


# --- cardinality ---------------------------------------------------------


@pytest.mark.parametrize("source", _SOURCES)
def test_a_source_yields_a_stream(source):
    program = compile(source(Ref("xs")))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


def test_next_yields_a_scalar():
    program = compile(NextAction(Ref("it")))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR


# --- effects -------------------------------------------------------------


def test_next_declares_a_write_on_its_iterator():
    # Slot 0 is the mutation slot, so a Ref there binds as a WRITE.
    program = compile(NextAction(Ref()))
    assert program.attr(program.root, Attr.MUTATES) == frozenset({0})
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset({(Ref, Effect.WRITE)})


def test_a_source_only_reads_its_children():
    # A StreamQuery source declares no mutation, so a Ref child is a READ.
    program = compile(IterQuery(Ref()))
    assert program.attr(program.root, Attr.MUTATES) == frozenset()
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset({(Ref, Effect.READ)})


# --- laws ----------------------------------------------------------------


@pytest.mark.parametrize("source", _SOURCES)
def test_a_source_validates(source):
    program = compile(source(Ref("xs")))
    assert validate(program, *LAWS) is program


def test_next_validates():
    program = compile(NextAction(Ref("it")))
    assert validate(program, *LAWS) is program


def test_an_action_yields_so_it_fits_a_query_slot():
    # NextAction is a dual-citizen: it mutates AND yields, so unlike a void Command
    # it composes inside a Query. A Command in the same slot would be refused.
    from nu2.context import SetCommand
    from nu2.core import AddQuery, LiteralQuery

    assert gate(compile(AddQuery(NextAction(Ref("it")), LiteralQuery(1))), *LAWS) == []
    verdict = gate(compile(AddQuery(SetCommand(Ref("x"), LiteralQuery(1)), LiteralQuery(2))), *LAWS)
    assert any(v.law == "composition" for v in verdict)


# --- evaluation (IterQuery) ---------------------------------------------------


def test_iter_streams_a_scalar_iterable():
    from nu2.core import CollectQuery, LiteralQuery
    from nu2.lang.helpers import run

    value, _ = run(CollectQuery(IterQuery(LiteralQuery([1, 2, 3]))))
    assert value == [1, 2, 3]


def test_iter_lifts_a_range_value_into_a_stream():
    # range is a Python value (a type), not a Nu stream atom; IterQuery lifts it.
    from nu2.core import CollectQuery, LiteralQuery
    from nu2.lang.helpers import run

    value, _ = run(CollectQuery(IterQuery(LiteralQuery(range(0, 4)))))
    assert value == [0, 1, 2, 3]


def test_enumerate_pairs_index_and_item():
    from nu2.core import CollectQuery, LiteralQuery
    from nu2.lang.helpers import run

    value, _ = run(CollectQuery(EnumerateQuery(IterQuery(LiteralQuery(["a", "b", "c"])))))
    assert value == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_honors_a_start():
    from nu2.core import CollectQuery, LiteralQuery
    from nu2.lang.helpers import run

    value, _ = run(
        CollectQuery(EnumerateQuery(IterQuery(LiteralQuery(["a", "b"])), LiteralQuery(1)))
    )
    assert value == [(1, "a"), (2, "b")]


def test_zip_threads_sources_to_shortest():
    from nu2.core import CollectQuery, LiteralQuery
    from nu2.lang.helpers import run

    value, _ = run(
        CollectQuery(
            ZipQuery(IterQuery(LiteralQuery([1, 2, 3])), IterQuery(LiteralQuery(["a", "b"])))
        )
    )
    assert value == [(1, "a"), (2, "b")]


def test_reversed_walks_a_source_backwards():
    from nu2.core import CollectQuery, LiteralQuery
    from nu2.lang.helpers import run

    value, _ = run(CollectQuery(ReversedQuery(IterQuery(LiteralQuery([1, 2, 3])))))
    assert value == [3, 2, 1]
