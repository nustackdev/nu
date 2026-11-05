"""Tests for Reconcile: the wake after binding, notifications, exit, and a real store."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import QUIET, Body, Feed, live_rechecks, start, stop, until

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive import Reconcile, WaitUntil
from nu.domains.shape import Shape
from nustd.kv import IntRef, Snapshot, Transaction, memory_navigator


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


def _passes(state: dict, log: list) -> Body:
    """A level body that records the state it reads on each pass."""

    async def fn(rt: Runtime) -> None:
        log.append(state["v"])

    return Body(fn)


# ---------------------------------------------------------------------------
# Reconcile: the wake after binding
# ---------------------------------------------------------------------------


async def test_first_pass_runs_right_after_binding() -> None:
    log: list = []
    feed = Feed(log)

    async def fn(rt: Runtime) -> None:
        log.append("pass")

    task = start(Reconcile(AttrRef("feed"), Body(fn), **QUIET), feed=feed)
    await until(lambda: "pass" in log)
    assert log == ["bind", "pass"]
    await stop(task)


async def test_state_written_before_binding_is_seen_by_the_first_pass() -> None:
    state, seen = {"v": "written before"}, []
    task = start(Reconcile(AttrRef("feed"), _passes(state, seen), **QUIET), feed=Feed())
    await until(lambda: seen)
    assert seen == ["written before"]
    await stop(task)


async def test_every_notification_wakes_a_pass() -> None:
    feed, state, seen = Feed(), {"v": 0}, []
    task = start(Reconcile(AttrRef("feed"), _passes(state, seen), **QUIET), feed=feed)
    await until(lambda: seen == [0])
    for v in (1, 2):
        state["v"] = v
        feed.fire()
        await until(lambda v=v: seen[-1] == v)
    assert seen == [0, 1, 2]
    await stop(task)


async def test_no_changed_key_reaches_the_body() -> None:
    feed, seen = Feed(), []

    async def fn(rt: Runtime) -> None:
        seen.append(dict(rt.ctx.attrs.items()))

    task = start(Reconcile(AttrRef("feed"), Body(fn), **QUIET), feed=feed)
    await until(lambda: len(seen) == 1)
    feed.fire("the-secret-key")
    await until(lambda: len(seen) == 2)
    assert seen == [{"feed": feed}, {"feed": feed}]
    await stop(task)


# ---------------------------------------------------------------------------
# Reconcile: exit
# ---------------------------------------------------------------------------


async def test_cancel_unbinds_closes_and_leaves_no_timer_or_task() -> None:
    log: list = []
    feed = Feed(log)
    before = asyncio.all_tasks()
    term = Reconcile(AttrRef("feed"), Body(lambda rt: asyncio.sleep(0)), after=(5.0,), every=5.0)
    task = start(term, feed=feed)
    await until(lambda: live_rechecks())
    await stop(task)
    assert log == ["bind", "unbind", "close"]
    assert feed.receivers == []
    assert live_rechecks() == []
    assert asyncio.all_tasks() == before


async def test_a_body_error_ends_the_flow_and_unbinds() -> None:
    feed = Feed()

    async def fn(rt: Runtime) -> None:
        raise ValueError("boom")

    task = start(Reconcile(AttrRef("feed"), Body(fn)), feed=feed)
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


# ---------------------------------------------------------------------------
# A real in-process store
# ---------------------------------------------------------------------------


class _Cart(Shape):
    qty = IntRef.slot()
    total = IntRef.slot()


def _wait_for_total(n: int) -> WaitUntil:
    return WaitUntil(Snapshot(_Cart.total.on_change()), Snapshot(_Cart.total == n), **QUIET)


async def _arun_with_store(body: object) -> None:
    await asyncio.wait_for(nu.arun(nu.With(memory_navigator(), body=body)), 10)


async def test_reconcile_keeps_a_real_store_in_step() -> None:
    """A write made before the flow starts is seen, and a later one is followed.

    Re-checks are off, so only the wake after binding and real notifications
    can drive it; a wait that never ends fails on the deadline.
    """
    keeper = Reconcile(
        Snapshot(_Cart.qty.on_change()),
        Transaction(_Cart.total.set(_Cart.qty * 10)),
        **QUIET,
    )
    follow = _wait_for_total(20) >> Transaction(_Cart.qty.set(3)) >> _wait_for_total(30)
    await _arun_with_store(
        Transaction(_Cart.qty.set(2) >> _Cart.total.set(0)) >> nu.Race(keeper, follow)
    )
