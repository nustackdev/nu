"""Unit tests for ``nu2.lang.attributes.cardinality``.

Covers the ``Cardinality`` enum (SCALAR / STREAM / VOID / TRANSPARENT),
the declared ``CARDINALITY`` per kind, and the synthesized
``CHILD_CARDINALITY`` that forwards a Span's body cardinality through the
transparent wrapper.
"""

from __future__ import annotations

import pytest
from _support.law_terms import Brk, Cmd, FlowC, FlowS, Pol, Q, R, Red, Stream

from nu2.lang import compile as nu_compile
from nu2.lang.attributes import Attr, Cardinality


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Q(), Cardinality.SCALAR),
        (Stream(), Cardinality.STREAM),
        (Red(), Cardinality.SCALAR),
        (R(), Cardinality.SCALAR),
        (Cmd(R()), Cardinality.VOID),
        (FlowS(), Cardinality.VOID),
        (FlowC(), Cardinality.VOID),
        (Brk(), Cardinality.TRANSPARENT),
        (Pol(), Cardinality.TRANSPARENT),
    ],
)
def test_declared_cardinality_per_kind(term, expected):
    program = nu_compile(term)
    assert program.attr((), Attr.CARDINALITY) is expected


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Q(), Cardinality.SCALAR),
        (Stream(), Cardinality.STREAM),
        (Red(), Cardinality.SCALAR),
        (R(), Cardinality.SCALAR),
    ],
)
def test_child_cardinality_for_non_span_equals_own(term, expected):
    program = nu_compile(term)
    nid = program.id_of[()]
    assert program.attrs[Attr.CHILD_CARDINALITY][nid] is expected


def test_child_cardinality_of_inner_node_equals_its_own():
    program = nu_compile(Q(R()))
    inner = program.id_of[(0,)]
    assert program.attrs[Attr.CHILD_CARDINALITY][inner] is Cardinality.SCALAR


def test_bracket_resolves_to_scalar_body():
    program = nu_compile(Brk(Q(R())))
    root = program.id_of[()]
    assert program.attr((), Attr.CARDINALITY) is Cardinality.TRANSPARENT
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.SCALAR


def test_bracket_resolves_to_stream_body():
    program = nu_compile(Brk(Stream(R())))
    root = program.id_of[()]
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.STREAM


def test_nested_span_transparency_passes_through():
    program = nu_compile(Brk(Pol(Stream(R()))))
    root = program.id_of[()]
    inner = program.id_of[(0,)]
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.STREAM
    assert program.attrs[Attr.CHILD_CARDINALITY][inner] is Cardinality.STREAM


def test_empty_bracket_resolves_to_void():
    program = nu_compile(Brk())
    root = program.id_of[()]
    assert program.attr((), Attr.CARDINALITY) is Cardinality.TRANSPARENT
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.VOID


def test_empty_policy_resolves_to_void():
    program = nu_compile(Pol())
    root = program.id_of[()]
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.VOID


def test_command_child_cardinality_is_void():
    program = nu_compile(Cmd(R()))
    root = program.id_of[()]
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.VOID


def test_flow_strategy_child_cardinality_is_void():
    program = nu_compile(FlowS(Cmd(R())))
    root = program.id_of[()]
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.VOID


def test_void_does_not_pass_through_span():
    program = nu_compile(Brk(Cmd(R())))
    root = program.id_of[()]
    assert program.attrs[Attr.CHILD_CARDINALITY][root] is Cardinality.VOID


def test_cardinality_enum_members():
    assert {c.value for c in Cardinality} == {"scalar", "stream", "void", "transparent"}
