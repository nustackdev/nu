"""Tests for the level wakes: the re-check schedule as child terms, re-checks and merging.

Driven through ``Reconcile``, the plainest level flow.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import (
    FEED,
    QUIET,
    Body,
    Feed,
    Src,
    live_rechecks,
    settle_loop,
    start,
    stop,
    until,
)

import nu
from nu.core.reactive import Reconcile, ReconcileLatestEach, WaitUntil


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


def _passes(state: dict, log: list) -> Body:
    """A level body that records the state it reads on each pass."""

    async def fn(rt: Runtime) -> None:
        log.append(state["v"])

    return Body(fn)


def _schedule(term: object) -> tuple:
    """The literal ``after`` and ``every`` children a level flow holds, as values."""
    *_, after, every = nu.tree.children(term)
    return after.value, every.value


def test_schedule_defaults_and_normalisation() -> None:
    assert _schedule(Reconcile(FEED, nu.Noop())) == ((), None)
    wait = WaitUntil(FEED, nu.Literal(True), after=[1, 0.5], every=None)
    assert _schedule(wait) == ((0.5, 1.0), None)
    fold = ReconcileLatestEach(nu.Iter([1]), FEED, nu.Noop(), every=2)
    assert _schedule(fold) == ((), 2.0)


def test_rechecks_are_opt_in_with_the_standard_schedule() -> None:
    term = Reconcile(FEED, nu.Noop(), after=nu.RECHECK_AFTER, every=nu.RECHECK_EVERY)
    assert _schedule(term) == ((0.1, 0.3, 1.0), 30.0)


async def test_no_rechecks_run_unless_asked() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    task = start(Reconcile(FEED, _passes(state, seen)), feed=feed)
    await until(lambda: seen == [0])
    assert live_rechecks() == []
    feed.dropping = 1
    state["v"] = 1
    feed.fire("v")
    await asyncio.sleep(0.15)
    assert seen == [0]  # the dropped notification is not caught: nothing re-checks
    await stop(task)


def test_the_schedule_is_children_not_fields() -> None:
    term = Reconcile(FEED, nu.Noop(), after=nu.Literal([0.2]), every=Src.every)
    assert "after" not in nu.tree.fields(term)
    assert "every" not in nu.tree.fields(term)
    # A term is held as given: only a plain value is normalised at build.
    after = nu.Literal([0.2])
    assert nu.tree.children(Reconcile(FEED, nu.Noop(), after=after))[-2] is after


@pytest.mark.parametrize("schedule", [{"every": 0}, {"every": -1.0}, {"after": (-0.1,)}], ids=str)
def test_a_schedule_that_cannot_run_is_refused(schedule: dict) -> None:
    with pytest.raises(ValueError, match="Reconcile"):
        Reconcile(FEED, nu.Noop(), **schedule)


async def test_a_computed_schedule_is_read_when_the_flow_runs() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(FEED, _passes(state, seen), after=Src.after, every=Src.every)
    task = start(term, feed=feed, after=(0.05,), every=None)
    await until(lambda: seen == [0])
    state["v"] = 1
    feed.dropping = 1
    feed.fire()
    await until(lambda: seen[-1] == 1)
    await stop(task)


@pytest.mark.parametrize(
    ("schedule", "message"),
    [
        ({"after": (), "every": 0}, "Reconcile: every= must be positive"),
        ({"after": (-0.1,), "every": None}, "Reconcile: after= delays must not be negative"),
    ],
    ids=["every", "after"],
)
async def test_a_computed_schedule_that_cannot_run_is_refused_when_read(
    schedule: dict, message: str
) -> None:
    feed = Feed()
    term = Reconcile(FEED, nu.Noop(), after=Src.after, every=Src.every)
    with pytest.raises(ValueError, match=message):
        await start(term, feed=feed, **schedule)
    assert feed.log == []


async def test_a_literal_schedule_that_cannot_run_is_refused_when_read() -> None:
    # A Literal is a term like any other: the flow runs it rather than peeking.
    feed = Feed()
    term = Reconcile(FEED, nu.Noop(), every=nu.Literal(0))
    with pytest.raises(ValueError, match="Reconcile: every= must be positive"):
        await start(term, feed=feed)
    assert feed.log == []


# ---------------------------------------------------------------------------
# Re-checks
# ---------------------------------------------------------------------------


async def test_a_dropped_notification_is_caught_by_an_after_recheck() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(FEED, _passes(state, seen), after=(0.05,), every=None)
    task = start(term, feed=feed)
    await until(lambda: seen == [0])
    state["v"] = 1
    feed.dropping = 1
    feed.fire()
    await until(lambda: seen[-1] == 1)
    await stop(task)


async def test_a_dropped_notification_is_caught_by_the_standing_recheck() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(FEED, _passes(state, seen), after=(0.01,), every=0.05)
    task = start(term, feed=feed)
    # The bind wake and the one ``after`` re-check: the early window is spent.
    await until(lambda: len(seen) >= 2)
    state["v"] = 1
    feed.dropping = 1
    feed.fire()
    await until(lambda: seen[-1] == 1)
    await stop(task)


async def test_rechecks_follow_the_schedule_and_stop_when_it_ends() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(FEED, _passes(state, seen), after=(0.01, 0.02), every=None)
    task = start(term, feed=feed)
    await until(lambda: len(seen) == 3)
    await until(lambda: not live_rechecks())
    await asyncio.sleep(0.05)
    assert len(seen) == 3
    await stop(task)


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


async def test_a_burst_during_a_pass_is_one_more_pass() -> None:
    feed, passes = Feed(), []
    started, gate = asyncio.Event(), asyncio.Event()

    async def fn(rt: Runtime) -> None:
        passes.append(len(passes))
        if len(passes) == 1:
            started.set()
            await gate.wait()

    task = start(Reconcile(FEED, Body(fn), **QUIET), feed=feed)
    await asyncio.wait_for(started.wait(), 5)
    for key in range(10):
        feed.fire(key)
    await settle_loop()
    gate.set()
    await until(lambda: len(passes) == 2)
    await asyncio.sleep(0.05)
    assert passes == [0, 1]
    await stop(task)


async def test_a_recheck_during_a_pass_merges_with_notifications() -> None:
    feed, passes = Feed(), []
    started, gate = asyncio.Event(), asyncio.Event()

    async def fn(rt: Runtime) -> None:
        passes.append(len(passes))
        if len(passes) == 1:
            started.set()
            await gate.wait()

    term = Reconcile(FEED, Body(fn), after=(0.01,), every=None)
    task = start(term, feed=feed)
    await asyncio.wait_for(started.wait(), 5)
    feed.fire()
    await until(lambda: not live_rechecks())
    feed.fire()
    await settle_loop()
    gate.set()
    await until(lambda: len(passes) == 2)
    await asyncio.sleep(0.05)
    assert passes == [0, 1]
    await stop(task)
