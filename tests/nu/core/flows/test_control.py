"""Tests for the Control flows: IfDo, WhileDo, ForeverDo, ForEachDo, ForRangeDo, Delay, DelayedDo, SwitchDo.

Control flows steer bodies under Query parameters. Coverage builds real
programs - condition / counter / iterable parameters over ``.set()`` bodies
that read and write a mem dict - and runs them through ``run`` / ``arun``. Class-hierarchy and ``param_slots`` checks pin the basis.
"""

from __future__ import annotations

import nu
import nustd.mem
from nu.context import Attr as AttrRef
from nu.core import Add, Iter, Lt
from nu.core.flows.control import (
    Delay,
    DelayedDo,
    ForEachDo,
    ForeverDo,
    ForRangeDo,
    IfDo,
    SwitchDo,
    WhileDo,
)
from nu.lang import Attr, Cardinality, Context, Control, Literal
from nu.lang.helpers import arun, compile, run


class S(nu.Shape):
    """The mem slots the bodies below write."""

    a = nustd.mem.ObjectRef.slot()
    b = nustd.mem.ObjectRef.slot()
    d = nustd.mem.ObjectRef.slot()
    i = nustd.mem.ObjectRef.slot()
    sum = nustd.mem.ObjectRef.slot()


def _set(name: str, value: object) -> nu.Nu:
    return getattr(S, name).set(Literal(value))


def _incr(name: str) -> nu.Nu:
    """A body that increments slot ``name`` by one."""
    return getattr(S, name).set(Add(getattr(S, name), Literal(1)))


def _seed(**values: object) -> tuple[dict, Context]:
    """A mem dict for ``S`` holding ``values``, and a Context with it bound."""
    data = dict(values)
    return data, Context().bind(dict, data, S)


# --- basis ----------------------------------------------------------------


def test_controls_are_control():
    for kind in (IfDo, WhileDo, ForeverDo, ForEachDo, ForRangeDo, Delay, DelayedDo, SwitchDo):
        assert issubclass(kind, Control)


def test_control_is_void():
    program = compile(IfDo(Literal(True), _set("a", 1)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID


def test_ifdo_param_slots_mark_the_condition():
    program = compile(IfDo(Literal(True), _set("a", 1)))
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset({0})


def test_foreach_param_slots_mark_items_and_name():
    program = compile(ForEachDo(Iter(Literal([1])), _incr("sum")))
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset({0, 2})


# --- IfDo -----------------------------------------------------------------


def test_ifdo_runs_then_when_truthy():
    data, ctx = _seed()
    run(IfDo(Literal(True), _set("a", 1)), ctx)
    assert data["a"] == 1


def test_ifdo_skips_then_when_falsy():
    data, ctx = _seed()
    run(IfDo(Literal(False), _set("a", 1)), ctx)
    assert "a" not in data


def test_ifdo_runs_else_when_falsy():
    data, ctx = _seed()
    run(IfDo(Literal(False), _set("a", 1), _set("b", 2)), ctx)
    assert "a" not in data
    assert data["b"] == 2


async def test_ifdo_async_runs_then():
    data, ctx = _seed()
    await arun(IfDo(Literal(True), _set("a", 1)), ctx)
    assert data["a"] == 1


# --- WhileDo --------------------------------------------------------------


def test_whiledo_loops_until_condition_fails():
    cond = Lt(S.i, Literal(3))
    data, ctx = _seed(i=0)
    run(WhileDo(cond, _incr("i")), ctx)
    assert data["i"] == 3


async def test_whiledo_async_loops():
    cond = Lt(S.i, Literal(3))
    data, ctx = _seed(i=0)
    await arun(WhileDo(cond, _incr("i")), ctx)
    assert data["i"] == 3


# --- ForEachDo ------------------------------------------------------------


def test_foreach_runs_body_per_item():
    body = S.sum.set(Add(S.sum, AttrRef("item")))
    data, ctx = _seed(sum=0)
    run(ForEachDo(Iter(Literal([1, 2, 3])), body), ctx)
    assert data["sum"] == 6


def test_foreach_binds_item_under_custom_name():
    body = S.sum.set(Add(S.sum, AttrRef("x")))
    data, ctx = _seed(sum=0)
    run(ForEachDo(Iter(Literal([10, 20])), body, item="x"), ctx)
    assert data["sum"] == 30


async def test_foreach_async_runs_body_per_item():
    body = S.sum.set(Add(S.sum, AttrRef("item")))
    data, ctx = _seed(sum=0)
    await arun(ForEachDo(Iter(Literal([1, 2, 3])), body), ctx)
    assert data["sum"] == 6


# --- ForRangeDo -----------------------------------------------------------


def test_forrange_sums_the_index_over_the_range():
    body = S.sum.set(Add(S.sum, AttrRef("index")))
    data, ctx = _seed(sum=0)
    run(ForRangeDo(0, 4, body), ctx)
    assert data["sum"] == 6  # 0 + 1 + 2 + 3


def test_forrange_honours_step_and_custom_index_name():
    body = S.sum.set(Add(S.sum, AttrRef("k")))
    data, ctx = _seed(sum=0)
    run(ForRangeDo(0, 10, body, step=2, index="k"), ctx)
    assert data["sum"] == 20  # 0 + 2 + 4 + 6 + 8


# --- Delay ----------------------------------------------------------------


def test_delay_is_childless_control():
    d = Delay(Literal(0.0))
    assert isinstance(d, Control)
    assert len(nu.tree.children(d)) == 1  # the delay param, no body


def test_delay_runs_and_yields_none():
    value, _ = run(Delay(Literal(0.0)))
    assert value is None


async def test_delay_runs_async():
    value, _ = await arun(Delay(Literal(0.0)))
    assert value is None


def test_delay_composes_before_body():
    data, ctx = _seed()
    run(Delay(Literal(0.0)) >> _set("a", 1), ctx)
    assert data["a"] == 1


# --- DelayedDo ------------------------------------------------------------


def test_delayed_runs_body_after_delay():
    data, ctx = _seed()
    run(DelayedDo(Literal(0.0), _set("a", 1)), ctx)
    assert data["a"] == 1


async def test_delayed_async_runs_body_after_delay():
    data, ctx = _seed()
    await arun(DelayedDo(Literal(0.0), _set("a", 1)), ctx)
    assert data["a"] == 1


# --- SwitchDo -------------------------------------------------------------


def test_switch_runs_the_matching_case():
    data, ctx = _seed()
    run(SwitchDo(Literal("b"), {"a": _set("a", 1), "b": _set("b", 2)}), ctx)
    assert "a" not in data
    assert data["b"] == 2


def test_switch_runs_the_default_when_no_case_matches():
    tree = SwitchDo(Literal("z"), {"a": _set("a", 1)}, default=_set("d", 9))
    data, ctx = _seed()
    run(tree, ctx)
    assert "a" not in data
    assert data["d"] == 9


def test_switch_without_default_runs_nothing_on_miss():
    data, ctx = _seed()
    run(SwitchDo(Literal("z"), {"a": _set("a", 1)}), ctx)
    assert "a" not in data


async def test_switch_async_runs_the_matching_case():
    data, ctx = _seed()
    await arun(SwitchDo(Literal("b"), {"a": _set("a", 1), "b": _set("b", 2)}), ctx)
    assert data["b"] == 2


# --- ForeverDo ------------------------------------------------------------
# Runs endlessly by design, so it is exercised structurally, not driven.


def test_foreverdo_compiles_as_a_void_control():
    program = compile(ForeverDo(_set("a", 1)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset()
