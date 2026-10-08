"""Every binder scopes its names through the attrs store.

A binder (a loop variable, a caught error, a changed key, a stream
cursor key) binds with ``ctx.attrs.let``: the name shadows an outer binding of
the same spelling while the binder's body runs, and the outer value is back,
or the name is gone, once it ends. Each test checks both halves: the body saw
the binding, and nothing leaked past the run.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from nu.context import Attr
from nu.core import Add, Div, Filter, Iter, Map, SortBy
from nu.core.flows import Noop
from nu.core.flows.control import ForEachDo, ForEachParAsync, ForRangeDo
from nu.core.reactive.event import React, ReactForever, ReactLatest, ReactWhile
from nu.core.reactive.stream import Stream
from nu.core.spans.policy import Retry, TryCatch
from nu.engine.structure import Declared
from nu.forms.collections import List
from nu.lang import Context, Literal, ScalarAction, ScalarQuery
from nu.lang.helpers import acollect, afirst, arun, collect, compile, first, run


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Attributes, Runtime


# --- helpers ---------------------------------------------------------------


class Peek(ScalarAction):
    """Hands ``fn`` the live attrs on either path; the body a Command binder runs."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable[[Attributes], object]) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        def thunk(rt: Runtime) -> object:
            fn(rt.ctx.attrs)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            fn(rt.ctx.attrs)

        return athunk


class Probe(ScalarQuery):
    """Yields ``fn`` of the live attrs on either path; a query binder's child."""

    def __init__(self, fn: Callable[[Attributes], object]) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        def thunk(rt: Runtime) -> object:
            return fn(rt.ctx.attrs)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return fn(rt.ctx.attrs)

        return athunk


class Park(ScalarQuery):
    """Async-only query that signals ``arrived`` and then waits forever."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, arrived: asyncio.Event) -> None:
        super().__init__()
        self._payload["arrived"] = arrived

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "Park was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        arrived = self._payload["arrived"]

        async def athunk(rt: Runtime) -> object:
            arrived.set()
            await asyncio.Event().wait()

        return athunk


def _items(*values: object) -> Iter:
    return Iter(Literal(list(values)))


def _outer(name: str, value: object = "outer", **more: object) -> Context:
    return Context(attrs={name: value, **more})


def _seen(name: str, log: list) -> Peek:
    return Peek(lambda attrs: log.append(attrs.get(name)))


class _Feed:
    """A Subscription the test fires by hand."""

    def __init__(self) -> None:
        self.receivers: list = []

    def __deepcopy__(self, memo: dict) -> _Feed:
        return self

    def bind(self, receiver: Callable) -> None:
        self.receivers.append(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.receivers.remove(receiver)

    def close(self) -> None:
        pass

    def fire(self, key: object) -> None:
        for receiver in list(self.receivers):
            receiver(key)


async def _until(check: Callable[[], bool], timeout: float = 2.0) -> None:
    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), timeout)


async def _cancel(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


# --- a binder over a stream -------------------------------------------------


def test_a_stream_binder_releases_on_exhaustion() -> None:
    values, ctx = collect(compile(Map(_items(1, 2), Add(Attr("x"), 10), key="x")), _outer("x"))
    assert values == [11, 12]
    assert ctx.attrs.get("x") == "outer"


def test_a_stream_binder_releases_on_early_close() -> None:
    value, ctx = first(compile(Map(_items(1, 2), Attr("x"), key="x")), _outer("x"))
    assert value == 1
    assert ctx.attrs.get("x") == "outer"


async def test_a_stream_binder_releases_on_early_close_async() -> None:
    value, ctx = await afirst(compile(Map(_items(1, 2), Attr("x"), key="x")), _outer("x"))
    assert value == 1
    assert ctx.attrs.get("x") == "outer"


async def test_a_stream_binder_releases_on_cancel() -> None:
    arrived = asyncio.Event()
    ctx = _outer("x")
    task = asyncio.ensure_future(acollect(compile(Map(_items(1), Park(arrived), key="x")), ctx))
    await asyncio.wait_for(arrived.wait(), 2)
    assert ctx.attrs.get("x") == 1
    await _cancel(task)
    assert ctx.attrs.get("x") == "outer"


# --- transforms ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Map(_items(1, 2), Attr("x"), key="x"), [1, 2]),
        (Filter(_items(1, 2, 3), Attr("x") > 1, key="x"), [2, 3]),
        (SortBy(_items(2, 1), Attr("x"), item="x"), [1, 2]),
    ],
    ids=["Map", "Filter", "SortBy"],
)
async def test_transform_item_is_scoped(term: object, expected: list) -> None:
    values, ctx = collect(compile(term), _outer("x"))
    assert values == expected
    assert ctx.attrs.get("x") == "outer"
    values, ctx = await acollect(compile(term), _outer("x"))
    assert values == expected
    assert ctx.attrs.get("x") == "outer"


def test_map_item_does_not_reach_the_consumer() -> None:
    # The binding lasts for the transform only: a consumer walking the
    # stream reads the outer value between pulls.
    inner = Map(_items(1, 2), Attr("x"), key="x")
    values, _ = collect(compile(Map(inner, Attr("x"), key="y")), _outer("x"))
    assert values == ["outer", "outer"]


# --- loops --------------------------------------------------------------------


def test_foreach_do_restores_the_item_after_the_loop() -> None:
    log: list = []
    _, ctx = run(ForEachDo(_items(1, 2), _seen("x", log), item="x"), _outer("x"))
    assert log == [1, 2]
    assert ctx.attrs.get("x") == "outer"


def test_foreach_do_leaves_nothing_behind() -> None:
    _, ctx = run(ForEachDo(List.of(1, 2), Noop(), item="x"))
    assert not ctx.attrs.exists("x")


async def test_foreach_do_restores_the_item_after_the_loop_async() -> None:
    log: list = []
    _, ctx = await arun(ForEachDo(_items(1, 2), _seen("x", log), item="x"), _outer("x"))
    assert log == [1, 2]
    assert ctx.attrs.get("x") == "outer"


def test_foreach_do_restores_when_the_body_raises() -> None:
    ctx = _outer("x")
    with pytest.raises(ZeroDivisionError):
        run(ForEachDo(_items(1), Peek(lambda attrs: 1 / 0), item="x"), ctx)
    assert ctx.attrs.get("x") == "outer"


def test_for_range_do_restores_the_index_after_the_loop() -> None:
    log: list = []
    _, ctx = run(ForRangeDo(0, 3, _seen("i", log), index="i"), _outer("i"))
    assert log == [0, 1, 2]
    assert ctx.attrs.get("i") == "outer"


async def test_for_range_do_restores_the_index_after_the_loop_async() -> None:
    log: list = []
    _, ctx = await arun(ForRangeDo(0, 2, _seen("i", log), index="i"), _outer("i"))
    assert log == [0, 1]
    assert ctx.attrs.get("i") == "outer"


async def test_foreach_par_async_binds_each_arm_and_leaves_the_caller_alone() -> None:
    log: list = []
    _, ctx = await arun(ForEachParAsync(_items(1, 2), _seen("x", log), item="x"), _outer("x"))
    assert sorted(log) == [1, 2]
    assert ctx.attrs.get("x") == "outer"


# --- policy -------------------------------------------------------------------


def test_try_catch_error_is_scoped_to_the_catch() -> None:
    term = List.of(TryCatch(Div(1, 0), catch=Attr("error")), Attr("error"))
    (caught, after), ctx = run(term, _outer("error"))
    assert caught == "division by zero"
    assert after == "outer"
    assert ctx.attrs.get("error") == "outer"


async def test_retry_hook_bindings_are_scoped_to_the_hook() -> None:
    log: list = []
    hook = Peek(lambda attrs: log.append((attrs.get("attempt"), attrs.get("error"))))
    term = Retry(Div(1, 0), max_attempts=2, on_attempt_fail=hook, on_fail=hook)
    ctx = _outer("attempt")
    await arun(term, ctx)
    assert log == [(1, "division by zero"), (2, "division by zero")]
    assert ctx.attrs.get("attempt") == "outer"
    assert not ctx.attrs.exists("error")


# --- reactive -----------------------------------------------------------------


async def test_react_changed_key_is_scoped_to_the_body() -> None:
    feed, log = _Feed(), []
    ctx = _outer("k", feed=feed)
    task = asyncio.ensure_future(arun(React(Attr("feed"), _seen("k", log), changed_key="k"), ctx))
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await task
    assert log == ["a"]
    assert ctx.attrs.get("k") == "outer"


async def test_react_while_condition_sees_its_own_turns_key() -> None:
    feed, log, conds = _Feed(), [], []

    def cond(attrs: Attributes) -> bool:
        conds.append(attrs.get("k"))
        return len(conds) < 3

    ctx = _outer("k", feed=feed)
    term = ReactWhile(Attr("feed"), Probe(cond), _seen("k", log), changed_key="k")
    task = asyncio.ensure_future(arun(term, ctx))
    await _until(lambda: feed.receivers)
    for key in ("a", "b", "c"):
        feed.fire(key)
    await task
    assert log == ["a", "b"]
    assert conds == ["a", "b", "c"]
    assert ctx.attrs.get("k") == "outer"


async def test_react_forever_changed_key_is_scoped_to_each_run() -> None:
    feed, log = _Feed(), []
    ctx = _outer("k", feed=feed)
    task = asyncio.ensure_future(
        arun(ReactForever(Attr("feed"), _seen("k", log), changed_key="k"), ctx)
    )
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: log == ["a"])
    assert ctx.attrs.get("k") == "outer"
    await _cancel(task)
    assert ctx.attrs.get("k") == "outer"


async def test_react_latest_changed_key_stays_on_the_run_branch() -> None:
    feed, log = _Feed(), []
    ctx = _outer("k", feed=feed)
    task = asyncio.ensure_future(
        arun(ReactLatest(Attr("feed"), _seen("k", log), changed_key="k"), ctx)
    )
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: log == ["a"])
    await _cancel(task)
    assert ctx.attrs.get("k") == "outer"


# --- stream -------------------------------------------------------------------


async def test_stream_key_lives_while_the_item_drains_and_is_released_on_close() -> None:
    # ``Stream`` has no sync thunk and no substrate yet, so it is driven
    # through its async thunk with hand-made children.
    keys = iter([(0, "a"), (1, "b")])
    ctx = _outer("stream_key")
    rt = type("Rt", (), {"ctx": ctx})()

    async def advance(rt: object) -> object:
        return next(keys, None)

    async def body(rt: Runtime) -> object:
        return [rt.ctx.attrs.get("stream_key")]

    async def name(value: str) -> str:
        return value

    children = (advance, None, body, lambda rt: name("stream_key"), lambda rt: name("log"))
    stream = Stream(Literal(None), Literal(None))
    agen = await stream._acompile(0, children)(rt)
    assert await agen.__anext__() == "a"
    assert ctx.attrs.get("stream_key") == "a"  # alive while the item drains
    await agen.aclose()
    assert ctx.attrs.get("stream_key") == "outer"
