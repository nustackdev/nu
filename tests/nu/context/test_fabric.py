"""Tests for the Context fabric axis: FabricRef read, FabricExists.

A FabricRef self-yields the fabric bound by type on the Context
(``ctx.bind`` / ``ctx.get``); unbound, it yields EMPTY. FabricExists
answers whether a binding is present. Fabrics are bound on the Context, never
written through a Ref, so there is no fabric write op - mirrors v1.
"""

from __future__ import annotations

import nustd.mem
from nu.context import FabricExists, FabricRef
from nu.core import IsEmpty
from nu.domains.shape import Shape
from nu.lang import Attr, Context, Effect
from nu.lang.helpers import compile, run


class Clock:
    """A stand-in execution resource bound by type."""


class Saved(Shape):
    """Where a test parks what a FabricRef read."""

    clock = nustd.mem.ObjectRef.slot()


# --- FabricRef read (the dual role) --------------------------------------
# A Ref is not a program on its own (the ``ref_not_root`` law), so the read is
# exercised in a value slot - the way a FabricRef is actually used.


def test_fabricref_yields_a_bound_fabric():
    clock = Clock()
    data: dict = {}
    run(Saved.clock.set(FabricRef(Clock)), Context().bind(Clock, clock).bind(dict, data, Saved))
    assert data["clock"] is clock


def test_fabricref_on_an_unbound_type_is_empty():
    assert run(IsEmpty(FabricRef(Clock)))[0] is True


# --- FabricExists ---------------------------------------------------


def test_fabric_exists_is_true_when_bound():
    ctx = Context().bind(Clock, Clock())
    value, _ = run(FabricExists(FabricRef(Clock)), ctx)
    assert value is True


def test_fabric_exists_is_false_when_unbound():
    value, _ = run(FabricRef(Clock).exists())
    assert value is False


# --- effects -------------------------------------------------------------


def test_fabric_exists_reads_its_ref_fabric():
    program = compile(FabricExists(FabricRef(Clock)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {(FabricRef, Effect.READ)}
    )
