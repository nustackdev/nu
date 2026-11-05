"""Tests for ReactLatestEach, driven end to end against a hand-fired subscription.

Its whole contract is which run a notification restarts: that key's, and no
other.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import Body, Feed, settle_loop, start, stop, until

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive.event import ReactLatest, ReactLatestEach
from nu.domains.shape import Shape
from nu.domains.shape.item import ItemRef
from nu.lang import Attr, Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


def test_react_latest_each_is_control():
    assert issubclass(ReactLatestEach, Control)


def test_react_latest_each_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    assert len(nu.tree.children(ReactLatestEach(change, body))) == 2
    assert len(nu.tree.children(ReactLatestEach(change, body, changed_key=ItemRef("k")))) == 3


# ---------------------------------------------------------------------------
# Law validation: a Control driving a mutating body validates. Structural;
# no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_latest_each_validates_with_mutating_body():
    _validate(ReactLatestEach(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_latest_each_mirrors_react_latest_metadata():
    body = _Sensor.n.set(_Sensor.n + 1)
    each = compile(ReactLatestEach(_Sensor.n.on_change(), body))
    latest = compile(ReactLatest(_Sensor.n.on_change(), body))
    for attr in (Attr.PARAM_SLOTS, Attr.REQUIRES_ASYNC):
        assert each.attr(each.root, attr) == latest.attr(latest.root, attr)


def test_react_latest_each_sync_thunk_raises():
    r = ReactLatestEach(ItemRef("sub"), ItemRef("body"))
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------


def _latest_each(body: Callable) -> ReactLatestEach:
    return ReactLatestEach(AttrRef("feed"), Body(body), changed_key="k")


def _parked(log: list) -> Callable:
    """A body that logs its start, parks forever, and logs its end when cancelled."""

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        log.append(("start", key))
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", key))

    return body


async def test_react_latest_each_restarts_only_that_key():
    feed, log = Feed(), []
    task = start(_latest_each(_parked(log)), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: len(log) == 2)
    feed.fire("a")
    await until(lambda: len(log) == 4)
    # a's stale run was fully unwound before its fresh one began; b never moved.
    assert log == [("start", "a"), ("start", "b"), ("end", "a"), ("start", "a")]
    await stop(task)


async def test_react_latest_each_finished_run_leaves_and_runs_again_on_the_next_change():
    feed, runs = Feed(), []

    async def body(rt: Runtime) -> None:
        runs.append(rt.ctx.attrs.get("k"))

    task = start(_latest_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: runs == ["a"])
    await asyncio.sleep(0.01)
    assert not task.done()
    feed.fire("a")
    await until(lambda: runs == ["a", "a"])
    await stop(task)


async def test_react_latest_each_restart_does_not_revive_a_run_that_ended():
    feed, log = Feed(), []
    unwinding, release_a, release_b = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        log.append(("start", key))
        if key == "b":
            await release_b.wait()
            log.append(("done", key))
            return
        try:
            await asyncio.Event().wait()
        finally:
            unwinding.set()
            await release_a.wait()  # a slow unwind, during which b finishes
            log.append(("end", key))

    task = start(_latest_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: len(log) == 2)
    feed.fire("a")
    await asyncio.wait_for(unwinding.wait(), 2)
    release_b.set()
    await until(lambda: ("done", "b") in log)
    release_a.set()
    await until(lambda: log[-1] == ("start", "a"))
    await asyncio.sleep(0.02)
    # b ended on its own while a unwound; a's rebirth did not bring b back.
    assert log == [("start", "a"), ("start", "b"), ("done", "b"), ("end", "a"), ("start", "a")]
    await stop(task)


async def test_react_latest_each_collapses_a_burst_on_one_key_and_keeps_the_others():
    feed, log = Feed(), []
    unwinding, gate = asyncio.Event(), asyncio.Event()

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        log.append(("start", key))
        try:
            await asyncio.Event().wait()
        finally:
            if key == "a" and not unwinding.is_set():
                unwinding.set()
                await gate.wait()
            log.append(("end", key))

    task = start(_latest_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: log == [("start", "a")])
    feed.fire("a")
    await asyncio.wait_for(unwinding.wait(), 2)
    for key in ("a", "b", "a"):
        feed.fire(key)
    await asyncio.sleep(0.01)
    gate.set()
    await until(lambda: ("start", "b") in log)
    await asyncio.sleep(0.02)
    # One restart for a, one birth for b, nothing replayed.
    assert log == [("start", "a"), ("end", "a"), ("start", "a"), ("start", "b")]
    await stop(task)


async def test_react_latest_each_gives_each_run_a_fresh_attrs_scope():
    feed, seen = Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append((rt.ctx.attrs.get("k"), rt.ctx.attrs.get("scratch")))
        rt.ctx.attrs.set("scratch", rt.ctx.attrs.get("k"))
        rt.ctx.attrs.set("k", "clobbered")
        await asyncio.Event().wait()

    task = start(_latest_each(body), feed=feed, scratch=None)
    await until(lambda: feed.receivers)
    for n, key in enumerate(("a", "b", "a"), 1):
        feed.fire(key)
        await until(lambda n=n: len(seen) == n)
    # No run sees what an earlier run bound, its own key included, even
    # though every run rebinds both names and a's second run follows a's first.
    assert seen == [("a", None), ("b", None), ("a", None)]
    await stop(task)


async def test_react_latest_each_body_error_propagates_and_cancels_the_others():
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

    task = start(_latest_each(body), feed=feed)
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


async def test_react_latest_each_error_while_unwinding_propagates_before_the_restart():
    feed, starts = Feed(), []

    async def body(rt: Runtime) -> None:
        starts.append(rt.ctx.attrs.get("k"))
        try:
            await asyncio.Event().wait()
        finally:
            raise ValueError("unwind")

    task = start(_latest_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: starts == ["a"])
    feed.fire("a")
    with pytest.raises(ValueError, match="unwind"):
        await asyncio.wait_for(task, 2)
    # The error ended the flow before a fresh run for the key began.
    assert starts == ["a"]
    assert feed.receivers == []
    assert feed.closed


async def test_react_latest_each_sibling_error_during_an_unwind_starts_no_fresh_run():
    feed, log = Feed(), []
    unwinding, boom, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        log.append(("start", key))
        if key == "boom":
            await boom.wait()
            log.append(("raise", key))
            raise ValueError("boom")
        try:
            await asyncio.Event().wait()
        finally:
            unwinding.set()
            await release.wait()  # a slow unwind, during which boom raises
            log.append(("end", key))

    task = start(_latest_each(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("boom")
    await until(lambda: len(log) == 2)
    feed.fire("a")
    await asyncio.wait_for(unwinding.wait(), 2)
    boom.set()
    await until(lambda: ("raise", "boom") in log)
    await settle_loop()  # the error reaches the book before a's unwind ends
    release.set()
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 2)
    # The error cut in ahead of the restart: a's fresh run never began.
    assert log == [("start", "a"), ("start", "boom"), ("raise", "boom"), ("end", "a")]
    assert feed.receivers == []
    assert feed.closed


async def test_react_latest_each_cancel_drains_every_run_and_unbinds():
    feed, log = Feed(), []
    task = start(_latest_each(_parked(log)), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    feed.fire("b")
    await until(lambda: len(log) == 2)
    await stop(task)
    assert sorted(log) == [("end", "a"), ("end", "b"), ("start", "a"), ("start", "b")]
    assert feed.receivers == []
    assert feed.closed
