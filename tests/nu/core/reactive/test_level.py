"""Tests for the level flows: ReconcileReactive, WaitReactive, ForEachParReactive.

Most tests drive a hand-fired subscription that can drop notifications, and a
body built from a Python coroutine, so each test decides when a change lands,
which one is lost, and when a pass may finish. Waits are event-driven with
generous deadlines; nothing asserts a wall-clock bound. Two tests at the end
run against a real in-process store.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive import ForEachParReactive, ReconcileReactive, WaitReactive
from nu.core.reactive._wakes import Wakes
from nu.domains.shape import Shape
from nu.engine.structure import Declared
from nu.lang import Attr, Context, Control, ScalarAction, ScalarQuery
from nu.lang.helpers import arun, compile, validate
from nu.lang.sentinels import EMPTY
from nustd.kv import IntRef, Snapshot, Transaction, memory_navigator


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _Feed:
    """A Subscription the test fires by hand, able to drop notifications.

    Records bind / unbind / close in ``log``. Survives the deep copy a scope
    carry makes of attrs, so the handle the flow binds is the one the test
    holds.
    """

    def __init__(self, log: list | None = None) -> None:
        self.receivers: list = []
        self.closed = False
        self.dropping = 0
        self.log = [] if log is None else log

    def __deepcopy__(self, memo: dict) -> _Feed:
        return self

    def bind(self, receiver: Callable) -> None:
        self.log.append("bind")
        self.receivers.append(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.log.append("unbind")
        self.receivers.remove(receiver)

    def close(self) -> None:
        self.log.append("close")
        self.closed = True

    def fire(self, key: object = "k") -> None:
        if self.dropping:
            self.dropping -= 1
            return
        for receiver in list(self.receivers):
            receiver(key)


class _Body(ScalarAction):
    """Async-only body running ``fn(rt)``."""

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


class _Read(ScalarQuery):
    """Async-only read answering ``fn(rt)``: a condition or an element list."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "_Read was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return await fn(rt)

        return athunk


def _start(term: object, **attrs: object) -> asyncio.Task:
    return asyncio.ensure_future(arun(term, Context(attrs=attrs)))


async def _until(check: Callable[[], bool], timeout: float = 5.0) -> None:
    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), timeout)


async def _stop(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def _settle_loop() -> None:
    """Let deliveries scheduled with call_soon_threadsafe land."""
    for _ in range(5):
        await asyncio.sleep(0)


def _live_rechecks() -> list:
    """Re-check timers still armed on the running loop, from any ``Wakes``."""
    loop = asyncio.get_running_loop()
    return [
        h
        for h in loop._scheduled  # type: ignore[attr-defined]
        if not h.cancelled() and isinstance(getattr(h._callback, "__self__", None), Wakes)
    ]


#: No re-checks at all: only the wake after binding and real notifications.
_QUIET: dict = {"after": (), "every": None}


def _passes(state: dict, log: list) -> _Body:
    """A level body that records the state it reads on each pass."""

    async def fn(rt: Runtime) -> None:
        log.append(state["v"])

    return _Body(fn)


# ---------------------------------------------------------------------------
# Construction and laws
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def test_level_flows_are_controls() -> None:
    assert issubclass(ReconcileReactive, Control)
    assert issubclass(WaitReactive, Control)
    assert issubclass(ForEachParReactive, Control)


def test_level_flows_validate() -> None:
    validate(compile(ReconcileReactive(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1))))
    validate(compile(WaitReactive(_Sensor.n.on_change(), _Sensor.n > 3)))


def test_level_flows_are_async_only_and_declare_their_params() -> None:
    reconcile = compile(ReconcileReactive(_Sensor.n.on_change(), _Sensor.n.set(1)))
    until = compile(WaitReactive(_Sensor.n.on_change(), _Sensor.n > 3))
    assert reconcile.attr(reconcile.root, Attr.REQUIRES_ASYNC)
    assert until.attr(until.root, Attr.REQUIRES_ASYNC)
    assert reconcile.attr(reconcile.root, Attr.PARAM_SLOTS) == frozenset({0})
    assert until.attr(until.root, Attr.PARAM_SLOTS) == frozenset({0, 1})


def test_sync_thunks_raise() -> None:
    for term in (
        ReconcileReactive(AttrRef("feed"), nu.Noop()),
        WaitReactive(AttrRef("feed"), nu.Literal(True)),
        ForEachParReactive(nu.Iter([1]), AttrRef("feed"), nu.Noop()),
    ):
        with pytest.raises(RuntimeError, match="async"):
            term._compile(0, ())(None)


def test_schedule_defaults_and_normalisation() -> None:
    assert ReconcileReactive(AttrRef("feed"), nu.Noop())._payload == {
        "after": (0.1, 0.3, 1.0),
        "every": 30.0,
    }
    until = WaitReactive(AttrRef("feed"), nu.Literal(True), after=[1, 0.5], every=None)
    assert until._payload == {"after": (0.5, 1.0), "every": None}
    fold = ForEachParReactive(nu.Iter([1]), AttrRef("feed"), nu.Noop(), "x", every=2)
    assert fold._payload == {"after": (0.1, 0.3, 1.0), "every": 2.0}


@pytest.mark.parametrize("schedule", [{"every": 0}, {"every": -1.0}, {"after": (-0.1,)}], ids=str)
def test_a_schedule_that_cannot_run_is_refused(schedule: dict) -> None:
    with pytest.raises(ValueError, match="ReconcileReactive"):
        ReconcileReactive(AttrRef("feed"), nu.Noop(), **schedule)


def test_a_body_cannot_ask_for_the_changed_key() -> None:
    with pytest.raises(TypeError, match="0 values"):
        ReconcileReactive(AttrRef("feed"), lambda key: nu.print(key))
    with pytest.raises(TypeError, match="0 values"):
        WaitReactive(AttrRef("feed"), lambda key: key)


def test_a_lambda_taking_nothing_builds_the_body() -> None:
    term = WaitReactive(AttrRef("feed"), lambda: nu.Literal(True))
    assert nu.tree.equal(term, WaitReactive(AttrRef("feed"), nu.Literal(True)))


# ---------------------------------------------------------------------------
# ReconcileReactive: the wake after binding
# ---------------------------------------------------------------------------


async def test_first_pass_runs_right_after_binding() -> None:
    log: list = []
    feed = _Feed(log)

    async def fn(rt: Runtime) -> None:
        log.append("pass")

    task = _start(ReconcileReactive(AttrRef("feed"), _Body(fn), **_QUIET), feed=feed)
    await _until(lambda: "pass" in log)
    assert log == ["bind", "pass"]
    await _stop(task)


async def test_state_written_before_binding_is_seen_by_the_first_pass() -> None:
    state, seen = {"v": "written before"}, []
    task = _start(ReconcileReactive(AttrRef("feed"), _passes(state, seen), **_QUIET), feed=_Feed())
    await _until(lambda: seen)
    assert seen == ["written before"]
    await _stop(task)


async def test_every_notification_wakes_a_pass() -> None:
    feed, state, seen = _Feed(), {"v": 0}, []
    task = _start(ReconcileReactive(AttrRef("feed"), _passes(state, seen), **_QUIET), feed=feed)
    await _until(lambda: seen == [0])
    for v in (1, 2):
        state["v"] = v
        feed.fire()
        await _until(lambda v=v: seen[-1] == v)
    assert seen == [0, 1, 2]
    await _stop(task)


async def test_no_changed_key_reaches_the_body() -> None:
    feed, seen = _Feed(), []

    async def fn(rt: Runtime) -> None:
        seen.append(dict(rt.ctx.attrs.items()))

    task = _start(ReconcileReactive(AttrRef("feed"), _Body(fn), **_QUIET), feed=feed)
    await _until(lambda: len(seen) == 1)
    feed.fire("the-secret-key")
    await _until(lambda: len(seen) == 2)
    assert seen == [{"feed": feed}, {"feed": feed}]
    await _stop(task)


# ---------------------------------------------------------------------------
# ReconcileReactive: re-checks
# ---------------------------------------------------------------------------


async def test_a_dropped_notification_is_caught_by_an_after_recheck() -> None:
    feed, state, seen = _Feed(), {"v": 0}, []
    term = ReconcileReactive(AttrRef("feed"), _passes(state, seen), after=(0.05,), every=None)
    task = _start(term, feed=feed)
    await _until(lambda: seen == [0])
    state["v"] = 1
    feed.dropping = 1
    feed.fire()
    await _until(lambda: seen[-1] == 1)
    await _stop(task)


async def test_a_dropped_notification_is_caught_by_the_standing_recheck() -> None:
    feed, state, seen = _Feed(), {"v": 0}, []
    term = ReconcileReactive(AttrRef("feed"), _passes(state, seen), after=(0.01,), every=0.05)
    task = _start(term, feed=feed)
    # The bind wake and the one ``after`` re-check: the early window is spent.
    await _until(lambda: len(seen) >= 2)
    state["v"] = 1
    feed.dropping = 1
    feed.fire()
    await _until(lambda: seen[-1] == 1)
    await _stop(task)


async def test_rechecks_follow_the_schedule_and_stop_when_it_ends() -> None:
    feed, state, seen = _Feed(), {"v": 0}, []
    term = ReconcileReactive(AttrRef("feed"), _passes(state, seen), after=(0.01, 0.02), every=None)
    task = _start(term, feed=feed)
    await _until(lambda: len(seen) == 3)
    await _until(lambda: not _live_rechecks())
    await asyncio.sleep(0.05)
    assert len(seen) == 3
    await _stop(task)


# ---------------------------------------------------------------------------
# ReconcileReactive: merging
# ---------------------------------------------------------------------------


async def test_a_burst_during_a_pass_is_one_more_pass() -> None:
    feed, passes = _Feed(), []
    started, gate = asyncio.Event(), asyncio.Event()

    async def fn(rt: Runtime) -> None:
        passes.append(len(passes))
        if len(passes) == 1:
            started.set()
            await gate.wait()

    task = _start(ReconcileReactive(AttrRef("feed"), _Body(fn), **_QUIET), feed=feed)
    await asyncio.wait_for(started.wait(), 5)
    for key in range(10):
        feed.fire(key)
    await _settle_loop()
    gate.set()
    await _until(lambda: len(passes) == 2)
    await asyncio.sleep(0.05)
    assert passes == [0, 1]
    await _stop(task)


async def test_a_recheck_during_a_pass_merges_with_notifications() -> None:
    feed, passes = _Feed(), []
    started, gate = asyncio.Event(), asyncio.Event()

    async def fn(rt: Runtime) -> None:
        passes.append(len(passes))
        if len(passes) == 1:
            started.set()
            await gate.wait()

    term = ReconcileReactive(AttrRef("feed"), _Body(fn), after=(0.01,), every=None)
    task = _start(term, feed=feed)
    await asyncio.wait_for(started.wait(), 5)
    feed.fire()
    await _until(lambda: not _live_rechecks())
    feed.fire()
    await _settle_loop()
    gate.set()
    await _until(lambda: len(passes) == 2)
    await asyncio.sleep(0.05)
    assert passes == [0, 1]
    await _stop(task)


# ---------------------------------------------------------------------------
# ReconcileReactive: exit
# ---------------------------------------------------------------------------


async def test_cancel_unbinds_closes_and_leaves_no_timer_or_task() -> None:
    log: list = []
    feed = _Feed(log)
    before = asyncio.all_tasks()
    term = ReconcileReactive(
        AttrRef("feed"), _Body(lambda rt: asyncio.sleep(0)), after=(5.0,), every=5.0
    )
    task = _start(term, feed=feed)
    await _until(lambda: _live_rechecks())
    await _stop(task)
    assert log == ["bind", "unbind", "close"]
    assert feed.receivers == []
    assert _live_rechecks() == []
    assert asyncio.all_tasks() == before


async def test_a_body_error_ends_the_flow_and_unbinds() -> None:
    feed = _Feed()

    async def fn(rt: Runtime) -> None:
        raise ValueError("boom")

    task = _start(ReconcileReactive(AttrRef("feed"), _Body(fn)), feed=feed)
    with pytest.raises(ValueError, match="boom"):
        await asyncio.wait_for(task, 5)
    assert feed.log == ["bind", "unbind", "close"]
    assert _live_rechecks() == []


# ---------------------------------------------------------------------------
# WaitReactive
# ---------------------------------------------------------------------------


def _cond(state: dict, reads: list) -> _Read:
    async def fn(rt: Runtime) -> bool:
        reads.append(state["done"])
        return state["done"]

    return _Read(fn)


async def test_until_returns_at_once_when_already_true() -> None:
    feed, reads = _Feed(), []
    term = WaitReactive(AttrRef("feed"), _cond({"done": True}, reads), after=(5.0,), every=5.0)
    await asyncio.wait_for(arun(term, Context(attrs={"feed": feed})), 5)
    assert reads == [True]
    assert feed.log == ["bind", "unbind", "close"]
    assert _live_rechecks() == []


async def test_until_returns_on_the_change_that_makes_it_true() -> None:
    feed, state, reads = _Feed(), {"done": False}, []
    task = _start(WaitReactive(AttrRef("feed"), _cond(state, reads), **_QUIET), feed=feed)
    await _until(lambda: reads == [False])
    feed.fire()
    await _until(lambda: len(reads) == 2)
    assert not task.done()
    state["done"] = True
    feed.fire()
    await asyncio.wait_for(task, 5)
    assert reads == [False, False, True]
    assert feed.closed


async def test_until_returns_on_a_recheck_when_the_notification_was_dropped() -> None:
    feed, state, reads = _Feed(), {"done": False}, []
    term = WaitReactive(AttrRef("feed"), _cond(state, reads), after=(0.05,), every=None)
    task = _start(term, feed=feed)
    await _until(lambda: reads == [False])
    state["done"] = True
    feed.dropping = 1
    feed.fire()
    await asyncio.wait_for(task, 5)
    assert reads[-1] is True
    assert feed.closed


async def test_until_treats_empty_as_false() -> None:
    feed, reads = _Feed(), []

    async def fn(rt: Runtime) -> object:
        reads.append(1)
        return EMPTY if len(reads) == 1 else True

    task = _start(WaitReactive(AttrRef("feed"), _Read(fn), **_QUIET), feed=feed)
    await _until(lambda: reads == [1])
    assert not task.done()
    feed.fire()
    await asyncio.wait_for(task, 5)


# ---------------------------------------------------------------------------
# ForEachParReactive
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

    return ForEachParReactive(_Read(read), AttrRef("feed"), _Body(arm), "x", **schedule)


async def test_fold_starts_arms_right_after_binding() -> None:
    feed, log = _Feed(), []
    task = _start(_fold({"a", "b"}, log, **_QUIET), feed=feed)
    await _until(lambda: len(log) == 2)
    assert feed.log == ["bind"]
    assert sorted(log) == [("start", "a"), ("start", "b")]
    await _stop(task)
    assert sorted(log) == [("end", "a"), ("end", "b"), ("start", "a"), ("start", "b")]
    assert feed.log == ["bind", "unbind", "close"]
    assert _live_rechecks() == []


async def test_fold_catches_a_missed_birth_on_an_after_recheck() -> None:
    feed, elems, log = _Feed(), {"a"}, []
    task = _start(_fold(elems, log, after=(0.05,), every=None), feed=feed)
    await _until(lambda: ("start", "a") in log)
    elems.add("b")
    feed.dropping = 1
    feed.fire()
    await _until(lambda: ("start", "b") in log)
    assert ("end", "a") not in log
    await _stop(task)


async def test_fold_catches_a_missed_death_on_the_standing_recheck() -> None:
    feed, elems, log, reads = _Feed(), {"a", "b"}, [], []
    task = _start(_fold(elems, log, reads, after=(0.01,), every=0.05), feed=feed)
    await _until(lambda: len(reads) >= 2)
    elems.discard("a")
    feed.dropping = 1
    feed.fire()
    await _until(lambda: ("end", "a") in log)
    assert ("end", "b") not in log
    await _stop(task)


async def test_fold_merges_a_burst_during_a_pass() -> None:
    feed, log = _Feed(), []
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

    term = ForEachParReactive(_Read(read), AttrRef("feed"), _Body(arm), "x", **_QUIET)
    task = _start(term, feed=feed)
    await asyncio.wait_for(started.wait(), 5)
    for key in range(10):
        feed.fire(key)
    await _settle_loop()
    gate.set()
    await _until(lambda: len(reads) == 2)
    await asyncio.sleep(0.05)
    assert len(reads) == 2
    assert log == ["a"]
    await _stop(task)


# ---------------------------------------------------------------------------
# A real in-process store
# ---------------------------------------------------------------------------


class _Cart(Shape):
    qty = IntRef.slot()
    total = IntRef.slot()


def _wait_for_total(n: int) -> WaitReactive:
    return WaitReactive(Snapshot(_Cart.total.on_change()), Snapshot(_Cart.total == n), **_QUIET)


def _wait_for_qty(n: int) -> WaitReactive:
    return WaitReactive(Snapshot(_Cart.qty.on_change()), Snapshot(_Cart.qty >= n), **_QUIET)


async def _arun_with_store(body: object) -> None:
    await asyncio.wait_for(nu.arun(nu.With(memory_navigator(), body=body)), 10)


async def test_reconcile_keeps_a_real_store_in_step() -> None:
    """A write made before the flow starts is seen, and a later one is followed.

    Re-checks are off, so only the wake after binding and real notifications
    can drive it; a wait that never ends fails on the deadline.
    """
    keeper = ReconcileReactive(
        Snapshot(_Cart.qty.on_change()),
        Transaction(_Cart.total.set(_Cart.qty * 10)),
        **_QUIET,
    )
    follow = _wait_for_total(20) >> Transaction(_Cart.qty.set(3)) >> _wait_for_total(30)
    await _arun_with_store(
        Transaction(_Cart.qty.set(2) >> _Cart.total.set(0)) >> nu.Race(keeper, follow)
    )


async def test_reconcile_until_on_a_real_store() -> None:
    """A write that makes the condition true ends the wait; already true returns at once."""
    writes = nu.ForRangeDo(1, 4, lambda i: nu.Delay(0.01) >> Transaction(_Cart.qty.set(i)))
    await _arun_with_store(
        Transaction(_Cart.qty.set(0))
        >> nu.Race(_wait_for_qty(3), writes >> nu.ForeverDo(nu.Delay(1.0)))
        >> _wait_for_qty(3)
    )
