"""Tests for ReactEach, driven end to end against a hand-fired subscription.

Its whole contract is order: one after the other within a key, side by side
across keys, and every notification runs.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import Body, Feed, start, stop, until

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive.event import ReactEach, ReactEvery
from nu.domains.shape import Shape
from nu.domains.shape.item import ItemRef
from nu.lang import Attr, Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


def test_react_each_is_control():
    assert issubclass(ReactEach, Control)


def test_react_each_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    assert len(nu.tree.children(ReactEach(change, body))) == 2
    assert len(nu.tree.children(ReactEach(change, body, changed_key=ItemRef("k")))) == 3


# ---------------------------------------------------------------------------
# Law validation: a Control driving a mutating body validates. Structural;
# no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_each_validates_with_mutating_body():
    _validate(ReactEach(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_each_mirrors_react_every_metadata():
    body = _Sensor.n.set(_Sensor.n + 1)
    each = compile(ReactEach(_Sensor.n.on_change(), body))
    every = compile(ReactEvery(_Sensor.n.on_change(), body))
    for attr in (Attr.PARAM_SLOTS, Attr.REQUIRES_ASYNC):
        assert each.attr(each.root, attr) == every.attr(every.root, attr)


def test_react_each_sync_thunk_raises():
    r = ReactEach(ItemRef("sub"), ItemRef("body"))
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------


def _each(body: Callable) -> ReactEach:
    return ReactEach(AttrRef("feed"), Body(body), changed_key="k")


def _gated(log: list, holds: list) -> Callable:
    """A body that logs its start, parks on a fresh gate the test releases, then logs its end."""

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        log.append(("start", key))
        gate = asyncio.Event()
        holds.append(gate)
        try:
            await gate.wait()
        finally:
            log.append(("end", key))

    return body


async def test_react_each_runs_one_key_in_order():
    feed, log, holds = Feed(), [], []
    task = start(_each(_gated(log, holds)), feed=feed)
    await until(lambda: feed.receivers)
    for _ in range(3):
        feed.fire("a")
    await until(lambda: log == [("start", "a")])
    await asyncio.sleep(0.01)
    # The second and third wait for the first to end.
    assert log == [("start", "a")]
    holds[0].set()
    await until(lambda: len(log) == 3)
    assert log == [("start", "a"), ("end", "a"), ("start", "a")]
    holds[1].set()
    await until(lambda: len(log) == 5)
    holds[2].set()
    await until(lambda: len(log) == 6)
    assert log[-1] == ("end", "a")
    await stop(task)


async def test_react_each_runs_keys_side_by_side():
    feed, log, holds = Feed(), [], []
    task = start(_each(_gated(log, holds)), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: len(log) == 2)
    assert log == [("start", "a"), ("start", "b")]
    # Releasing b first: a stays parked, b ends on its own.
    holds[1].set()
    await until(lambda: ("end", "b") in log)
    assert ("end", "a") not in log
    await stop(task)


async def test_react_each_runs_a_key_again_after_its_queue_drained():
    feed, runs = Feed(), []

    async def body(rt: Runtime) -> None:
        runs.append(rt.ctx.attrs.get("k"))

    task = start(_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: runs == ["a"])
    await asyncio.sleep(0.01)
    assert not task.done()
    feed.fire("a")
    await until(lambda: runs == ["a", "a"])
    await stop(task)


async def test_react_each_gives_each_run_its_own_key():
    feed, seen = Feed(), []

    async def body(rt: Runtime) -> None:
        first = rt.ctx.attrs.get("k")
        await asyncio.sleep(0.01)
        seen.append((first, rt.ctx.attrs.get("k")))

    task = start(_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: len(seen) == 2)
    # Two runs side by side each keep their own key for their whole run.
    assert sorted(seen) == [("a", "a"), ("b", "b")]
    await stop(task)


async def test_react_each_body_error_propagates_and_cancels_the_others():
    feed, log = Feed(), []

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        if key == "boom":
            raise ValueError("boom")
        log.append(("start", key))
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", key))

    task = start(_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: log == [("start", "a")])
    feed.fire("boom")
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 2)
    # The sibling was cancelled and drained before the flow let go.
    assert log == [("start", "a"), ("end", "a")]
    assert feed.receivers == []
    assert feed.closed


async def test_react_each_cancel_drains_every_run_and_unbinds():
    feed, log, holds = Feed(), [], []
    task = start(_each(_gated(log, holds)), feed=feed)
    await until(lambda: feed.receivers)
    for key in ("a", "a", "b"):
        feed.fire(key)
    await until(lambda: len(log) == 2)
    await stop(task)
    # Both running bodies unwound; the queued second "a" never ran.
    assert sorted(log) == [("end", "a"), ("end", "b"), ("start", "a"), ("start", "b")]
    assert feed.receivers == []
    assert feed.closed
