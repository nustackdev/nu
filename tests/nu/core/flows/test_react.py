"""Tests for reactive control flows: React, ReactWhile, ReactForever, ReactLatest.

All four are ``Control`` flows: they drive a mutating body on change events and
yield nothing. Construction, class-hierarchy, and law-validation checks run
without a substrate (validation is structural). Execution of the first three
(subscription binding, async queue drain) is deferred to substrate integration.
``ReactLatest`` is driven end to end against a hand-fired subscription, since
its whole contract is timing: which run is cancelled, when, and what it leaves.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu.context import AttrRef, With
from nu.core.flows import ParallelAsync, Race
from nu.core.flows.react import React, ReactForever, ReactLatest, ReactWhile
from nu.domains.shape import Shape
from nu.domains.shape.refs.item import ItemRef
from nu.engine.structure import Declared
from nu.lang import Attr, Context, Control, ScalarAction
from nu.lang.helpers import arun, compile, validate
from nustd.kv import IntRef, Snapshot, Transaction, memory_navigator
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# Class hierarchy: all four are Controls (Flows), not Queries
# ---------------------------------------------------------------------------


def test_react_is_control():
    assert issubclass(React, Control)


def test_react_while_is_control():
    assert issubclass(ReactWhile, Control)


def test_react_forever_is_control():
    assert issubclass(ReactForever, Control)


def test_react_latest_is_control():
    assert issubclass(ReactLatest, Control)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_react_constructs_with_change_only():
    change = ItemRef("sub")
    r = React(change)
    assert nu.tree.children(r)  # at least one child


def test_react_constructs_with_body():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = React(change, body)
    assert len(nu.tree.children(r)) >= 2


def test_react_changed_key_requires_body():
    change = ItemRef("sub")
    key = ItemRef("k")
    with pytest.raises(ValueError, match="changed_key requires a body"):
        React(change, changed_key=key)


def test_react_while_constructs():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    assert len(nu.tree.children(r)) == 3


def test_react_while_constructs_with_changed_key():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    key = ItemRef("k")
    r = ReactWhile(change, cond, body, changed_key=key)
    assert len(nu.tree.children(r)) == 4


def test_react_forever_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    assert len(nu.tree.children(r)) == 2


def test_react_latest_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    assert len(nu.tree.children(ReactLatest(change, body))) == 2
    assert len(nu.tree.children(ReactLatest(change, body, changed_key=ItemRef("k")))) == 3


# ---------------------------------------------------------------------------
# Law validation — a Control driving a mutating body validates, and composes
# as a work branch inside a Strategy (Race). Structural; no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_validates_with_mutating_body():
    _validate(React(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_while_validates_with_mutating_body():
    _validate(ReactWhile(_Sensor.n.on_change(), _Sensor.n < 10, _Sensor.n.set(_Sensor.n + 1)))


def test_react_forever_validates_with_mutating_body():
    _validate(ReactForever(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_latest_validates_with_mutating_body():
    _validate(ReactLatest(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1), initial=True))


def test_react_latest_mirrors_react_forever_metadata():
    body = _Sensor.n.set(_Sensor.n + 1)
    latest = compile(ReactLatest(_Sensor.n.on_change(), body))
    forever = compile(ReactForever(_Sensor.n.on_change(), body))
    for attr in (Attr.PARAM_SLOTS, Attr.REQUIRES_ASYNC):
        assert latest.attr(latest.root, attr) == forever.attr(forever.root, attr)


def test_react_while_composes_in_race():
    """The reason for the refactor: a reactive branch is now WORK, so a Strategy holds it."""
    producer = _Sensor.n.set(0)
    consumer_a = ReactWhile(_Sensor.n.on_change(), _Sensor.n < 10, _Sensor.n.set(_Sensor.n + 1))
    consumer_b = ReactForever(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1))
    _validate(Race(producer, consumer_a, consumer_b))


# ---------------------------------------------------------------------------
# Sync compile raises (async-only)
# ---------------------------------------------------------------------------


def test_react_sync_thunk_raises():
    """Sync compile returns a thunk that raises at execution -- matches Race/AnyN.

    Compile itself must succeed so emit_thunks can walk the whole tree; the raise
    only fires if the sync path is actually driven (arun uses acompile).
    """
    change = ItemRef("sub")
    r = React(change)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_while_sync_thunk_raises():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_forever_sync_thunk_raises():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_latest_sync_thunk_raises():
    r = ReactLatest(ItemRef("sub"), ItemRef("body"))
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — needs asyncio subscription backing store")
async def test_react_fires_on_first_change():
    pass


@pytest.mark.skip(reason="substrate impl deferred — needs asyncio subscription backing store")
async def test_react_while_stops_when_condition_false():
    pass


# ---------------------------------------------------------------------------
# ReactLatest execution: a hand-fired subscription and a body built from a
# Python coroutine, so every test decides exactly when a change lands.
# ---------------------------------------------------------------------------


class _Feed:
    """A Subscription the test fires by hand. Records bind / unbind / close.

    Survives the deep copy a scope carry makes of attrs, so the handle the
    flow binds to is the one the test holds.
    """

    def __init__(self) -> None:
        self.receivers: list = []
        self.closed = False

    def __deepcopy__(self, memo: dict) -> _Feed:
        return self

    def bind(self, receiver: Callable) -> None:
        self.receivers.append(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.receivers.remove(receiver)

    def close(self) -> None:
        self.closed = True

    def fire(self, key: object) -> None:
        for receiver in list(self.receivers):
            receiver(key)


class _Body(ScalarAction):
    """Async-only body running ``fn(rt)``; what every ReactLatest run drives."""

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "_Body was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return await fn(rt)

        return athunk


def _start(term: object, **attrs: object) -> asyncio.Task:
    ctx = Context()
    for key, value in attrs.items():
        ctx.attrs[key] = value
    return asyncio.ensure_future(arun(term, ctx))


async def _until(check: Callable[[], bool], timeout: float = 2.0) -> None:
    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), timeout)


async def _stop(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def _latest(body: Callable, **kwargs: object) -> ReactLatest:
    return ReactLatest(AttrRef("feed"), _Body(body), changed_key="k", **kwargs)


async def test_react_latest_restarts_and_cancels_the_stale_run():
    feed, log = _Feed(), []

    async def body(rt: Runtime) -> None:
        key = rt.ctx.attrs["k"]
        log.append(("start", key))
        try:
            await asyncio.Event().wait()
        finally:
            log.append(("end", key))

    task = _start(_latest(body), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: ("start", "a") in log)
    feed.fire("b")
    await _until(lambda: ("start", "b") in log)
    # The stale run was fully unwound before the fresh one began.
    assert log == [("start", "a"), ("end", "a"), ("start", "b")]
    await _stop(task)


async def test_react_latest_collapses_a_burst_during_a_slow_unwind():
    feed, starts = _Feed(), []
    unwinding, gate = asyncio.Event(), asyncio.Event()

    async def body(rt: Runtime) -> None:
        starts.append(rt.ctx.attrs["k"])
        try:
            await asyncio.Event().wait()
        finally:
            if not unwinding.is_set():
                unwinding.set()
                await gate.wait()

    task = _start(_latest(body), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: starts == ["a"])
    feed.fire("b")
    await asyncio.wait_for(unwinding.wait(), 2)
    for key in ("c", "d", "e"):
        feed.fire(key)
    await asyncio.sleep(0.01)
    gate.set()
    await _until(lambda: len(starts) == 2)
    await asyncio.sleep(0.02)
    assert starts == ["a", "e"]
    await _stop(task)


async def test_react_latest_initial_runs_before_any_change():
    feed, seen = _Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append(rt.ctx.attrs.get("k", "unbound"))

    task = _start(_latest(body, initial=True), feed=feed)
    await _until(lambda: seen)
    assert seen == ["unbound"]
    feed.fire("a")
    await _until(lambda: len(seen) == 2)
    assert seen == ["unbound", "a"]
    await _stop(task)


async def test_react_latest_initial_sees_a_seeded_key():
    feed, seen = _Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append(rt.ctx.attrs["k"])

    task = _start(_latest(body, initial=True), feed=feed, k="default")
    await _until(lambda: seen)
    assert seen == ["default"]
    await _stop(task)


async def test_react_latest_cancel_drains_the_body_and_unbinds():
    feed, log = _Feed(), []

    async def body(rt: Runtime) -> None:
        log.append("start")
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0.01)  # a slow unwind is still waited for
            log.append("end")

    task = _start(_latest(body), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: log == ["start"])
    await _stop(task)
    assert log == ["start", "end"]
    assert feed.receivers == []
    assert feed.closed


async def test_react_latest_body_that_finishes_waits_for_the_next_change():
    feed, runs = _Feed(), []

    async def body(rt: Runtime) -> None:
        runs.append(rt.ctx.attrs["k"])

    task = _start(_latest(body), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: runs == ["a"])
    await asyncio.sleep(0.01)
    assert not task.done()
    feed.fire("b")
    await _until(lambda: runs == ["a", "b"])
    assert not task.done()
    await _stop(task)


async def test_react_latest_body_error_propagates_and_unbinds():
    feed = _Feed()

    async def body(rt: Runtime) -> None:
        if rt.ctx.attrs["k"] == "boom":
            raise ValueError("boom")
        await asyncio.Event().wait()

    task = _start(_latest(body), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("fine")
    await asyncio.sleep(0.01)
    feed.fire("boom")
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 2)
    assert feed.receivers == []
    assert feed.closed


async def test_react_latest_error_while_unwinding_propagates():
    feed = _Feed()

    async def body(rt: Runtime) -> None:
        try:
            await asyncio.Event().wait()
        finally:
            raise ValueError("unwind")

    task = _start(_latest(body), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await asyncio.sleep(0.01)
    feed.fire("b")
    with pytest.raises(ValueError, match="unwind"):
        await asyncio.wait_for(task, 2)


async def test_react_latest_gives_each_run_a_fresh_attrs_scope():
    feed, seen = _Feed(), []

    async def body(rt: Runtime) -> None:
        seen.append((rt.ctx.attrs["k"], rt.ctx.attrs.get("scratch")))
        rt.ctx.attrs["scratch"] = rt.ctx.attrs["k"]
        rt.ctx.attrs["k"] = "clobbered"
        await asyncio.Event().wait()

    task = _start(_latest(body, initial=True), feed=feed, k="seed")
    await _until(lambda: seen)
    for key in ("a", "b"):
        feed.fire(key)
        await _until(lambda key=key: seen[-1][0] == key)
    # No run sees what an earlier run bound, and the seed is never clobbered
    # for the next one, even though every run rebinds both names.
    assert seen == [("seed", None), ("a", None), ("b", None)]
    await _stop(task)


class _Store(Shape):
    n = IntRef.slot()


async def test_react_latest_restart_unwinds_nested_parallel_and_kv_boundaries():
    """A stale run holding open brackets under a fan-out leaves nothing behind.

    Run one parks three arms under ``ParallelAsync``: a Transaction with a
    write buffered, a Snapshot with a read view open, and a bare arm. The
    restart must abort the transaction (the write never lands), close the
    snapshot, and run every arm's ``finally`` before run two starts.
    """
    feed = _Feed()
    handles: dict[str, list] = {"txn": [], "snap": [], "storage": []}
    arms_done: list[str] = []
    started: list[object] = []
    key = ("react-latest", "k")

    def arm(name: str, touch: Callable) -> _Body:
        async def fn(rt: Runtime) -> None:
            touch(rt)
            try:
                await asyncio.Event().wait()
            finally:
                arms_done.append(name)

        return _Body(fn)

    def write(rt: Runtime) -> None:
        txn = rt.ctx.get(TransactionProtocol)
        txn.put(key, 1)
        handles["txn"].append(txn)
        handles["storage"].append(rt.ctx.get(Navigator).storage)

    def read(rt: Runtime) -> None:
        snap = rt.ctx.get(SnapshotProtocol)
        snap.get(key)
        handles["snap"].append(snap)

    async def mark(rt: Runtime) -> None:
        started.append(rt.ctx.attrs["k"])

    body = _Body(mark) >> ParallelAsync(
        Transaction(arm("txn", write)),
        Snapshot(arm("snap", read)),
        arm("bare", lambda rt: None),
    )
    task = _start(With(memory_navigator(), body=_latest_of(body)), feed=feed)
    await _until(lambda: feed.receivers)
    feed.fire("a")
    await _until(lambda: handles["txn"] and handles["snap"])
    txn, snap, storage = handles["txn"][0], handles["snap"][0], handles["storage"][0]
    assert txn.is_active
    assert not snap.is_closed

    feed.fire("b")
    await _until(lambda: started == ["a", "b"])
    assert sorted(arms_done) == ["bare", "snap", "txn"]
    assert txn.is_closed
    assert not txn._committed
    assert snap.is_closed
    assert txn not in storage._active_transactions
    assert snap not in storage._active_snapshots
    with storage.snapshot() as view:
        assert not view.exists(key)
    await _stop(task)


def _latest_of(body: object) -> ReactLatest:
    return ReactLatest(AttrRef("feed"), body, changed_key="k")
