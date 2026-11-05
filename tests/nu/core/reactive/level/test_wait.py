"""Tests for WaitUntil: return on the first truthy read."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from _support.reactive import QUIET, Feed, Read, live_rechecks, start, until

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive import WaitUntil
from nu.domains.shape import Shape
from nu.lang import NULL, Context
from nu.lang.helpers import arun
from nustd.kv import IntRef, Snapshot, Transaction, memory_navigator


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# WaitUntil
# ---------------------------------------------------------------------------


def _cond(state: dict, reads: list) -> Read:
    async def fn(rt: Runtime) -> bool:
        reads.append(state["done"])
        return state["done"]

    return Read(fn)


async def test_until_returns_at_once_when_already_true() -> None:
    feed, reads = Feed(), []
    term = WaitUntil(AttrRef("feed"), _cond({"done": True}, reads), after=(5.0,), every=5.0)
    await asyncio.wait_for(arun(term, Context(attrs={"feed": feed})), 5)
    assert reads == [True]
    assert feed.log == ["bind", "unbind", "close"]
    assert live_rechecks() == []


async def test_until_returns_on_the_change_that_makes_it_true() -> None:
    feed, state, reads = Feed(), {"done": False}, []
    task = start(WaitUntil(AttrRef("feed"), _cond(state, reads), **QUIET), feed=feed)
    await until(lambda: reads == [False])
    feed.fire()
    await until(lambda: len(reads) == 2)
    assert not task.done()
    state["done"] = True
    feed.fire()
    await asyncio.wait_for(task, 5)
    assert reads == [False, False, True]
    assert feed.closed


async def test_until_returns_on_a_recheck_when_the_notification_was_dropped() -> None:
    feed, state, reads = Feed(), {"done": False}, []
    term = WaitUntil(AttrRef("feed"), _cond(state, reads), after=(0.05,), every=None)
    task = start(term, feed=feed)
    await until(lambda: reads == [False])
    state["done"] = True
    feed.dropping = 1
    feed.fire()
    await asyncio.wait_for(task, 5)
    assert reads[-1] is True
    assert feed.closed


async def test_until_treats_empty_as_false() -> None:
    feed, reads = Feed(), []

    async def fn(rt: Runtime) -> object:
        reads.append(1)
        return NULL if len(reads) == 1 else True

    task = start(WaitUntil(AttrRef("feed"), Read(fn), **QUIET), feed=feed)
    await until(lambda: reads == [1])
    assert not task.done()
    feed.fire()
    await asyncio.wait_for(task, 5)


# ---------------------------------------------------------------------------
# A real in-process store
# ---------------------------------------------------------------------------


class _Cart(Shape):
    qty = IntRef.slot()
    total = IntRef.slot()


def _wait_for_qty(n: int) -> WaitUntil:
    return WaitUntil(Snapshot(_Cart.qty.on_change()), Snapshot(_Cart.qty >= n), **QUIET)


async def _arun_with_store(body: object) -> None:
    await asyncio.wait_for(nu.arun(nu.With(memory_navigator(), body=body)), 10)


async def test_reconcile_until_on_a_real_store() -> None:
    """A write that makes the condition true ends the wait; already true returns at once."""
    writes = nu.ForRangeDo(1, 4, lambda i: nu.Delay(0.01) >> Transaction(_Cart.qty.set(i)))
    await _arun_with_store(
        Transaction(_Cart.qty.set(0))
        >> nu.Race(_wait_for_qty(3), writes >> nu.ForeverDo(nu.Delay(1.0)))
        >> _wait_for_qty(3)
    )
