"""Tests for ReconcileLatestEach: one arm per element, kept live against a change."""

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
from nu.core.reactive import ReconcileLatestEach


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# ReconcileLatestEach
# ---------------------------------------------------------------------------


def _fold(elems: set, log: list, reads: list | None = None, **schedule: object) -> object:
    async def read(rt: Runtime) -> list:
        if reads is not None:
            reads.append(sorted(elems))
        return sorted(elems)

    async def arm(rt: Runtime) -> None:
        x = rt.ctx.attrs.get("x")
        log.append(("start", x))
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", x))

    return ReconcileLatestEach(Read(read), AttrRef("feed"), Body(arm), "x", **schedule)


async def test_fold_starts_arms_right_after_binding() -> None:
    feed, log = Feed(), []
    task = start(_fold({"a", "b"}, log, **QUIET), feed=feed)
    await until(lambda: len(log) == 2)
    assert feed.log == ["bind"]
    assert sorted(log) == [("start", "a"), ("start", "b")]
    await stop(task)
    assert sorted(log) == [("end", "a"), ("end", "b"), ("start", "a"), ("start", "b")]
    assert feed.log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_fold_catches_a_missed_birth_on_an_after_recheck() -> None:
    feed, elems, log = Feed(), {"a"}, []
    task = start(_fold(elems, log, after=(0.05,), every=None), feed=feed)
    await until(lambda: ("start", "a") in log)
    elems.add("b")
    feed.dropping = 1
    feed.fire()
    await until(lambda: ("start", "b") in log)
    assert ("end", "a") not in log
    await stop(task)


async def test_fold_catches_a_missed_death_on_the_standing_recheck() -> None:
    feed, elems, log, reads = Feed(), {"a", "b"}, [], []
    task = start(_fold(elems, log, reads, after=(0.01,), every=0.05), feed=feed)
    await until(lambda: len(reads) >= 2)
    elems.discard("a")
    feed.dropping = 1
    feed.fire()
    await until(lambda: ("end", "a") in log)
    assert ("end", "b") not in log
    await stop(task)


async def test_fold_merges_a_burst_during_a_pass() -> None:
    feed, log = Feed(), []
    reads: list = []
    started, gate = asyncio.Event(), asyncio.Event()

    async def read(rt: Runtime) -> list:
        reads.append(1)
        if len(reads) == 1:
            started.set()
            await gate.wait()
        return ["a"]

    async def arm(rt: Runtime) -> None:
        log.append(rt.ctx.attrs.get("x"))
        await asyncio.Event().wait()

    term = ReconcileLatestEach(Read(read), AttrRef("feed"), Body(arm), "x", **QUIET)
    task = start(term, feed=feed)
    await asyncio.wait_for(started.wait(), 5)
    for key in range(10):
        feed.fire(key)
    await settle_loop()
    gate.set()
    await until(lambda: len(reads) == 2)
    await asyncio.sleep(0.05)
    assert len(reads) == 2
    assert log == ["a"]
    await stop(task)


# ---------------------------------------------------------------------------
# the laws: empty items, rule 1 (the done set), rule 2 (errors propagate)
# ---------------------------------------------------------------------------


async def test_fold_over_nothing_runs_nothing_and_never_returns() -> None:
    feed, log, reads = Feed(), [], []
    task = start(_fold(set(), log, reads, **QUIET), feed=feed)
    await until(lambda: reads == [[]])
    feed.fire()
    await until(lambda: len(reads) == 2)
    await asyncio.sleep(0.05)
    assert log == []
    assert not task.done()
    await stop(task)
    assert feed.log == ["bind", "unbind", "close"]


def _once(
    elems: set, log: list, plan: dict, reads: list | None = None, **schedule: object
) -> ReconcileLatestEach:
    """Like ``_fold``, with arms that finish or raise as ``plan`` says."""

    async def read(rt: Runtime) -> list:
        if reads is not None:
            reads.append(sorted(elems))
        return sorted(elems)

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

    return ReconcileLatestEach(Read(read), AttrRef("feed"), Body(arm), "x", **schedule)


async def test_a_finished_arm_stays_finished_while_its_element_stays() -> None:
    feed, elems, log = Feed(), {"a", "b"}, []
    task = start(_once(elems, log, {"a": "finish"}, **QUIET), feed=feed)
    await until(lambda: ("end", "a") in log)
    for key in range(3):
        feed.fire(key)
        await settle_loop()
    await asyncio.sleep(0.02)
    assert log.count(("start", "a")) == 1
    assert ("end", "b") not in log
    await stop(task)


async def test_a_finished_arm_is_born_again_after_its_element_leaves_and_returns() -> None:
    feed, elems, log, reads = Feed(), {"a", "b"}, [], []
    task = start(_once(elems, log, {"a": "finish"}, reads, **QUIET), feed=feed)
    await until(lambda: ("end", "a") in log)
    elems.discard("a")
    feed.fire()
    await until(lambda: reads[-1] == ["b"])
    elems.add("a")
    feed.fire()
    await until(lambda: log.count(("start", "a")) == 2)
    assert log.count(("start", "b")) == 1
    assert ("end", "b") not in log
    await stop(task)


async def test_an_arm_error_drains_the_siblings_closes_and_propagates() -> None:
    log: list = []
    feed = Feed(log)
    task = start(_once({"a", "b"}, log, {"a": "boom"}, **QUIET), feed=feed)
    with pytest.raises(ValueError, match="boom a"):
        await asyncio.wait_for(task, 5)
    assert ("end", "b") in log
    assert log.index(("end", "b")) < log.index("unbind")
    assert log[-2:] == ["unbind", "close"]
    assert live_rechecks() == []


async def test_an_arm_error_while_the_flow_waits_ends_it_at_once() -> None:
    """The error cuts into the wait for a wake: no notification is needed to notice it."""
    feed, gate = Feed(), asyncio.Event()

    async def read(rt: Runtime) -> list:
        return ["a"]

    async def arm(rt: Runtime) -> None:
        await gate.wait()
        raise ValueError("late boom")

    task = start(
        ReconcileLatestEach(Read(read), AttrRef("feed"), Body(arm), "x", **QUIET), feed=feed
    )
    await until(lambda: feed.log == ["bind"])
    await settle_loop()
    gate.set()
    with pytest.raises(ValueError, match="late boom"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]


async def test_unhashable_elements_are_a_clear_error() -> None:
    feed = Feed()

    async def read(rt: Runtime) -> list:
        return [[1]]

    term = ReconcileLatestEach(Read(read), AttrRef("feed"), nu.Noop(), **QUIET)
    task = start(term, feed=feed)
    with pytest.raises(TypeError, match=r"ReconcileLatestEach: ids must be hashable, got list"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]
