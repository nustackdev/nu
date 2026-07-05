"""Tests for the Control flows: IfDo, WhileDo, ForeverDo, ForEachDo, ForRangeDo, Delay, DelayedDo, SwitchDo.

Control flows steer bodies under Query parameters. Coverage builds real
programs - condition / counter / iterable parameters over ``SetCommand`` bodies
that read and write the attrs side-channel - and runs them through ``run`` /
``arun``. Class-hierarchy and ``param_slots`` checks pin the basis.
"""

from __future__ import annotations

from nu.context import AttrRef, SetCommand
from nu.core import AddQuery, IterQuery, LiteralQuery, LtQuery
from nu.flows.control import (
    Delay,
    DelayedDo,
    ForEachDo,
    ForeverDo,
    ForRangeDo,
    IfDo,
    SwitchDo,
    WhileDo,
)
from nu.lang import Attr, Cardinality, Context, Control, compile
from nu.lang.helpers import arun, run


def _set(name: str, value: object) -> SetCommand:
    return SetCommand(AttrRef(name), LiteralQuery(value))


def _incr(name: str) -> SetCommand:
    """A body that increments ``ctx.attrs[name]`` by one."""
    return SetCommand(AttrRef(name), AddQuery(AttrRef(name), LiteralQuery(1)))


def _seed(**attrs: object) -> Context:
    ctx = Context()
    for key, value in attrs.items():
        ctx.attrs[key] = value
    return ctx


# --- basis ----------------------------------------------------------------


def test_controls_are_control():
    for kind in (IfDo, WhileDo, ForeverDo, ForEachDo, ForRangeDo, Delay, DelayedDo, SwitchDo):
        assert issubclass(kind, Control)


def test_control_is_void():
    program = compile(IfDo(LiteralQuery(True), _set("a", 1)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID


def test_ifdo_param_slots_mark_the_condition():
    program = compile(IfDo(LiteralQuery(True), _set("a", 1)))
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset({0})


def test_foreach_param_slots_mark_items_and_name():
    program = compile(ForEachDo(IterQuery(LiteralQuery([1])), _incr("sum")))
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset({0, 2})


# --- IfDo -----------------------------------------------------------------


def test_ifdo_runs_then_when_truthy():
    _, ctx = run(IfDo(LiteralQuery(True), _set("a", 1)))
    assert ctx.attrs["a"] == 1


def test_ifdo_skips_then_when_falsy():
    _, ctx = run(IfDo(LiteralQuery(False), _set("a", 1)))
    assert "a" not in ctx.attrs


def test_ifdo_runs_else_when_falsy():
    _, ctx = run(IfDo(LiteralQuery(False), _set("a", 1), _set("b", 2)))
    assert "a" not in ctx.attrs
    assert ctx.attrs["b"] == 2


async def test_ifdo_async_runs_then():
    _, ctx = await arun(IfDo(LiteralQuery(True), _set("a", 1)))
    assert ctx.attrs["a"] == 1


# --- WhileDo --------------------------------------------------------------


def test_whiledo_loops_until_condition_fails():
    cond = LtQuery(AttrRef("i"), LiteralQuery(3))
    _, ctx = run(WhileDo(cond, _incr("i")), _seed(i=0))
    assert ctx.attrs["i"] == 3


async def test_whiledo_async_loops():
    cond = LtQuery(AttrRef("i"), LiteralQuery(3))
    _, ctx = await arun(WhileDo(cond, _incr("i")), _seed(i=0))
    assert ctx.attrs["i"] == 3


# --- ForEachDo ------------------------------------------------------------


def test_foreach_runs_body_per_item():
    body = SetCommand(AttrRef("sum"), AddQuery(AttrRef("sum"), AttrRef("item")))
    _, ctx = run(ForEachDo(IterQuery(LiteralQuery([1, 2, 3])), body), _seed(sum=0))
    assert ctx.attrs["sum"] == 6


def test_foreach_binds_item_under_custom_name():
    body = SetCommand(AttrRef("sum"), AddQuery(AttrRef("sum"), AttrRef("x")))
    _, ctx = run(ForEachDo(IterQuery(LiteralQuery([10, 20])), body, item="x"), _seed(sum=0))
    assert ctx.attrs["sum"] == 30


async def test_foreach_async_runs_body_per_item():
    body = SetCommand(AttrRef("sum"), AddQuery(AttrRef("sum"), AttrRef("item")))
    _, ctx = await arun(ForEachDo(IterQuery(LiteralQuery([1, 2, 3])), body), _seed(sum=0))
    assert ctx.attrs["sum"] == 6


# --- ForRangeDo -----------------------------------------------------------


def test_forrange_sums_the_index_over_the_range():
    body = SetCommand(AttrRef("sum"), AddQuery(AttrRef("sum"), AttrRef("index")))
    _, ctx = run(ForRangeDo(0, 4, body), _seed(sum=0))
    assert ctx.attrs["sum"] == 6  # 0 + 1 + 2 + 3


def test_forrange_honours_step_and_custom_index_name():
    body = SetCommand(AttrRef("sum"), AddQuery(AttrRef("sum"), AttrRef("k")))
    _, ctx = run(ForRangeDo(0, 10, body, step=2, index="k"), _seed(sum=0))
    assert ctx.attrs["sum"] == 20  # 0 + 2 + 4 + 6 + 8


# --- Delay ----------------------------------------------------------------


def test_delay_is_childless_control():
    d = Delay(LiteralQuery(0.0))
    assert isinstance(d, Control)
    assert len(d._children) == 1  # the delay param, no body


def test_delay_runs_and_yields_none():
    value, _ = run(Delay(LiteralQuery(0.0)))
    assert value is None


async def test_delay_runs_async():
    value, _ = await arun(Delay(LiteralQuery(0.0)))
    assert value is None


def test_delay_composes_before_body():
    _, ctx = run(Delay(LiteralQuery(0.0)) >> _set("a", 1))
    assert ctx.attrs["a"] == 1


# --- DelayedDo ------------------------------------------------------------


def test_delayed_runs_body_after_delay():
    _, ctx = run(DelayedDo(LiteralQuery(0.0), _set("a", 1)))
    assert ctx.attrs["a"] == 1


async def test_delayed_async_runs_body_after_delay():
    _, ctx = await arun(DelayedDo(LiteralQuery(0.0), _set("a", 1)))
    assert ctx.attrs["a"] == 1


# --- SwitchDo -------------------------------------------------------------


def test_switch_runs_the_matching_case():
    _, ctx = run(SwitchDo(LiteralQuery("b"), {"a": _set("a", 1), "b": _set("b", 2)}))
    assert "a" not in ctx.attrs
    assert ctx.attrs["b"] == 2


def test_switch_runs_the_default_when_no_case_matches():
    tree = SwitchDo(LiteralQuery("z"), {"a": _set("a", 1)}, default=_set("d", 9))
    _, ctx = run(tree)
    assert "a" not in ctx.attrs
    assert ctx.attrs["d"] == 9


def test_switch_without_default_runs_nothing_on_miss():
    _, ctx = run(SwitchDo(LiteralQuery("z"), {"a": _set("a", 1)}))
    assert "a" not in ctx.attrs


async def test_switch_async_runs_the_matching_case():
    _, ctx = await arun(SwitchDo(LiteralQuery("b"), {"a": _set("a", 1), "b": _set("b", 2)}))
    assert ctx.attrs["b"] == 2


# --- ForeverDo ------------------------------------------------------------
# Runs endlessly by design, so it is exercised structurally, not driven.


def test_foreverdo_compiles_as_a_void_control():
    program = compile(ForeverDo(_set("a", 1)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset()
