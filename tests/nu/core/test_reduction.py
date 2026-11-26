"""Tests for the reduction atoms, and for reductions on the write side.

The core folds are QueryReductions: compile one over a stream source and the
node is SCALAR over a STREAM child, a clean one validates, and each folds as
its Python builtin does. Two test-only atoms, an ActionReduction and a
CommandReduction, fold a stream in slot 1 into one write to a real ref, sync
and async, to show a write can fold a stream as a read does.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nu.mem as nm
from nu.core import Iter
from nu.core.reduction import (
    AllOf,
    AnyOf,
    Collect,
    Count,
    First,
    Last,
    Max,
    Min,
    Sum,
)
from nu.engine.structure import Declared
from nu.lang import LAWS, ActionReduction, Attr, Cardinality, CommandReduction, Literal, gate
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.helpers import compile, validate


_FOLDS = [
    Sum,
    Min,
    Max,
    AnyOf,
    AllOf,
    Count,
    First,
    Last,
    Collect,
]


def _stream() -> Iter:
    return Iter(Literal(range(10)))


@pytest.mark.parametrize("fold", _FOLDS)
def test_reduction_is_scalar_over_a_stream(fold):
    program = compile(fold(_stream()))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


@pytest.mark.parametrize("fold", _FOLDS)
def test_a_reduction_validates(fold):
    program = compile(fold(_stream()))
    assert validate(program) is program


def test_a_scalar_in_the_stream_slot_is_refused():
    # A reduction over a scalar child violates the cardinality law: a fold
    # needs a stream to consume.
    verdict = gate(compile(Sum(Literal(1))), *LAWS)
    assert any(v.law == "reduction_takes_stream" for v in verdict)


# --- evaluation (Sum, Collect) -------------------------------------------


def test_sum_folds_a_stream_to_its_total():
    from nu.lang.helpers import run

    value, _ = run(Sum(Iter(Literal(range(1, 5)))))
    assert value == 10


def test_collect_drains_a_stream_to_a_list():
    from nu.lang.helpers import run

    value, _ = run(Collect(Iter(Literal(range(3)))))
    assert value == [0, 1, 2]


def test_min_and_max_fold_the_extremes():
    from nu.lang.helpers import run

    assert run(Min(Iter(Literal([3, 1, 2]))))[0] == 1
    assert run(Max(Iter(Literal([3, 1, 2]))))[0] == 3


def test_min_of_an_empty_stream_raises():
    from nu.lang.helpers import run

    with pytest.raises(ValueError):
        run(Min(Iter(Literal([]))))


def test_any_and_all_fold_truthiness():
    from nu.lang.helpers import run

    assert run(AnyOf(Iter(Literal([0, 0, 1]))))[0] is True
    assert run(AnyOf(Iter(Literal([0, 0, 0]))))[0] is False
    assert run(AllOf(Iter(Literal([1, 2, 3]))))[0] is True
    assert run(AllOf(Iter(Literal([1, 0, 3]))))[0] is False


def test_count_counts_items():
    from nu.lang.helpers import run

    assert run(Count(Iter(Literal([1, 2, 3, 4]))))[0] == 4


def test_first_and_last_take_the_ends():
    from nu.lang.helpers import run

    assert run(First(Iter(Literal([10, 20, 30]))))[0] == 10
    assert run(Last(Iter(Literal([10, 20, 30]))))[0] == 30


def test_first_of_an_empty_stream_raises_or_takes_a_default():
    from nu.lang.helpers import run

    with pytest.raises(ValueError):
        run(First(Iter(Literal([]))))
    assert run(First(Iter(Literal([])), Literal("d")))[0] == "d"
    assert run(Last(Iter(Literal([])), Literal("d")))[0] == "d"


# --- reductions that write -----------------------------------------------


class Log(nu.Shape):
    entries = nm.ListRef.slot(object)


class AppendTotal(ActionReduction):
    """Appends the total of the stream in slot 1 to the list in slot 0; yields it."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _reduces = Declared(value=1, name="reduces")

    def _compile(self, nid, children):
        target, stream = children

        def thunk(rt):
            total = sum(sync_iter(stream(rt)))
            target(rt).append(total)
            return total

        return thunk

    def _acompile(self, nid, children):
        target, stream = children

        async def athunk(rt):
            total = 0
            async for v in aiter_any(await stream(rt)):
                total += v
            (await target(rt)).append(total)
            return total

        return athunk


class AppendAll(CommandReduction):
    """Appends the whole stream in slot 1 to the list in slot 0, as one entry."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _reduces = Declared(value=1, name="reduces")

    def _compile(self, nid, children):
        target, stream = children

        def thunk(rt):
            target(rt).append(tuple(sync_iter(stream(rt))))

        return thunk

    def _acompile(self, nid, children):
        target, stream = children

        async def athunk(rt):
            items = tuple([v async for v in aiter_any(await stream(rt))])
            (await target(rt)).append(items)

        return athunk


def _run(term, ctx, mode):
    if mode == "sync":
        return nu.run(term, ctx)[0]
    return asyncio.run(nu.arun(term, ctx))[0]


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_an_action_reduction_writes_the_folded_value_once(mode):
    data: dict = {"entries": []}
    ctx = nu.Context().bind(dict, data, Log)
    total = _run(AppendTotal(Log.entries, nu.Iter([1, 2, 3])), ctx, mode)
    assert total == 6
    assert data["entries"] == [6]


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_a_command_reduction_writes_the_folded_stream_once(mode):
    data: dict = {"entries": []}
    ctx = nu.Context().bind(dict, data, Log)
    out = _run(
        AppendAll(Log.entries, nu.Map(nu.Iter([1, 2, 3]), lambda item: nu.Mul(item, 10))),
        ctx,
        mode,
    )
    assert out is None
    assert data["entries"] == [(10, 20, 30)]


def test_a_write_reduction_over_a_scalar_is_refused():
    verdict = gate(compile(AppendTotal(Log.entries, Literal(1))), *LAWS)
    assert any(v.law == "reduction_takes_stream" for v in verdict)
