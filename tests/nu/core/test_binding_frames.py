"""Every core binding hands its values through a frame of its own.

A binding pushes a frame under the Shape its lambda generated, holding what it
hands, and runs the body on it. Each test checks both halves: the body read
the value, and nothing reached the caller (the Context a run hands back is
the one it was given). Every body execution gets a frame of its own, pushed
from the same parent Context, so work it detaches reads its own value.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import FEED, Body, Feed, seeded, stop, until

import nu
import nu.mem as nm
from nu.engine.structure import Declared
from nu.lang import Context, ScalarAction


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


class Out(nu.Shape):
    log = nm.ListRef.slot(object)


def _ctx() -> tuple[dict, Context]:
    data: dict = {"log": []}
    return data, Context().bind(dict, data, Out)


SEQUENTIAL = [
    pytest.param(
        lambda: nu.ForEachDo(nu.Iter([1, 2]), lambda x: Out.log.append(x)), [1, 2], id="ForEachDo"
    ),
    pytest.param(lambda: nu.ForRangeDo(0, 2, lambda i: Out.log.append(i)), [0, 1], id="ForRangeDo"),
    pytest.param(
        lambda: nu.ForEachDo(
            nu.Collect(nu.Map(nu.Iter([1, 2]), lambda x: nu.Int(x) * 10)),
            lambda x: Out.log.append(x),
        ),
        [10, 20],
        id="Map",
    ),
    pytest.param(
        lambda: nu.ForEachDo(
            nu.Collect(nu.Filter(nu.Iter([1, 2, 3]), lambda x: x > 1)),
            lambda x: Out.log.append(x),
        ),
        [2, 3],
        id="Filter",
    ),
    pytest.param(
        lambda: nu.ForEachDo(
            nu.Collect(nu.SortBy(nu.Iter(["bb", "a"]), lambda s: nu.Len(s))),
            lambda x: Out.log.append(x),
        ),
        ["a", "bb"],
        id="SortBy",
    ),
    pytest.param(
        lambda: nu.TryCatch(nu.Div(1, 0), catch=lambda err: Out.log.append(err)),
        ["division by zero"],
        id="TryCatch",
    ),
]


@pytest.mark.parametrize(("build", "expected"), SEQUENTIAL)
def test_a_binding_hands_its_values_and_leaves_the_caller_alone(
    build: object, expected: list
) -> None:
    data, ctx = _ctx()
    _, out = nu.run(build(), ctx)  # type: ignore[operator]
    assert data["log"] == expected
    assert out is ctx
    assert data == {"log": expected}  # nothing of a frame lands in the caller's dict


@pytest.mark.parametrize(("build", "expected"), SEQUENTIAL)
async def test_a_binding_hands_its_values_and_leaves_the_caller_alone_async(
    build: object, expected: list
) -> None:
    data, ctx = _ctx()
    _, out = await nu.arun(build(), ctx)  # type: ignore[operator]
    assert data["log"] == expected
    assert out is ctx


def test_a_raising_body_leaves_the_caller_alone() -> None:
    data, ctx = _ctx()
    loop = nu.ForEachDo(
        nu.Iter([1, 2]), lambda x: Out.log.append(x) >> nu.raise_(ValueError, "boom")
    )
    with pytest.raises(ValueError, match="boom"):
        nu.run(loop, ctx)
    assert data == {"log": [1]}


def test_a_nested_binding_over_the_same_lambda_shadows_the_outer() -> None:
    # One lambda, one Shape: the inner loop's frame shadows the outer's for
    # its body, and the outer value is read again once the inner loop ends.
    data, ctx = _ctx()

    def nest(depth: int) -> nu.Nu:
        if depth == 0:
            return nu.Noop()
        return nu.ForEachDo(
            nu.Iter([depth * 10]),
            lambda x: Out.log.append(x) >> nest(depth - 1) >> Out.log.append(x),
        )

    nu.run(nest(2), ctx)
    assert data["log"] == [20, 10, 10, 20]


def test_a_lazy_map_reads_each_item_as_it_is_pulled() -> None:
    # Each pulled item gets a frame of its own for its transform.
    stream = nu.Map(nu.Iter([1, 2, 3]), lambda x: nu.Int(x) + 1)
    assert nu.run(nu.Collect(nu.Filter(stream, lambda y: y > 2)))[0] == [3, 4]


def test_two_runs_of_one_tree_get_their_own_frames() -> None:
    term = nu.Collect(nu.Map(nu.Iter([1, 2]), lambda x: x))
    assert nu.run(term)[0] == [1, 2]
    assert nu.run(term)[0] == [1, 2]


async def test_foreach_par_arms_each_read_their_own_item() -> None:
    seen: list = []

    async def arm(rt: object, x: object) -> None:
        await asyncio.sleep(0.01 * (3 - x))  # type: ignore[operator]
        seen.append(x)

    await nu.arun(nu.ForEachParAsync(nu.Iter([1, 2, 3]), lambda x: Body(arm, x)))
    assert seen == [3, 2, 1]


async def test_retry_hooks_read_error_then_attempt() -> None:
    data, ctx = _ctx()
    term = nu.Retry(
        nu.Div(1, 0),
        max_attempts=2,
        on_attempt_fail=lambda err, attempt: Out.log.append(nu.List.of(err, attempt)),
        on_fail=lambda err: Out.log.append(err),
    )
    _, out = await nu.arun(term, ctx)
    assert data["log"] == [["division by zero", 1], "division by zero"]
    assert out is ctx


async def test_react_while_hands_the_key_to_condition_and_body() -> None:
    feed, seen = Feed(), []

    async def record(rt: object, key: object) -> None:
        seen.append(key)

    term = nu.ReactWhile(FEED, lambda key: nu.Str(key) != "stop", lambda key: Body(record, key))
    task = asyncio.ensure_future(nu.arun(term, seeded(feed=feed)))
    await until(lambda: feed.receivers)
    for key in ("a", "b", "stop", "c"):
        feed.fire(key)
    await asyncio.wait_for(task, 5)
    assert seen == ["a", "b"]


async def test_react_every_runs_each_push_their_own_frame() -> None:
    feed, seen = Feed(), []

    async def record(rt: object, key: object) -> None:
        seen.append(key)

    task = asyncio.ensure_future(
        nu.arun(nu.ReactEvery(FEED, lambda key: Body(record, key)), seeded(feed=feed))
    )
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: seen == ["a", "b"])
    await stop(task)


class _Later(ScalarAction):
    """Detached work: schedules its child's read for later and returns at once."""

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, read: object, seen: list) -> None:
        super().__init__(read)
        self._seen = seen

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "_Later is async-only"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (read,) = children
        seen = self._seen

        async def later(rt: Runtime) -> None:
            await asyncio.sleep(0.01)
            seen.append(await read(rt))

        async def athunk(rt: Runtime) -> None:
            _TASKS.append(asyncio.ensure_future(later(rt)))

        return athunk


_TASKS: list[asyncio.Task] = []


async def test_work_a_loop_body_detaches_reads_its_own_item() -> None:
    seen: list = []
    await nu.arun(nu.ForEachDo(nu.Iter([1, 2, 3]), lambda x: _Later(x, seen)))
    await asyncio.gather(*_TASKS)
    _TASKS.clear()
    assert seen == [1, 2, 3]
