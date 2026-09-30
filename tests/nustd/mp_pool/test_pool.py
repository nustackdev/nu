"""Resource-level tests for ``nustd.mp_pool.WorkerPool``. Real processes, no mocks."""

from __future__ import annotations

import asyncio
import os
import time

import pytest
from _support.pool_workers import RESIDENT, Marker

import nu
from nustd.mp_pool import UnknownWorker, WorkerGone, WorkerPool


pytestmark = pytest.mark.slow


# --- helpers ----------------------------------------------------------------


def _pid_of(pool: WorkerPool, wid: int) -> int:
    return pool._workers[wid].proc.pid


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _wait_gone(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def pool():
    p = WorkerPool(name="nu-test")
    p.setup(None)
    try:
        yield p
    finally:
        p.cleanup()


# --- launch -----------------------------------------------------------------


def test_launch_returns_usable_ids(pool):
    a = pool.launch()
    b = pool.launch()
    assert a != b
    assert pool.workers() == [a, b]
    assert pool.alive(a) and pool.alive(b)
    assert pool.teleport(a, nu.Add(1, 2)) == 3
    assert pool.teleport(b, nu.Add(10, 20)) == 30


def test_ids_are_monotonic_and_never_reused(pool):
    first = pool.launch()
    pool.kill(first)
    second = pool.launch()
    third = pool.launch()
    assert second > first
    assert third > second
    assert first not in pool.workers()
    assert pool.alive(first) is False


def test_launch_ships_the_init_bracket(pool):
    plain = pool.launch()
    marked = pool.launch(nu.Provide(Marker, {"label": "hi"}))
    assert pool.teleport(plain, nu.FabricRef(Marker).exists()) is False
    assert pool.teleport(marked, nu.FabricRef(Marker).exists()) is True


def test_pool_default_init_applies_to_every_worker():
    p = WorkerPool(name="nu-test-init", init=nu.Provide(Marker, {"label": "pool"}))
    p.setup(None)
    try:
        w = p.launch()
        assert p.teleport(w, nu.FabricRef(Marker).exists()) is True
    finally:
        p.cleanup()


# --- dispatch ---------------------------------------------------------------


def test_dispatch_returns_promptly(pool):
    w = pool.launch()

    start = time.monotonic()
    pool.dispatch(w, RESIDENT)
    elapsed = time.monotonic() - start

    # The body never terminates; if Dispatch awaited it this would hang.
    assert elapsed < 1.0
    assert pool.running(w) is True


def test_teleport_still_answers_while_a_resident_body_runs(pool):
    w = pool.launch()
    pool.dispatch(w, RESIDENT)
    assert pool.teleport(w, nu.Add(2, 2)) == 4


def test_teleport_reraises_the_child_error(pool):
    w = pool.launch()
    with pytest.raises(ZeroDivisionError):
        pool.teleport(w, nu.Div(1, 0))


# --- kill -------------------------------------------------------------------


def test_kill_terminates_a_worker_running_a_resident_body_and_is_prompt(pool):
    w = pool.launch()
    pid = _pid_of(pool, w)
    pool.dispatch(w, RESIDENT)

    start = time.monotonic()
    pool.kill(w)
    elapsed = time.monotonic() - start

    # A cooperative stop sentinel would never be read by a busy worker, so the
    # join would time out; nustd.mp pays 5s here.
    assert elapsed < 1.0
    assert pool.alive(w) is False
    assert _wait_gone(pid)


def test_kill_is_idempotent(pool):
    w = pool.launch()
    pool.kill(w)
    pool.kill(w)
    pool.kill(w)
    pool.kill(9999)
    assert pool.workers() == []


def test_calls_on_a_killed_id_raise_rather_than_hang(pool):
    w = pool.launch()
    pool.kill(w)
    with pytest.raises(UnknownWorker):
        pool.teleport(w, nu.Add(1, 1))


def test_teleport_in_flight_fails_when_the_worker_is_killed(pool):
    w = pool.launch()
    result: list[object] = []

    def call() -> None:
        try:
            result.append(pool.teleport(w, nu.DelayedDo(30, nu.Noop())))
        except BaseException as exc:
            result.append(exc)

    import threading

    t = threading.Thread(target=call, daemon=True)
    t.start()
    time.sleep(0.2)
    pool.kill(w)
    t.join(timeout=5)
    assert not t.is_alive()
    assert isinstance(result[0], WorkerGone)


# --- teardown ---------------------------------------------------------------


def test_cleanup_reaps_every_worker():
    p = WorkerPool(name="nu-test-teardown")
    p.setup(None)
    ids = [p.launch() for _ in range(3)]
    pids = [_pid_of(p, w) for w in ids]
    p.dispatch(ids[0], RESIDENT)

    start = time.monotonic()
    p.cleanup()
    assert time.monotonic() - start < 3.0
    assert p.workers() == []
    for pid in pids:
        assert _wait_gone(pid)


async def test_acleanup_reaps_under_cancellation():
    """The measured ``nustd.mp`` bug, which this pool must not have.

    ``MpWorker.acleanup`` is ``asyncio.to_thread(self.cleanup)``: when the
    enclosing task is cancelled the await raises immediately and the cleanup
    thread is abandoned, so the tree completes with the child still alive.
    ``WorkerPool.acleanup`` does its work inline with no await points, so a
    cancellation cannot land inside it.
    """
    bracket = nu.Provide(WorkerPool, {"name": "nu-test-cancel"})
    pids: list[int] = []
    entered = asyncio.Event()

    async def body() -> None:
        ctx = nu.Context()
        async with bracket._aopen(ctx):
            pool = ctx.fabrics.get(WorkerPool)
            w = await pool.alaunch()
            pids.append(_pid_of(pool, w))
            await pool.adispatch(w, RESIDENT)
            entered.set()
            await asyncio.sleep(60)

    task = asyncio.create_task(body())
    await asyncio.wait_for(entered.wait(), timeout=30)
    assert _pid_alive(pids[0])

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # The await above returned, so teardown has already finished. No polling
    # grace here on purpose: that is exactly the assertion.
    assert not _pid_alive(pids[0])


async def test_async_lifecycle_round_trip():
    bracket = nu.Provide(WorkerPool, {"name": "nu-test-async"})
    ctx = nu.Context()
    async with bracket._aopen(ctx):
        pool = ctx.fabrics.get(WorkerPool)
        w = await pool.alaunch()
        assert await pool.ateleport(w, nu.Add(2, 3)) == 5
        await pool.akill(w)
        assert pool.alive(w) is False


# --- reads ------------------------------------------------------------------


def test_running_is_false_before_and_after_a_dispatch(pool):
    w = pool.launch()
    assert pool.running(w) is False
    pool.dispatch(w, nu.DelayedDo(0.3, nu.Noop()))
    assert pool.running(w) is True
    deadline = time.monotonic() + 10
    while pool.running(w) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert pool.running(w) is False


def test_workers_tracks_launches_and_kills(pool):
    assert pool.workers() == []
    a = pool.launch()
    b = pool.launch()
    assert pool.workers() == [a, b]
    pool.kill(a)
    assert pool.workers() == [b]


# --- cancel -----------------------------------------------------------------


def _poll(check, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.01)
    return False


async def test_cancelling_ateleport_cancels_the_remote_body():
    bracket = nu.Provide(WorkerPool, {"name": "nu-test-cancel-exec"})
    ctx = nu.Context()
    async with bracket._aopen(ctx):
        pool = ctx.fabrics.get(WorkerPool)
        w = await pool.alaunch()

        call = asyncio.create_task(pool.ateleport(w, RESIDENT))
        await asyncio.sleep(0.2)
        call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await call

        # The worker still serves, and nothing is left on the books.
        assert await pool.ateleport(w, nu.Add(2, 2)) == 4
        assert pool._workers[w]._pending == {}


async def test_cancelling_one_exec_leaves_its_siblings_alone():
    bracket = nu.Provide(WorkerPool, {"name": "nu-test-cancel-one"})
    ctx = nu.Context()
    async with bracket._aopen(ctx):
        pool = ctx.fabrics.get(WorkerPool)
        w = await pool.alaunch()
        slow = [
            asyncio.create_task(pool.ateleport(w, nu.DelayedDo(0.3, nu.Noop()))) for _ in range(3)
        ]
        doomed = asyncio.create_task(pool.ateleport(w, nu.DelayedDo(30, nu.Noop())))
        await asyncio.sleep(0.1)
        doomed.cancel()
        await asyncio.gather(*slow)
        assert doomed.cancelled()
        assert all(task.done() and not task.cancelled() for task in slow)


def test_cancel_ends_a_dispatched_body(pool):
    w = pool.launch()
    token = pool.dispatch(w, RESIDENT)
    assert pool.running(w) is True

    pool.cancel(w, token)
    # The child says cancelled, which closes the token like done.
    assert _poll(lambda: pool.running(w) is False)
    assert pool.teleport(w, nu.Add(1, 2)) == 3


def test_cancel_is_a_no_op_once_finished(pool):
    w = pool.launch()
    token = pool.dispatch(w, nu.Add(1, 1))
    assert _poll(lambda: pool.running(w) is False)
    pool.cancel(w, token)
    pool.cancel(w, 12345)
    pool.cancel(9999, token)
    assert pool.teleport(w, nu.Add(1, 2)) == 3


async def test_worker_death_raises_on_a_pending_ateleport():
    bracket = nu.Provide(WorkerPool, {"name": "nu-test-death"})
    ctx = nu.Context()
    async with bracket._aopen(ctx):
        pool = ctx.fabrics.get(WorkerPool)
        w = await pool.alaunch()
        call = asyncio.create_task(pool.ateleport(w, nu.DelayedDo(30, nu.Add(1, 1))))
        await asyncio.sleep(0.2)
        # Died by itself: not a pool kill, so the pool learns it from the pipe.
        os.kill(_pid_of(pool, w), 9)
        with pytest.raises(WorkerGone):
            await asyncio.wait_for(call, timeout=10)
        assert await pool.await_exit(w) == -9
