"""Tests for ReactLatest, driven end to end against a hand-fired subscription.

Its whole contract is timing: which run is cancelled, when, and what it leaves.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import Body, Feed, start, stop, until

import nu
from nu.context import Attr as AttrRef
from nu.context import With
from nu.core.flows import ParallelAsync
from nu.core.reactive.event import ReactEvery, ReactLatest
from nu.domains.shape import Shape
from nu.domains.shape.item import ItemRef
from nu.lang import Attr, Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef, Snapshot, Transaction, memory_navigator
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


def test_react_latest_is_control():
    assert issubclass(ReactLatest, Control)


def test_react_latest_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    assert len(nu.tree.children(ReactLatest(change, body))) == 2
    assert len(nu.tree.children(ReactLatest(change, body, changed_key=ItemRef("k")))) == 3


# ---------------------------------------------------------------------------
# Law validation: a Control driving a mutating body validates.
# Structural; no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_latest_validates_with_mutating_body():
    _validate(ReactLatest(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1), initial=True))


def test_react_latest_mirrors_react_every_metadata():
    body = _Sensor.n.set(_Sensor.n + 1)
    latest = compile(ReactLatest(_Sensor.n.on_change(), body))
    forever = compile(ReactEvery(_Sensor.n.on_change(), body))
    for attr in (Attr.PARAM_SLOTS, Attr.REQUIRES_ASYNC):
        assert latest.attr(latest.root, attr) == forever.attr(forever.root, attr)


def test_react_latest_sync_thunk_raises():
    r = ReactLatest(ItemRef("sub"), ItemRef("body"))
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def _latest(body: Callable, **kwargs: object) -> ReactLatest:
    return ReactLatest(AttrRef("feed"), Body(body), changed_key="k", **kwargs)


async def test_react_latest_restarts_and_cancels_the_stale_run():
    feed, log = Feed(), []

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs.get("k")
        log.append(("start", key))
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", key))

    task = start(_latest(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: ("start", "a") in log)
    feed.fire("b")
    await until(lambda: ("start", "b") in log)
    # The stale run was fully unwound before the fresh one began.
    assert log == [("start", "a"), ("end", "a"), ("start", "b")]
    await stop(task)


async def test_react_latest_collapses_a_burst_during_a_slow_unwind():
    feed, starts = Feed(), []
    unwinding, gate = asyncio.Event(), asyncio.Event()

    async def body(rt: Runtime) -> None:
        starts.append(rt.ctx.attrs.get("k"))
        try:
            await asyncio.Event().wait()
        finally:
            if not unwinding.is_set():
                unwinding.set()
                await gate.wait()

    task = start(_latest(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: starts == ["a"])
    feed.fire("b")
    await asyncio.wait_for(unwinding.wait(), 2)
    for key in ("c", "d", "e"):
        feed.fire(key)
    await asyncio.sleep(0.01)
    gate.set()
    await until(lambda: len(starts) == 2)
    await asyncio.sleep(0.02)
    assert starts == ["a", "e"]
    await stop(task)


async def test_react_latest_initial_runs_before_any_change():
    feed, seen = Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append(rt.ctx.attrs.get("k", "unbound"))

    task = start(_latest(body, initial=True), feed=feed)
    await until(lambda: seen)
    assert seen == ["unbound"]
    feed.fire("a")
    await until(lambda: len(seen) == 2)
    assert seen == ["unbound", "a"]
    await stop(task)


async def test_react_latest_initial_sees_a_seeded_key():
    feed, seen = Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append(rt.ctx.attrs.get("k"))

    task = start(_latest(body, initial=True), feed=feed, k="default")
    await until(lambda: seen)
    assert seen == ["default"]
    await stop(task)


async def test_react_latest_cancel_drains_the_body_and_unbinds():
    feed, log = Feed(), []

    async def body(rt: Runtime) -> None:
        log.append("start")
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0.01)  # a slow unwind is still waited for
            log.append("end")

    task = start(_latest(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: log == ["start"])
    await stop(task)
    assert log == ["start", "end"]
    assert feed.receivers == []
    assert feed.closed


async def test_react_latest_body_that_finishes_waits_for_the_next_change():
    feed, runs = Feed(), []

    async def body(rt: Runtime) -> None:
        runs.append(rt.ctx.attrs.get("k"))

    task = start(_latest(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: runs == ["a"])
    await asyncio.sleep(0.01)
    assert not task.done()
    feed.fire("b")
    await until(lambda: runs == ["a", "b"])
    assert not task.done()
    await stop(task)


async def test_react_latest_body_error_propagates_and_unbinds():
    feed = Feed()

    async def body(rt: Runtime) -> None:
        if rt.ctx.attrs.get("k") == "boom":
            raise ValueError("boom")
        await asyncio.Event().wait()

    task = start(_latest(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("fine")
    await asyncio.sleep(0.01)
    feed.fire("boom")
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 2)
    assert feed.receivers == []
    assert feed.closed


async def test_react_latest_error_while_unwinding_propagates():
    feed = Feed()

    async def body(rt: Runtime) -> None:
        try:
            await asyncio.Event().wait()
        finally:
            raise ValueError("unwind")

    task = start(_latest(body), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await asyncio.sleep(0.01)
    feed.fire("b")
    with pytest.raises(ValueError, match="unwind"):
        await asyncio.wait_for(task, 2)


async def test_react_latest_gives_each_run_a_fresh_attrs_scope():
    feed, seen = Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append((rt.ctx.attrs.get("k"), rt.ctx.attrs.get("scratch")))
        rt.ctx.attrs.set("scratch", rt.ctx.attrs.get("k"))
        rt.ctx.attrs.set("k", "clobbered")
        await asyncio.Event().wait()

    task = start(_latest(body, initial=True), feed=feed, k="seed", scratch=None)
    await until(lambda: seen)
    for key in ("a", "b"):
        feed.fire(key)
        await until(lambda key=key: seen[-1][0] == key)
    # No run sees what an earlier run bound, and the seed is never clobbered
    # for the next one, even though every run rebinds both names.
    assert seen == [("seed", None), ("a", None), ("b", None)]
    await stop(task)


async def test_react_latest_restart_unwinds_nested_parallel_and_kv_boundaries():
    """A stale run holding open brackets under a fan-out leaves nothing behind.

    Run one parks three arms under ``ParallelAsync``: a Transaction with a
    write buffered, a Snapshot with a read view open, and a bare arm. The
    restart must abort the transaction (the write never lands), close the
    snapshot, and run every arm's ``finally`` before run two starts.
    """
    feed = Feed()
    handles: dict[str, list] = {"txn": [], "snap": [], "storage": []}
    arms_done: list[str] = []
    started: list[object] = []
    key = ("react-latest", "k")

    def arm(name: str, touch: Callable) -> Body:
        async def fn(rt: Runtime) -> None:
            touch(rt)
            try:
                await asyncio.Event().wait()
            finally:
                arms_done.append(name)

        return Body(fn)

    def write(rt: Runtime) -> None:
        txn = rt.ctx.fabrics.get(TransactionProtocol)
        txn.put(key, 1)
        handles["txn"].append(txn)
        handles["storage"].append(rt.ctx.fabrics.get(Navigator).storage)

    def read(rt: Runtime) -> None:
        snap = rt.ctx.fabrics.get(SnapshotProtocol)
        snap.get(key)
        handles["snap"].append(snap)

    async def mark(rt: Runtime) -> None:
        started.append(rt.ctx.attrs.get("k"))

    body = Body(mark) >> ParallelAsync(
        Transaction(arm("txn", write)),
        Snapshot(arm("snap", read)),
        arm("bare", lambda rt: None),
    )
    task = start(With(memory_navigator(), body=_latest_of(body)), feed=feed)
    await until(lambda: feed.receivers)
    feed.fire("a")
    await until(lambda: handles["txn"] and handles["snap"])
    txn, snap, storage = handles["txn"][0], handles["snap"][0], handles["storage"][0]
    assert txn.is_active
    assert not snap.is_closed

    feed.fire("b")
    await until(lambda: started == ["a", "b"])
    assert sorted(arms_done) == ["bare", "snap", "txn"]
    assert txn.is_closed
    assert not txn._committed
    assert snap.is_closed
    assert txn not in storage._active_transactions
    assert snap not in storage._active_snapshots
    with storage.snapshot() as view:
        assert not view.exists(key)
    await stop(task)


def _latest_of(body: object) -> ReactLatest:
    return ReactLatest(AttrRef("feed"), body, changed_key="k")
