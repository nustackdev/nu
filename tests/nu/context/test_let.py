"""Tests for ``Let``: a scoped attr binding.

``Let(name, value, body)`` evaluates ``value`` once, pushes it into
``ctx.attrs[name]`` for the body's duration, and pops on exit (restoring the
prior slot on nesting, or removing it if there was none). The binding is
dereferenceable via ``AttrRef(name)`` (and typed variants) inside the body.

These tests cover the load-bearing invariants: eval-once (a single
``value`` evaluation feeds many reads), no leak (the slot is gone after the
body returns), shadowing (nested ``Let`` restores the outer on inner pop),
pop-on-exception (the finally path fires), and async parity.
"""

from __future__ import annotations

from itertools import count

import pytest

from nu import host
from nu.context import AttrRef, IntAttrRef, Let, SetCmd
from nu.core import Add, Literal
from nu.lang import Context
from nu.lang.helpers import arun, run


# --- basic: bind, dereference twice inside body -----------------------------


def test_let_binds_and_dereferences_twice_in_body():
    # body reads AttrRef("k") twice; both reads yield the bound value.
    tree = Let("k", Literal(7), Add(IntAttrRef("k"), IntAttrRef("k")))
    value, ctx = run(tree)
    assert value == 14
    # And the binding does not leak past the body.
    assert "k" not in ctx.attrs


# --- shadowing: inner Let masks outer, outer restored on pop ----------------


def test_let_shadows_and_restores_outer_binding():
    # Outer binds x=1; inner rebinds x=2; body reads x -> 2.
    inner = Let("x", Literal(2), IntAttrRef("x"))
    outer = Let("x", Literal(1), inner)
    value, ctx = run(outer)
    assert value == 2
    # After the outer body the outer scope no longer sees x.
    assert "x" not in ctx.attrs


# --- eval-once: value runs once even when body reads many times -------------


def test_let_evaluates_value_once_even_when_body_reads_many_times():
    # A host counter that returns a fresh int on every call; if Let evaluated
    # value per-read, the two reads would see 0 and 1 and their sum would be
    # 1, not 0. deterministic=False keeps the engine from folding the call.
    counter = count()

    @host(deterministic=False)
    def next_seq() -> int:
        return next(counter)

    tree = Let("seq", next_seq(), Add(IntAttrRef("seq"), IntAttrRef("seq")))
    value, _ = run(tree)
    assert value == 0  # 0 + 0, not 0 + 1


# --- pop-on-exception: binding is removed even when body raises -------------


def test_let_pops_binding_when_body_raises():
    @host(deterministic=False)
    def blow_up() -> int:
        raise RuntimeError("boom")

    ctx = Context()
    with pytest.raises(RuntimeError, match="boom"):
        run(Let("k", Literal(99), blow_up()), ctx)
    # The exception unwound through Let's finally; the slot is gone.
    assert "k" not in ctx.attrs


# --- async parity: same semantics under arun --------------------------------


async def test_let_async_matches_sync():
    # Basic bind + two-read behaviour holds on the async path.
    tree = Let("k", Literal(3), Add(IntAttrRef("k"), IntAttrRef("k")))
    value, ctx = await arun(tree)
    assert value == 6
    assert "k" not in ctx.attrs

    # Shadowing round-trips on async too.
    nested = Let("x", Literal(10), Let("x", Literal(20), IntAttrRef("x")))
    value, ctx = await arun(nested)
    assert value == 20
    assert "x" not in ctx.attrs


# --- interaction with SetCmd: Let scopes, SetCmd persists -------------------


def test_let_scopes_binding_while_body_sets_do_persist():
    # Body inside the Let writes a DIFFERENT slot; that write persists,
    # while Let's own slot is popped when the body returns.
    ctx = Context()
    tree = Let(
        "src",
        Literal(5),
        SetCmd(AttrRef("dst"), Add(IntAttrRef("src"), Literal(1))),
    )
    _, ctx = run(tree, ctx)
    assert "src" not in ctx.attrs
    assert ctx.attrs["dst"] == 6


# --- name as a Nu expression: resolved at eval time -------------------------


def test_let_name_can_be_a_nu_expression():
    # Name is a Literal("dyn"): evaluates to "dyn" at eval time, so the body
    # reads back via IntAttrRef("dyn") - same round-trip as the Python-str form.
    tree = Let(Literal("dyn"), 42, body=IntAttrRef("dyn"))
    value, ctx = run(tree)
    assert value == 42
    assert "dyn" not in ctx.attrs
