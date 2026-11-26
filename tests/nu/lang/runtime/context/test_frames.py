"""Context frames at the tree level: what a pushed frame reaches and what it never does.

A binding pushes a frame for its body and the body runs on a derived Runtime;
nothing is restored. These tests pin the model: concurrent arms over one Shape
each get their own dict (thread pool and loop), an inner frame shadows its key
and never reroutes a tagged lookup, a stream body holds its frame across its
pulls, an error or a cancel leaves nothing behind, two runs on one Context
never meet, and a task still holding its Runtime reads its frame after the
binding that pushed it has exited.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nu.mem as nm
from nu.context import FabricRef, Provide


class Out(nu.Shape):
    log = nm.ListRef.slot(int)
    first = nm.IntRef.slot()


class S(nu.Shape):
    a = nm.IntRef.slot()


class Rate(nu.Shape):
    pending = nm.ObjectRef.slot()


def _out() -> tuple[dict, nu.Context]:
    data: dict = {"log": []}
    return data, nu.Context().bind(dict, data, Out)


# One lambda, so every arm below binds the same generated Shape.
def _arm(n: nm.ObjectRef) -> nu.Nu:
    return n.set(n * 10) >> nu.Delay(0.03) >> Out.log.append(n)


# --- isolation across concurrent arms ------------------------------------------


def test_threaded_arms_over_one_shape_get_their_own_dict() -> None:
    data, ctx = _out()
    arms = nu.Parallel(nm.let(_arm, n=1), nm.let(_arm, n=2), nm.let(_arm, n=3))
    nu.run(arms, ctx, max_parallel=3)
    assert sorted(data["log"]) == [10, 20, 30]


@pytest.mark.parametrize("max_parallel", [1, 3])
async def test_loop_arms_over_one_shape_get_their_own_dict(max_parallel: int) -> None:
    data, ctx = _out()
    arms = nu.Parallel(nm.let(_arm, n=1), nm.let(_arm, n=2), nm.let(_arm, n=3))
    await nu.arun(arms, ctx, max_parallel=max_parallel)
    assert sorted(data["log"]) == [10, 20, 30]


async def test_foreach_par_arms_each_push_their_own_frame() -> None:
    data, ctx = _out()
    arms = nu.ForEachParAsync(nu.Iter([1, 2, 3]), lambda x: nm.let(_arm, n=x))
    await nu.arun(arms, ctx)
    assert sorted(data["log"]) == [10, 20, 30]


async def test_a_frame_above_the_arms_is_shared_by_them() -> None:
    data, ctx = _out()
    arms = nu.Parallel(S.a.set(S.a + 1), S.a.set(S.a + 1))
    await nu.arun(nm.let(S, arms >> Out.first.set(S.a), a=0), ctx)
    assert data["first"] == 2


# --- shadowing -----------------------------------------------------------------


def test_an_inner_frame_over_the_same_shape_shadows_for_its_body_only() -> None:
    data, ctx = _out()
    inner = nm.let(S, Out.log.append(S.a), a=2)
    nu.run(nm.let(S, Out.log.append(S.a) >> inner >> Out.log.append(S.a), a=1), ctx)
    assert data["log"] == [1, 2, 1]


def test_an_inner_untagged_dict_never_reroutes_a_shape_read() -> None:
    # mem dicts are bound tagged by Shape: an untagged dict provided inside
    # does not hide the frame a Shape's refs read.
    data, ctx = _out()
    body = Provide(dict, kwargs={"a": 99}, body=Out.first.set(S.a))
    nu.run(nm.let(S, body, a=7), ctx)
    assert data["first"] == 7


def test_an_inner_provide_shadows_an_outer_one_of_the_same_class(
    capsys: pytest.CaptureFixture,
) -> None:
    seen = FabricRef(dict)
    inner = Provide(dict, kwargs={"at": "inner"}, body=nu.print(seen))
    outer = Provide(dict, kwargs={"at": "outer"}, body=inner >> nu.print(seen))
    _, ctx = nu.run(outer)
    assert capsys.readouterr().out == "{'at': 'inner'}\n{'at': 'outer'}\n"
    assert ctx.has(dict) is False


# --- streams -------------------------------------------------------------------


async def test_an_async_stream_body_holds_its_frame_across_pulls() -> None:
    stream = nm.let(lambda n: nu.Map(nu.Iter([1, 2, 3]), lambda x: nu.Add(n, x)), n=10)
    ctx = nu.Context()
    agen, _ = await nu.arun(stream, ctx)
    got = []
    async for v in agen:
        got.append(v)
        await asyncio.sleep(0)
    assert got == [11, 12, 13]
    assert ctx.has(dict) is False


# --- error and cancel ----------------------------------------------------------


def test_an_arm_that_raises_leaves_nothing_on_the_parent() -> None:
    data, ctx = _out()
    failing = nm.let(lambda n: nu.raise_(ValueError, "boom"), n=1)
    with pytest.raises(ValueError, match="boom"):
        nu.run(nu.Parallel(nm.let(_arm, n=1), failing), ctx, max_parallel=2)
    assert not ctx.has(dict, S)
    assert ctx.get(dict, Out) is data


async def test_a_cancelled_arm_leaves_its_sibling_and_parent_alone() -> None:
    data, ctx = _out()
    slow = nm.let(lambda n: nu.Delay(1.0) >> Out.log.append(n), n=1)
    fast = nm.let(lambda n: nu.Delay(0.01) >> Out.log.append(n), n=2)
    await nu.arun(nu.Race(slow, fast), ctx)
    assert data["log"] == [2]
    assert ctx.get(dict, Out) is data


# --- runs on one Context -------------------------------------------------------


async def test_two_concurrent_runs_on_one_context_never_meet() -> None:
    data, ctx = _out()
    await asyncio.gather(nu.arun(nm.let(_arm, n=1), ctx), nu.arun(nm.let(_arm, n=2), ctx))
    assert sorted(data["log"]) == [10, 20]


def test_two_runs_on_one_context_each_start_fresh() -> None:
    data, ctx = _out()
    term = nm.let(S, S.a.set(S.a + 1) >> Out.log.append(S.a), a=0)
    nu.run(term, ctx)
    nu.run(term, ctx)
    assert data["log"] == [1, 1]


# --- a task holding its Runtime ------------------------------------------------


async def test_a_delayed_task_reads_its_frame_after_the_binding_exited() -> None:
    # The Debounce case: the delayed body holds the Runtime it was created
    # with, so the let's frame is still there when it fires.
    data, ctx = _out()
    debounced = lambda v: nm.let(Rate, nm.Debounce(0.01, Out.log.append(v), pending=Rate.pending))  # noqa: E731
    await nu.arun(nm.let(debounced, v=41) >> nu.Delay(0.05), ctx)
    assert data["log"] == [41]
