"""Tests for ReconcileEach: each wake, one pass per element, all at once, joined."""

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

from nu.context import Attr as AttrRef
from nu.core.reactive import ReconcileEach


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


def _rounds(
    elems: list,
    log: list,
    gate: asyncio.Event | None = None,
    plan: dict | None = None,
    reads: list | None = None,
    **schedule: object,
) -> ReconcileEach:
    """A fan-out whose arms log start and end, park on ``gate`` and raise as ``plan`` says."""
    plan = plan or {}

    async def read(rt: Runtime) -> list:
        if reads is not None:
            reads.append(list(elems))
        return list(elems)

    async def arm(rt: Runtime) -> None:
        x = rt.ctx.attrs.get("x")
        log.append(("start", x))
        try:
            if plan.get(x) == "boom":
                msg = f"boom {x}"
                raise ValueError(msg)
            if plan.get(x) == "park":
                await asyncio.Event().wait()
            if gate is not None:
                await gate.wait()
        finally:
            log.append(("end", x))

    return ReconcileEach(Read(read), AttrRef("feed"), Body(arm), "x", **schedule)


async def test_a_pass_runs_every_element_at_once_and_joins() -> None:
    feed, log, gate = Feed(), [], asyncio.Event()
    task = start(_rounds(["a", "b"], log, gate, **QUIET), feed=feed)
    await until(lambda: len(log) == 2)
    assert sorted(log) == [("start", "a"), ("start", "b")]
    gate.set()
    await until(lambda: log.count(("end", "a")) == 1 and log.count(("end", "b")) == 1)
    assert not task.done()
    await stop(task)
    assert feed.log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_wakes_during_a_pass_merge_into_one_more_pass() -> None:
    feed, log, gate, reads = Feed(), [], asyncio.Event(), []
    task = start(_rounds(["a", "b"], log, gate, reads=reads, **QUIET), feed=feed)
    await until(lambda: len(log) == 2)
    for key in range(10):
        feed.fire(key)
    await settle_loop()
    assert len(reads) == 1
    gate.set()
    await until(lambda: len(reads) == 2)
    await asyncio.sleep(0.05)
    assert len(reads) == 2
    assert log.count(("start", "a")) == 2
    assert log.count(("start", "b")) == 2
    await stop(task)


async def test_elements_are_read_again_each_pass() -> None:
    feed, elems, log, reads = Feed(), ["a"], [], []
    task = start(_rounds(elems, log, reads=reads, **QUIET), feed=feed)
    await until(lambda: ("end", "a") in log)
    elems[:] = ["b", "c"]
    feed.fire()
    await until(lambda: ("end", "c") in log)
    assert reads == [["a"], ["b", "c"]]
    assert log.count(("start", "a")) == 1
    await stop(task)


async def test_a_repeated_element_runs_the_body_once_per_repeat() -> None:
    feed, log = Feed(), []
    task = start(_rounds(["a", "a"], log, **QUIET), feed=feed)
    await until(lambda: log.count(("end", "a")) == 2)
    assert log.count(("start", "a")) == 2
    await stop(task)


async def test_an_empty_read_runs_nothing_and_holds() -> None:
    feed, log, reads = Feed(), [], []
    task = start(_rounds([], log, reads=reads, **QUIET), feed=feed)
    await until(lambda: reads == [[]])
    feed.fire()
    await until(lambda: len(reads) == 2)
    await asyncio.sleep(0.05)
    assert log == []
    assert not task.done()
    await stop(task)


async def test_a_recheck_runs_a_pass_when_the_notification_was_dropped() -> None:
    feed, elems, log, reads = Feed(), ["a"], [], []
    task = start(_rounds(elems, log, reads=reads, after=(0.05,), every=None), feed=feed)
    await until(lambda: ("end", "a") in log)
    elems[:] = ["b"]
    feed.dropping = 1
    feed.fire()
    await until(lambda: ("end", "b") in log)
    assert reads == [["a"], ["b"]]
    await stop(task)


async def test_an_arm_error_ends_the_flow_and_cancels_its_siblings() -> None:
    log: list = []
    feed = Feed(log)
    term = _rounds(["a", "b"], log, plan={"a": "boom", "b": "park"}, **QUIET)
    task = start(term, feed=feed)
    with pytest.raises(ValueError, match="boom a"):
        await asyncio.wait_for(task, 5)
    assert ("end", "b") in log
    assert log.index(("end", "b")) < log.index("unbind")
    assert log[-2:] == ["unbind", "close"]
    assert live_rechecks() == []


async def test_cancel_drains_the_pass_under_way() -> None:
    log: list = []
    feed = Feed(log)
    task = start(_rounds(["a", "b"], log, plan={"a": "park", "b": "park"}, **QUIET), feed=feed)
    await until(lambda: len(log) == 3)
    await stop(task)
    assert sorted(log[3:5]) == [("end", "a"), ("end", "b")]
    assert log[5:] == ["unbind", "close"]
