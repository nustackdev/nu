"""Structural tests for the IO core atoms (nu2.core.io).

These atoms write through the stdio/filesystem fabric, which is not wired yet,
so they are declared structurally (no eval). We check only what the language
assigns from structure: effect attribution (the slot-0 fabric write), sort,
and cardinality. No execution.
"""

from __future__ import annotations

from nu2.core import Add, Literal
from nu2.core.io import Input, Open, Print
from nu2.lang import Attr, Cardinality, Effect, Ref, Sort, compile


# --- effects: the slot-0 fabric write ------------------------------------


def test_print_declares_a_write_through_its_fabric_ref():
    program = compile(Print(Ref("stdout"), Literal("hi")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("stdout", Effect.WRITE)}
    )


def test_print_reads_its_value_operands():
    program = compile(Print(Ref("stdout"), Add(Ref("x"), Literal(1))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("stdout", Effect.WRITE), ("x", Effect.READ)}
    )


def test_input_declares_a_write_through_its_fabric_ref():
    program = compile(Input(Ref("stdin")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("stdin", Effect.WRITE)}
    )


def test_open_declares_a_write_through_its_fabric_ref():
    program = compile(Open(Ref("fs"), Literal("/tmp/f")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset({("fs", Effect.WRITE)})


# --- sorts ---------------------------------------------------------------


def test_print_is_a_command():
    assert Print.sort.value is Sort.SCALAR_COMMAND


def test_input_and_open_are_scalar_actions():
    assert Input.sort.value is Sort.SCALAR_ACTION
    assert Open.sort.value is Sort.SCALAR_ACTION


# --- cardinality ---------------------------------------------------------


def test_print_yields_nothing():
    assert Print.cardinality.value is Cardinality.VOID


def test_actions_yield_a_scalar():
    assert Input.cardinality.value is Cardinality.SCALAR
    assert Open.cardinality.value is Cardinality.SCALAR
