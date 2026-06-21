"""Tests for the Context service axis: ServiceRef read, ServiceExists.

A ServiceRef self-yields the service bound by type on the Context
(``ctx.bind`` / ``ctx.get``); unbound, it yields EMPTY. ServiceExists answers
whether a binding is present. Services are bound on the Context, never written
through a Ref, so there is no service write op - mirrors v1.
"""

from __future__ import annotations

from nu2.context import AttrRef, ServiceExists, ServiceRef, Set
from nu2.lang import Attr, Context, Effect, compile
from nu2.lang.helpers import run


class Clock:
    """A stand-in execution resource bound by type."""


# --- ServiceRef read (the dual role) -------------------------------------
# A Ref is not a program on its own (the ``ref_not_root`` law), so the read is
# exercised in a value slot - the way a ServiceRef is actually used.


def test_serviceref_yields_a_bound_service():
    clock = Clock()
    ctx = Context().bind(Clock, clock)
    _, ctx = run(Set(AttrRef("saved"), ServiceRef(Clock)), ctx)
    assert ctx.attrs["saved"] is clock


def test_serviceref_on_an_unbound_type_is_empty():
    # Unbound -> EMPTY; Set's sentinel guard then leaves the slot unwritten.
    ctx = Context()
    _, ctx = run(Set(AttrRef("saved"), ServiceRef(Clock)), ctx)
    assert "saved" not in ctx.attrs


# --- ServiceExists -------------------------------------------------------


def test_service_exists_is_true_when_bound():
    ctx = Context().bind(Clock, Clock())
    value, _ = run(ServiceExists(ServiceRef(Clock)), ctx)
    assert value is True


def test_service_exists_is_false_when_unbound():
    value, _ = run(ServiceRef(Clock).exists())
    assert value is False


# --- effects -------------------------------------------------------------


def test_service_exists_reads_its_ref_fabric():
    program = compile(ServiceExists(ServiceRef(Clock)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {(ServiceRef, Effect.READ)}
    )
