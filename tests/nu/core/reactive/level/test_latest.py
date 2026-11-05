"""Tests for ReconcileLatest: one arm for the one id read from state."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import (
    QUIET,
    Body,
    Feed,
    Read,
    live_rechecks,
    settle_loop,
    start,
    stop,
    until,
)

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive import ReconcileLatest
from nu.lang import NULL


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


def _hold(
    state: dict, log: list, plan: dict | None = None, reads: list | None = None, **schedule: object
) -> ReconcileLatest:
    """An arm for ``state["id"]`` that logs start and end, and parks, finishes or raises per ``plan``."""
    plan = plan or {}

    async def read(rt: Runtime) -> object:
        if reads is not None:
            reads.append(state["id"])
        return state["id"]

    async def arm(rt: Runtime) -> None:
        x = rt.ctx.attrs.get("x")
        log.append(("start", x))
        try:
            if plan.get(x) == "boom":
                msg = f"boom {x}"
                raise ValueError(msg)
            if plan.get(x, "park") == "park":
                await asyncio.Event().wait()
        finally:
            log.append(("end", x))

    return ReconcileLatest(Read(read), AttrRef("feed"), Body(arm), "x", **schedule)


def _starts(log: list, key: object) -> int:
    return log.count(("start", key))


# ---------------------------------------------------------------------------
# the law: ReconcileLatest(const v, c, f) runs f(v) once and then holds
# ---------------------------------------------------------------------------


async def test_a_constant_id_runs_the_body_once_and_holds() -> None:
    feed, log = Feed(), []

    async def arm(rt: Runtime) -> None:
        log.append(("start", rt.ctx.attrs.get("x")))

    task = start(
        ReconcileLatest(nu.Literal("v"), AttrRef("feed"), Body(arm), "x", **QUIET), feed=feed
    )
    await until(lambda: log == [("start", "v")])
    for key in range(3):
        feed.fire(key)
        await settle_loop()
    await asyncio.sleep(0.05)
    assert log == [("start", "v")]
    assert not task.done()
    await stop(task)
    assert feed.log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


# ---------------------------------------------------------------------------
# the id decides
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nothing", [None, NULL])
async def test_no_id_means_no_arm(nothing: object) -> None:
    feed, state, log = Feed(), {"id": nothing}, []
    task = start(_hold(state, log, **QUIET), feed=feed)
    await until(lambda: feed.log == ["bind"])
    feed.fire()
    await settle_loop()
    await asyncio.sleep(0.02)
    assert log == []
    state["id"] = "a"
    feed.fire()
    await until(lambda: ("start", "a") in log)
    state["id"] = nothing
    feed.fire()
    await until(lambda: ("end", "a") in log)
    assert not task.done()
    await stop(task)


async def test_a_new_id_is_a_death_then_a_birth() -> None:
    feed, state, log = Feed(), {"id": "a"}, []
    task = start(_hold(state, log, **QUIET), feed=feed)
    await until(lambda: ("start", "a") in log)
    state["id"] = "b"
    feed.fire()
    await until(lambda: ("start", "b") in log)
    assert log == [("start", "a"), ("end", "a"), ("start", "b")]
    await stop(task)
    assert log[-1] == ("end", "b")


async def test_the_same_id_leaves_the_arm_running() -> None:
    feed, state, log = Feed(), {"id": "a"}, []
    task = start(_hold(state, log, **QUIET), feed=feed)
    await until(lambda: ("start", "a") in log)
    for key in range(3):
        feed.fire(key)
        await settle_loop()
    await asyncio.sleep(0.02)
    assert log == [("start", "a")]
    await stop(task)


async def test_a_tuple_from_a_scalar_read_is_one_id() -> None:
    """A versioned id is a tuple, and a scalar read never takes it apart."""
    feed, state, log = Feed(), {"id": ("row", 1)}, []
    task = start(_hold(state, log, **QUIET), feed=feed)
    await until(lambda: ("start", ("row", 1)) in log)
    state["id"] = ("row", 2)
    feed.fire()
    await until(lambda: ("start", ("row", 2)) in log)
    assert log == [("start", ("row", 1)), ("end", ("row", 1)), ("start", ("row", 2))]
    await stop(task)


# ---------------------------------------------------------------------------
# a stream read: yields the id, or nothing
# ---------------------------------------------------------------------------


def _hold_stream(
    state: dict, log: list, reads: list | None = None, **schedule: object
) -> ReconcileLatest:
    """Like ``_hold``, with the id read through a stream over ``state["ids"]``."""

    async def read(rt: Runtime) -> list:
        if reads is not None:
            reads.append(list(state["ids"]))
        return list(state["ids"])

    async def arm(rt: Runtime) -> None:
        x = rt.ctx.attrs.get("x")
        log.append(("start", x))
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", x))

    return ReconcileLatest(nu.Iter(Read(read)), AttrRef("feed"), Body(arm), "x", **schedule)


async def test_a_stream_read_yields_the_id_or_nothing() -> None:
    feed, state, log, reads = Feed(), {"ids": []}, [], []
    task = start(_hold_stream(state, log, reads, **QUIET), feed=feed)
    await until(lambda: reads == [[]])
    await settle_loop()
    assert log == []
    state["ids"] = ["a"]
    feed.fire()
    await until(lambda: ("start", "a") in log)
    feed.fire()
    await until(lambda: len(reads) == 3)
    await asyncio.sleep(0.02)
    assert log == [("start", "a")]
    state["ids"] = [None]
    feed.fire()
    await until(lambda: ("end", "a") in log)
    state["ids"] = ["b"]
    feed.fire()
    await until(lambda: ("start", "b") in log)
    assert log == [("start", "a"), ("end", "a"), ("start", "b")]
    assert not task.done()
    await stop(task)
    assert log[-1] == ("end", "b")


async def test_a_stream_read_that_yields_more_than_one_id_is_a_clear_error() -> None:
    log: list = []
    feed = Feed(log)
    task = start(_hold_stream({"ids": ["a", "b"]}, log, **QUIET), feed=feed)
    with pytest.raises(ValueError, match="ReconcileLatest: read must yield one id or nothing"):
        await asyncio.wait_for(task, 5)
    assert log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_a_recheck_catches_a_dropped_change_of_id() -> None:
    feed, state, log = Feed(), {"id": "a"}, []
    task = start(_hold(state, log, after=(0.05,), every=None), feed=feed)
    await until(lambda: ("start", "a") in log)
    state["id"] = "b"
    feed.dropping = 1
    feed.fire()
    await until(lambda: ("start", "b") in log)
    assert ("end", "a") in log
    await stop(task)


async def test_a_finished_arm_stays_finished_until_the_id_leaves_and_returns() -> None:
    feed, state, log, reads = Feed(), {"id": "a"}, [], []
    task = start(_hold(state, log, {"a": "finish"}, reads, **QUIET), feed=feed)
    await until(lambda: ("end", "a") in log)
    feed.fire()
    await until(lambda: len(reads) == 2)
    await asyncio.sleep(0.02)
    assert _starts(log, "a") == 1
    state["id"] = None
    feed.fire()
    await until(lambda: reads[-1] is None)
    state["id"] = "a"
    feed.fire()
    await until(lambda: _starts(log, "a") == 2)
    assert not task.done()
    await stop(task)


# ---------------------------------------------------------------------------
# errors and exit
# ---------------------------------------------------------------------------


async def test_an_arm_error_ends_the_flow_and_closes() -> None:
    log: list = []
    feed = Feed(log)
    task = start(_hold({"id": "a"}, log, {"a": "boom"}, **QUIET), feed=feed)
    with pytest.raises(ValueError, match="boom a"):
        await asyncio.wait_for(task, 5)
    assert log == ["bind", ("start", "a"), ("end", "a"), "unbind", "close"]
    assert live_rechecks() == []


async def test_an_unhashable_id_is_a_clear_error() -> None:
    feed = Feed()
    task = start(_hold({"id": [1]}, [], **QUIET), feed=feed)
    with pytest.raises(TypeError, match=r"ReconcileLatest: ids must be hashable, got list"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]


async def test_cancel_drains_the_arm_before_closing() -> None:
    log: list = []
    feed = Feed(log)
    task = start(_hold({"id": "a"}, log, after=(5.0,), every=5.0), feed=feed)
    await until(lambda: ("start", "a") in log)
    await stop(task)
    assert log == ["bind", ("start", "a"), ("end", "a"), "unbind", "close"]
    assert live_rechecks() == []
