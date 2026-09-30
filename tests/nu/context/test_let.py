"""Tests for ``Let``: a scoped attr binding.

``Let(name, value, body)`` evaluates ``value`` once, pushes it into
``ctx.attrs[name]`` for the body's duration, and pops on exit (restoring the
prior slot on nesting, or removing it if there was none). The binding is
dereferenceable via an attrs ref (``IntRef(name)``, ``ObjectRef(name)``, ...) inside the body.

These tests cover the load-bearing invariants: eval-once (a single
``value`` evaluation feeds many reads), no leak (the slot is gone after the
body returns), shadowing (nested ``Let`` restores the outer on inner pop),
pop-on-exception (the finally path fires), and async parity.
"""

from __future__ import annotations

from itertools import count

import pytest

from nu import host
from nu.context import IntRef, Let, ObjectRef, StrRef
from nu.core import Add
from nu.lang import EMPTY, Context, Literal
from nu.lang.helpers import arun, run


# --- basic: bind, dereference twice inside body -----------------------------


def test_let_binds_and_dereferences_twice_in_body():
    # body reads IntRef("k") twice; both reads yield the bound value.
    tree = Let("k", Literal(7), Add(IntRef("k"), IntRef("k")))
    value, ctx = run(tree)
    assert value == 14
    # And the binding does not leak past the body.
    assert "k" not in ctx.attrs


# --- shadowing: inner Let masks outer, outer restored on pop ----------------


def test_let_shadows_and_restores_outer_binding():
    # Outer binds x=1; inner rebinds x=2; body reads x -> 2.
    inner = Let("x", Literal(2), IntRef("x"))
    outer = Let("x", Literal(1), inner)
    value, ctx = run(outer)
    assert value == 2
    # After the outer body the outer scope no longer sees x.
    assert "x" not in ctx.attrs


# --- eval-once: value runs once even when body reads many times -------------


def test_let_evaluates_value_once_even_when_body_reads_many_times():
    # A host counter that returns a fresh int on every call; if Let evaluated
    # value per-read, the two reads would see 0 and 1 and their sum would be
    # 1, not 0.
    counter = count()

    @host
    def next_seq() -> int:
        return next(counter)

    tree = Let("seq", next_seq(), Add(IntRef("seq"), IntRef("seq")))
    value, _ = run(tree)
    assert value == 0  # 0 + 0, not 0 + 1


# --- pop-on-exception: binding is removed even when body raises -------------


def test_let_pops_binding_when_body_raises():
    @host
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
    tree = Let("k", Literal(3), Add(IntRef("k"), IntRef("k")))
    value, ctx = await arun(tree)
    assert value == 6
    assert "k" not in ctx.attrs

    # Shadowing round-trips on async too.
    nested = Let("x", Literal(10), Let("x", Literal(20), IntRef("x")))
    value, ctx = await arun(nested)
    assert value == 20
    assert "x" not in ctx.attrs


# --- interaction with .set(): Let scopes, a set on an outer name persists ----


def test_let_scopes_binding_while_body_sets_do_persist():
    # Body inside the Let reassigns a DIFFERENT, already declared slot; that
    # write persists, while Let's own slot is popped when the body returns.
    ctx = Context()
    ctx.attrs["dst"] = 0
    tree = Let(
        "src",
        Literal(5),
        IntRef("dst").set(Add(IntRef("src"), Literal(1))),
    )
    _, ctx = run(tree, ctx)
    assert "src" not in ctx.attrs
    assert ctx.attrs["dst"] == 6


# --- name as a Nu expression: resolved at eval time -------------------------


def test_let_name_can_be_a_nu_expression():
    # Name is a Literal("dyn"): evaluates to "dyn" at eval time, so the body
    # reads back via IntRef("dyn") - same round-trip as the Python-str form.
    tree = Let(Literal("dyn"), 42, body=IntRef("dyn"))
    value, ctx = run(tree)
    assert value == 42
    assert "dyn" not in ctx.attrs


# --- target as an attrs ref ---------------------------------------------------


def test_let_target_can_be_an_attrs_ref():
    n = IntRef("n")
    value, ctx = run(Let(n, 4, n * 2))
    assert value == 8
    assert "n" not in ctx.attrs


def test_let_ref_target_resolves_a_computed_address():
    # IntRef(StrRef("key")) names whatever "key" holds, the same way its read does.
    key = StrRef("key")
    tree = Let(key, "total", Let(IntRef(key), 5, IntRef("total") + 1))
    value, ctx = run(tree)
    assert value == 6
    assert "key" not in ctx.attrs
    assert "total" not in ctx.attrs


async def test_let_ref_target_on_the_async_path():
    key = StrRef("key")
    tree = Let(key, "total", Let(IntRef(key), 5, IntRef("total") + 1))
    value, _ = await arun(tree)
    assert value == 6


# --- declaring without a value ------------------------------------------------


def test_let_without_a_value_declares_the_name_holding_empty():
    x = ObjectRef("x")
    exists, _ = run(Let(x, body=x.exists()))
    read, _ = run(Let(x, body=x.is_empty()))
    assert exists is True
    assert read is True


def test_let_without_a_value_then_set():
    ctx = Context()
    ctx.attrs["out"] = None
    x = IntRef("x")
    _, ctx = run(Let(x, body=x.set(3) >> ObjectRef("out").set(x + 1)), ctx)
    assert ctx.attrs["out"] == 4
    assert "x" not in ctx.attrs


def test_let_without_a_value_binds_the_empty_sentinel():
    value, _ = run(Let("x", body=IntRef("x")))
    assert value is EMPTY


# --- .set() inside a Let ----------------------------------------------------------


def test_set_on_a_declared_name_reassigns_it():
    ctx = Context()
    ctx.attrs["out"] = None
    n = IntRef("n")
    _, ctx = run(Let(n, 1, n.set(n + 1) >> ObjectRef("out").set(n)), ctx)
    assert ctx.attrs["out"] == 2


def test_set_on_an_undeclared_name_raises_with_a_let_hint():
    with pytest.raises(NameError, match=r"not declared.*nu\.Let"):
        run(Let("m", 1, IntRef("n").set(2)))


def test_set_rebinds_the_inner_shadow_and_the_outer_comes_back():
    ctx = Context()
    ctx.attrs["inner"] = None
    ctx.attrs["outer"] = None
    n = IntRef("n")
    inner = Let(n, 2, n.set(3) >> ObjectRef("inner").set(n))
    tree = Let(n, 1, inner >> ObjectRef("outer").set(n))
    _, ctx = run(tree, ctx)
    assert ctx.attrs["inner"] == 3
    assert ctx.attrs["outer"] == 1
    assert "n" not in ctx.attrs


async def test_set_rebinds_the_inner_shadow_on_the_async_path():
    ctx = Context()
    ctx.attrs["outer"] = None
    n = IntRef("n")
    tree = Let(n, 1, Let(n, 2, n.set(3)) >> ObjectRef("outer").set(n))
    _, ctx = await arun(tree, ctx)
    assert ctx.attrs["outer"] == 1


# --- .exists() --------------------------------------------------------------------


def test_exists_is_true_inside_the_let_and_false_after():
    x = ObjectRef("x")
    inside, _ = run(Let(x, 1, x.exists()))
    outside, _ = run(x.exists())
    assert inside is True
    assert outside is False
