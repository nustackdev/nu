"""Tests for ReconcileWhile: a pass per wake while the condition holds, the WaitUntil law."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import QUIET, Body, Feed, Read, live_rechecks, start, stop, until

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive import ReconcileWhile, WaitUntil
from nu.domains.shape import Shape
from nu.lang import NULL, Context
from nu.lang.helpers import arun
from nustd.kv import IntRef, Snapshot, Transaction, memory_navigator


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


def _cond(state: dict, reads: list) -> Read:
    async def fn(rt: Runtime) -> object:
        reads.append(state["on"])
        return state["on"]

    return Read(fn)


def _pass(log: list) -> Body:
    async def fn(rt: Runtime) -> None:
        log.append("pass")

    return Body(fn)


# ---------------------------------------------------------------------------
# ReconcileWhile
# ---------------------------------------------------------------------------


async def test_a_falsy_first_read_returns_without_a_pass() -> None:
    log: list = []
    feed, reads = Feed(log), []
    term = ReconcileWhile(AttrRef("feed"), _cond({"on": False}, reads), _pass(log), **QUIET)
    await asyncio.wait_for(arun(term, Context(attrs={"feed": feed})), 5)
    assert reads == [False]
    assert log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_a_truthy_read_runs_one_pass_per_wake_until_a_falsy_one() -> None:
    log: list = []
    feed, state, reads = Feed(log), {"on": True}, []
    task = start(
        ReconcileWhile(AttrRef("feed"), _cond(state, reads), _pass(log), **QUIET), feed=feed
    )
    await until(lambda: log.count("pass") == 1)
    feed.fire()
    await until(lambda: log.count("pass") == 2)
    assert not task.done()
    state["on"] = False
    feed.fire()
    await asyncio.wait_for(task, 5)
    assert reads == [True, True, False]
    assert log == ["bind", "pass", "pass", "unbind", "close"]


async def test_the_absent_sentinel_counts_as_false() -> None:
    log: list = []
    feed = Feed(log)

    async def fn(rt: Runtime) -> object:
        return NULL

    term = ReconcileWhile(AttrRef("feed"), Read(fn), _pass(log), **QUIET)
    await asyncio.wait_for(arun(term, Context(attrs={"feed": feed})), 5)
    assert log == ["bind", "unbind", "close"]


async def test_a_recheck_reads_the_condition_again() -> None:
    feed, state, reads, log = Feed(), {"on": True}, [], []
    term = ReconcileWhile(
        AttrRef("feed"), _cond(state, reads), _pass(log), after=(0.05,), every=None
    )
    task = start(term, feed=feed)
    await until(lambda: reads == [True])
    state["on"] = False
    feed.dropping = 1
    feed.fire()
    await asyncio.wait_for(task, 5)
    assert reads == [True, False]
    assert log == ["pass"]
    assert live_rechecks() == []


async def test_no_changed_key_reaches_cond_or_body() -> None:
    feed, seen = Feed(), []

    async def cond(rt: Runtime) -> bool:
        seen.append(dict(rt.ctx.attrs.items()))
        return len(seen) < 3

    async def body(rt: Runtime) -> None:
        seen.append(dict(rt.ctx.attrs.items()))

    task = start(ReconcileWhile(AttrRef("feed"), Read(cond), Body(body), **QUIET), feed=feed)
    await until(lambda: len(seen) == 2)
    feed.fire("the-secret-key")
    await asyncio.wait_for(task, 5)
    assert seen == [{"feed": feed}] * 3


# ---------------------------------------------------------------------------
# the law: WaitUntil(c, x) is ReconcileWhile(c, Not(x), Noop())
# ---------------------------------------------------------------------------


async def test_wait_until_and_reconcile_while_not_agree() -> None:
    script = [False, False, True]

    async def drive(make: object) -> tuple[list, list]:
        """Run one flow over the scripted reads, firing a change after each but the last."""
        log: list = []
        feed, reads = Feed(log), []

        async def fn(rt: Runtime) -> bool:
            value = script[len(reads)]
            reads.append(value)
            return value

        task = start(make(Read(fn)), feed=feed)
        for n in range(1, len(script)):
            await until(lambda n=n: len(reads) == n)
            assert not task.done()
            feed.fire()
        await asyncio.wait_for(task, 5)
        return reads, log

    wait = await drive(lambda x: WaitUntil(AttrRef("feed"), x, **QUIET))
    loop = await drive(lambda x: ReconcileWhile(AttrRef("feed"), nu.Not(x), nu.Noop(), **QUIET))
    assert wait == loop == ([False, False, True], ["bind", "unbind", "close"])


# ---------------------------------------------------------------------------
# exit
# ---------------------------------------------------------------------------


async def test_cancel_unbinds_closes_and_leaves_no_timer() -> None:
    log: list = []
    feed = Feed(log)
    term = ReconcileWhile(AttrRef("feed"), nu.Literal(True), nu.Noop(), after=(5.0,), every=5.0)
    task = start(term, feed=feed)
    await until(lambda: live_rechecks())
    await stop(task)
    assert log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_a_body_error_ends_the_flow_and_unbinds() -> None:
    feed = Feed()

    async def fn(rt: Runtime) -> None:
        raise ValueError("boom")

    task = start(ReconcileWhile(AttrRef("feed"), nu.Literal(True), Body(fn), **QUIET), feed=feed)
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]


async def test_a_cond_error_ends_the_flow_and_unbinds() -> None:
    feed = Feed()

    async def fn(rt: Runtime) -> bool:
        raise ValueError("boom")

    task = start(ReconcileWhile(AttrRef("feed"), Read(fn), nu.Noop(), **QUIET), feed=feed)
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]


# ---------------------------------------------------------------------------
# A real in-process store
# ---------------------------------------------------------------------------


class _Stock(Shape):
    n = IntRef.slot()


async def test_reconcile_while_drives_a_real_store_to_its_exit() -> None:
    """A body that moves the state wakes the flow again, one unit per pass, until the condition fails."""
    top_up = ReconcileWhile(
        Snapshot(_Stock.n.on_change()),
        Snapshot(_Stock.n < 3),
        Transaction(_Stock.n.set(_Stock.n + 1)),
        **QUIET,
    )
    full = WaitUntil(Snapshot(_Stock.n.on_change()), Snapshot(_Stock.n == 3), **QUIET)
    body = Transaction(_Stock.n.set(0)) >> top_up >> full
    await asyncio.wait_for(nu.arun(nu.With(memory_navigator(), body=body)), 10)
