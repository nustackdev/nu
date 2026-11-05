"""Tests for the level wakes: the re-check schedule as child terms, re-checks and merging.

Driven through ``Reconcile``, the plainest level flow.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import QUIET, Body, Feed, live_rechecks, settle_loop, start, stop, until

import nu
from nu.context import Attr as AttrRef
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
    return after._payload["value"], every._payload["value"]


def test_schedule_defaults_and_normalisation() -> None:
    assert _schedule(Reconcile(AttrRef("feed"), nu.Noop())) == ((0.1, 0.3, 1.0), 30.0)
    wait = WaitUntil(AttrRef("feed"), nu.Literal(True), after=[1, 0.5], every=None)
    assert _schedule(wait) == ((0.5, 1.0), None)
    fold = ReconcileLatestEach(nu.Iter([1]), AttrRef("feed"), nu.Noop(), "x", every=2)
    assert _schedule(fold) == ((0.1, 0.3, 1.0), 2.0)


def test_the_schedule_is_children_not_payload() -> None:
    term = Reconcile(AttrRef("feed"), nu.Noop(), after=nu.Literal([0.2]), every=AttrRef("every"))
    assert "after" not in term._payload
    assert "every" not in term._payload
    assert _schedule(Reconcile(AttrRef("feed"), nu.Noop(), after=nu.Literal([0.2])))[0] == (0.2,)


@pytest.mark.parametrize("schedule", [{"every": 0}, {"every": -1.0}, {"after": (-0.1,)}], ids=str)
def test_a_schedule_that_cannot_run_is_refused(schedule: dict) -> None:
    with pytest.raises(ValueError, match="Reconcile"):
        Reconcile(AttrRef("feed"), nu.Noop(), **schedule)


async def test_a_computed_schedule_is_read_when_the_flow_runs() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(
        AttrRef("feed"), _passes(state, seen), after=AttrRef("after"), every=AttrRef("every")
    )
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
    term = Reconcile(AttrRef("feed"), nu.Noop(), after=AttrRef("after"), every=AttrRef("every"))
    with pytest.raises(ValueError, match=message):
        await start(term, feed=feed, **schedule)
    assert feed.log == []


# ---------------------------------------------------------------------------
# Re-checks
# ---------------------------------------------------------------------------


async def test_a_dropped_notification_is_caught_by_an_after_recheck() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(AttrRef("feed"), _passes(state, seen), after=(0.05,), every=None)
    task = start(term, feed=feed)
    await until(lambda: seen == [0])
    state["v"] = 1
    feed.dropping = 1
    feed.fire()
    await until(lambda: seen[-1] == 1)
    await stop(task)


async def test_a_dropped_notification_is_caught_by_the_standing_recheck() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    term = Reconcile(AttrRef("feed"), _passes(state, seen), after=(0.01,), every=0.05)
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
    term = Reconcile(AttrRef("feed"), _passes(state, seen), after=(0.01, 0.02), every=None)
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

    task = start(Reconcile(AttrRef("feed"), Body(fn), **QUIET), feed=feed)
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

    term = Reconcile(AttrRef("feed"), Body(fn), after=(0.01,), every=None)
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
