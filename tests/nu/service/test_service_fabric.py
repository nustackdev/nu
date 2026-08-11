"""Functional tests for nu.service: the in-process Service fabric.

Every test wraps a body Term in `With(bind(Calc, target=fresh_calculator), body=...)`
via the `app` fixture, then drives it through `run` / `arun` (scalar bodies)
or `nu.Collect`-then-`run` (stream bodies). Assertions check both the value
returned by the interaction and the resulting mutation on the target object.
"""

from __future__ import annotations

import pytest

import nu

from .conftest import Calc, Calculator, CalcWithDefaults


# --- scalar Query -----------------------------------------------------------


def test_query_returns_target_return_value(app):
    value, _ = nu.run(app(Calc.add(a=1, b=2)))
    assert value == 3


def test_query_does_not_mutate_target(app, target: Calculator):
    nu.run(app(Calc.mul(a=6, b=7)))
    assert target.total == 0.0
    assert target.log == []


@pytest.mark.asyncio
async def test_query_async_target_via_arun(app):
    value, _ = await nu.arun(app(Calc.aadd(a=4, b=5)))
    assert value == 9


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_query_async_target_under_sync_run_raises(app):
    with pytest.raises(RuntimeError, match=r"awaitable under nu\.run"):
        nu.run(app(Calc.aadd(a=1, b=2)))


# --- scalar Action ----------------------------------------------------------


def test_action_returns_value_and_mutates_target(app, target: Calculator):
    value, _ = nu.run(app(Calc.bump(by=5)))
    assert value == 5.0
    assert target.total == 5.0
    assert target.log == [("bump", (5,))]


def test_action_state_accumulates_across_calls(app, target: Calculator):
    nu.run(app(nu.Sequential(Calc.bump(by=3), Calc.bump(by=4), Calc.bump(by=2))))
    assert target.total == 9.0


@pytest.mark.asyncio
async def test_action_async_target(app, target: Calculator):
    value, _ = await nu.arun(app(Calc.abump(by=7)))
    assert value == 7.0
    assert target.total == 7.0


# --- void Command -----------------------------------------------------------


def test_command_yields_nothing_and_mutates(app, target: Calculator):
    target.total = 42.0
    value, _ = nu.run(app(Calc.reset()))
    assert value is None
    assert target.total == 0.0
    assert target.log == [("reset", ())]


def test_command_drops_target_return_value(app, target: Calculator):
    # Calculator.reset returns None already, but the contract holds regardless:
    # a CommandRef never surfaces the target's return value to the caller.
    value, _ = nu.run(app(Calc.reset()))
    assert value is None


@pytest.mark.asyncio
async def test_command_async_target(app, target: Calculator):
    target.total = 10.0
    value, _ = await nu.arun(app(Calc.areset()))
    assert value is None
    assert target.total == 0.0


# --- stream Query -----------------------------------------------------------


def test_stream_query_from_generator(app):
    values, _ = nu.run(app(nu.Collect(Calc.squares(n=4))))
    assert values == [0, 1, 4, 9]


def test_stream_query_from_list(app):
    values, _ = nu.run(app(nu.Collect(Calc.tens(n=3))))
    assert values == [0, 10, 20]


def test_stream_query_reduces_with_sum(app):
    total, _ = nu.run(app(nu.Sum(Calc.squares(n=4))))
    assert total == 14  # 0 + 1 + 4 + 9


@pytest.mark.asyncio
async def test_stream_query_async_target(app):
    values, _ = await nu.arun(app(nu.Collect(Calc.arange(n=3))))
    assert values == [100, 101, 102]


# --- stream Action ----------------------------------------------------------


def test_stream_action_yields_and_mutates(app, target: Calculator):
    target.log = [("a", ()), ("b", ())]
    values, _ = nu.run(app(nu.Collect(Calc.drain())))
    assert values == [("a", ()), ("b", ())]
    assert target.log == []


# --- defaults / target_attr wiring ------------------------------------------


def test_defaults_are_merged_into_call_kwargs(defaults_app):
    # add's default is b=100; call only passes a.
    value, _ = nu.run(defaults_app(CalcWithDefaults.add(a=5)))
    assert value == 105


def test_call_kwargs_override_defaults(defaults_app):
    # Call-site b= wins over the default b=100.
    value, _ = nu.run(defaults_app(CalcWithDefaults.add(a=5, b=1)))
    assert value == 6


def test_target_attr_override_selects_a_different_attribute(app, target: Calculator):
    # Calc.squares is declared with name="range", so it dispatches to
    # Calculator.range even though the field name is "squares".
    values, _ = nu.run(app(nu.Collect(Calc.squares(n=3))))
    assert values == [0, 1, 4]


# --- fabric binding ---------------------------------------------------------


def test_fabric_is_bound_tagged_by_service_class():
    calc_a = Calculator()
    calc_b = Calculator()

    class OtherSvc(nu.Service):
        add = nu.service.QueryRef.method()

    # Two services in one program, each with its own target: readings do not
    # cross-contaminate because bind() tags the fabric by the Service class.
    binds = [
        nu.service.bind(Calc, target=calc_a),
        nu.service.bind(OtherSvc, target=calc_b),
    ]
    # Read from OtherSvc's target, mutate Calc's target: no crossover.
    value, _ = nu.run(nu.With(*binds, body=OtherSvc.add(a=1, b=2)))
    assert value == 3
    nu.run(nu.With(*binds, body=Calc.bump(by=3)))
    assert calc_a.total == 3.0
    assert calc_b.total == 0.0


def test_unknown_target_attribute_raises_at_call_time(app):
    class Bad(nu.Service):
        missing = nu.service.QueryRef.method()

    tree = nu.With(
        nu.service.bind(Bad, target=Calculator()),
        body=Bad.missing(),
    )
    with pytest.raises(AttributeError):
        nu.run(tree)
