"""Tests for the Strategy flows: Sequential, Parallel, Race, Gather, AnyN.

Strategy flows compose mutating atoms directly. Coverage builds real programs
of ``SetCmd`` bodies and runs them through ``run`` / ``arun``, asserting the
writes landed. Class-hierarchy and declared-attribute checks pin the basis.
"""

from __future__ import annotations

import pytest

from nu.context import AttrRef, SetCmd
from nu.core.flows import AnyN, Gather, Parallel, Race, Sequential
from nu.lang import Attr, Cardinality, Literal, Strategy
from nu.lang.attributes.execution import ExecOrder
from nu.lang.helpers import arun, compile, run


def _set(name: str, value: object) -> SetCmd:
    return SetCmd(AttrRef(name), Literal(value))


# --- basis ----------------------------------------------------------------


def test_strategies_are_strategy():
    for kind in (Sequential, Parallel, Race, Gather, AnyN):
        assert issubclass(kind, Strategy)


def test_strategy_is_void():
    program = compile(Sequential(_set("a", 1)))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID


def test_parallel_declares_parallel_exec_order():
    program = compile(Parallel(_set("a", 1), _set("b", 2)))
    assert program.attr(program.root, Attr.EXEC_ORDER) is ExecOrder.PARALLEL


def test_anyn_requires_async():
    program = compile(AnyN(_set("a", 1)))
    assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True


# --- Sequential -----------------------------------------------------------


def test_sequential_runs_all_children_in_order():
    _, ctx = run(Sequential(_set("a", 1), _set("b", 2)))
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2


async def test_sequential_async_runs_all_children():
    _, ctx = await arun(Sequential(_set("a", 1), _set("b", 2)))
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2


# --- Parallel / Gather ----------------------------------------------------


def test_parallel_runs_all_children():
    _, ctx = run(Parallel(_set("a", 1), _set("b", 2), _set("c", 3)))
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2
    assert ctx.attrs["c"] == 3


def test_parallel_runs_all_children_on_the_thread_pool():
    # max_parallel > 1 drives the Budget's thread pool rather than the
    # sequential fall-through.
    _, ctx = run(Parallel(_set("a", 1), _set("b", 2), _set("c", 3)), max_parallel=4)
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2
    assert ctx.attrs["c"] == 3


async def test_parallel_async_runs_all_children():
    _, ctx = await arun(Parallel(_set("a", 1), _set("b", 2)))
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2


def test_gather_runs_all_children():
    _, ctx = run(Gather(_set("a", 1), _set("b", 2)))
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2


# --- Race (async-only) ----------------------------------------------------


def test_race_requires_async():
    program = compile(Race(_set("a", 1)))
    assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True


def test_race_sync_run_is_rejected_as_async_only():
    with pytest.raises(RuntimeError):
        run(Race(_set("a", 1), _set("b", 2)))


async def test_race_runs_at_least_the_winner():
    _, ctx = await arun(Race(_set("a", 1), _set("b", 2)))
    assert "a" in ctx.attrs or "b" in ctx.attrs


# --- AnyN -----------------------------------------------------------------


async def test_anyn_succeeds_when_a_child_succeeds():
    _, ctx = await arun(AnyN(_set("a", 1), _set("b", 2)))
    assert "a" in ctx.attrs or "b" in ctx.attrs


def test_anyn_sync_run_is_rejected_as_async_only():
    with pytest.raises(RuntimeError):
        run(AnyN(_set("a", 1)))
