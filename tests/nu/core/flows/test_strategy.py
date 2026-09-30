"""Tests for the Strategy flows: Sequential, Parallel, Race, Gather, AnyN.

Strategy flows compose mutating atoms directly. Coverage builds real programs
of ``.set()`` bodies over a mem dict and runs them through ``run`` / ``arun``,
asserting the writes landed. A concurrent arm runs on its own branch, but the
dict bound around it is shared by reference, so arm writes land in it too. Class-hierarchy and declared-attribute checks pin the basis.
"""

from __future__ import annotations

import pytest
from _support.policy_atoms import RecordAction

import nu
import nustd.mem
from nu.core.flows import AnyN, Gather, Parallel, Race, Sequential
from nu.lang import Attr, Cardinality, Context, Literal, Strategy
from nu.lang.attributes.execution import ExecOrder
from nu.lang.helpers import arun, compile, run


class S(nu.Shape):
    """The mem slots the bodies below write."""

    a = nustd.mem.ObjectRef.slot()
    b = nustd.mem.ObjectRef.slot()


def _set(name: str, value: object) -> nu.Nu:
    return getattr(S, name).set(Literal(value))


def _mem() -> tuple[dict, Context]:
    """An empty mem dict for ``S``, and a Context with it bound."""
    data: dict = {}
    return data, Context().bind(dict, data, S)


def _tags(log: list) -> list[str]:
    """The tags of the ``RecordAction`` children that ran, sorted."""
    return sorted(tag for tag, _, _ in log)


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
    data, ctx = _mem()
    run(Sequential(_set("a", 1), _set("b", 2)), ctx)
    assert data == {"a": 1, "b": 2}


async def test_sequential_async_runs_all_children():
    data, ctx = _mem()
    await arun(Sequential(_set("a", 1), _set("b", 2)), ctx)
    assert data == {"a": 1, "b": 2}


# --- Parallel / Gather ----------------------------------------------------


def test_parallel_runs_all_children():
    log: list = []
    run(Parallel(RecordAction(log, "a"), RecordAction(log, "b"), RecordAction(log, "c")))
    assert _tags(log) == ["a", "b", "c"]


def test_parallel_arms_share_the_mem_dict_bound_around_them():
    data, ctx = _mem()
    run(Parallel(_set("a", 1), _set("b", 2)), ctx)
    assert data == {"a": 1, "b": 2}


def test_parallel_runs_all_children_on_the_thread_pool():
    # max_parallel > 1 drives the Budget's thread pool rather than the
    # sequential fall-through.
    log: list = []
    run(
        Parallel(RecordAction(log, "a"), RecordAction(log, "b"), RecordAction(log, "c")),
        max_parallel=4,
    )
    assert _tags(log) == ["a", "b", "c"]


async def test_parallel_async_runs_all_children():
    log: list = []
    await arun(Parallel(RecordAction(log, "a"), RecordAction(log, "b")))
    assert _tags(log) == ["a", "b"]


def test_gather_runs_all_children():
    log: list = []
    run(Gather(RecordAction(log, "a"), RecordAction(log, "b")))
    assert _tags(log) == ["a", "b"]


# --- Race (async-only) ----------------------------------------------------


def test_race_requires_async():
    program = compile(Race(_set("a", 1)))
    assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True


def test_race_sync_run_is_rejected_as_async_only():
    with pytest.raises(RuntimeError):
        run(Race(_set("a", 1), _set("b", 2)))


async def test_race_runs_at_least_the_winner():
    log: list = []
    await arun(Race(RecordAction(log, "a"), RecordAction(log, "b")))
    assert _tags(log)


# --- AnyN -----------------------------------------------------------------


async def test_anyn_succeeds_when_a_child_succeeds():
    log: list = []
    await arun(AnyN(RecordAction(log, "a"), RecordAction(log, "b")))
    assert _tags(log)


def test_anyn_sync_run_is_rejected_as_async_only():
    with pytest.raises(RuntimeError):
        run(AnyN(_set("a", 1)))
