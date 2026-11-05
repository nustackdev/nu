"""``Wait`` and the ``spares=`` knob. Real processes, no mocks, spawns kept few."""

from __future__ import annotations

import asyncio
import os
import signal
import time

import pytest
from _support.pool_workers import HoldAfterHangup

import nu
from nustd.mp_pool import (
    Kill,
    Launch,
    PoolRef,
    Status,
    UnknownWorker,
    Wait,
    WorkerGone,
    WorkerPool,
    WorkerStatus,
)
from nustd.mp_pool import (
    pool as pool_preset,
)


pytestmark = pytest.mark.slow


class Local(nu.Shape):
    """The worker a tree launched, held for the rest of the tree."""

    w = nu.mem.IntRef.slot()


@pytest.fixture
def pool():
    p = WorkerPool(name="nu-test-wait")
    p.setup(None)
    try:
        yield p
    finally:
        p.cleanup()


@pytest.fixture
def ctx(pool):
    return nu.Context().bind(WorkerPool, pool)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


async def _until(fn, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        await asyncio.sleep(0.01)
    return False


def _sync_until(fn, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        time.sleep(0.01)
    return False


# --- Wait -------------------------------------------------------------------


async def test_wait_on_a_killed_worker_returns_its_record_at_once(ctx, pool):
    wid = pool.launch()
    pool.kill(wid)
    value, _ = await asyncio.wait_for(nu.arun(Wait(worker=nu.Literal(wid)), ctx), 1.0)
    assert isinstance(value, WorkerStatus)
    assert (value.state, value.exitcode, value.cause) == ("exited", -9, "killed")
    # The sync path answers the same, without blocking.
    assert nu.run(PoolRef().wait(nu.Literal(wid)), ctx)[0] == value


async def test_wait_on_an_unknown_id_raises(ctx, pool):
    with pytest.raises(UnknownWorker):
        await nu.arun(Wait(worker=nu.Literal(999)), ctx)
    with pytest.raises(UnknownWorker):
        pool.wait(999)


async def test_wait_completes_when_another_branch_kills_the_worker(ctx, pool):
    wid = pool.launch()
    statuses: list = []

    # Each Gather arm runs on its own branch, so the waiting arm reports
    # through a host-side list rather than a name the parent would not see.
    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    def keep(status: object) -> None:
        statuses.append(status)

    tree = nu.Gather(
        keep(Wait(worker=nu.Literal(wid))),
        nu.DelayedDo(0.2, Kill(worker=nu.Literal(wid))),
    )
    start = time.monotonic()
    await asyncio.wait_for(nu.arun(tree, ctx), 5.0)
    assert time.monotonic() - start >= 0.2
    assert [(s.exitcode, s.cause) for s in statuses] == [(-signal.SIGKILL, "killed")]


async def test_wait_sees_a_worker_that_exits_on_its_own(ctx, pool):
    """No pool verb at all: the child leaves on a raw stop frame and Wait reads its code."""
    tree = nu.mem.Frame(Local, Wait(worker=Local.w), w=Launch())
    task = asyncio.ensure_future(nu.arun(tree, ctx))
    assert await _until(lambda: pool.workers() and pool.status(pool.workers()[0]).state == "idle")
    handle = pool._workers[pool.workers()[0]]
    await asyncio.sleep(0.05)
    assert not task.done()
    handle.conn.send(("stop",))
    value, _ = await asyncio.wait_for(task, 5.0)
    assert (value.exitcode, value.cause) == (0, "stopped")


async def test_a_cancelled_wait_leaves_no_waiter_behind(ctx, pool):
    wid = pool.launch()
    task = asyncio.ensure_future(nu.arun(Wait(worker=nu.Literal(wid)), ctx))
    handle = pool._workers[wid]
    assert await _until(lambda: bool(handle._exit_waiters))
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert handle._exit_waiters == []
    assert pool.status(wid).state == "idle"


async def test_wait_with_a_timeout_returns_the_status_as_it_stands(ctx, pool):
    wid = pool.launch()
    start = time.monotonic()
    status = pool.wait(wid, timeout=0.2)
    assert 0.2 <= time.monotonic() - start < 0.6
    assert status.state == "idle"

    start = time.monotonic()
    value, _ = await nu.arun(Wait(worker=nu.Literal(wid), timeout=0.2), ctx)
    assert 0.2 <= time.monotonic() - start < 0.6
    assert value.state == "idle"


async def test_wait_with_a_timeout_returns_when_the_pipe_closed_but_the_process_lingers(pool):
    """The worker hangs up its pipe and holds on: requests fail, Wait is still bounded."""
    wid = pool.launch()
    pid = pool.status(wid).pid
    start = time.monotonic()
    with pytest.raises(WorkerGone):
        await asyncio.wait_for(pool.ateleport(wid, HoldAfterHangup(600)), 5.0)
    assert time.monotonic() - start < 2.0
    assert _pid_alive(pid)

    start = time.monotonic()
    status = await pool.await_exit(wid, timeout=0.3)
    assert 0.3 <= time.monotonic() - start < 0.8
    assert status.state != "exited"
    assert pool.wait(wid, timeout=0.1).state != "exited"

    await pool.akill(wid)
    status = pool.status(wid)
    assert (status.state, status.exitcode, status.cause) == ("exited", -9, "killed")


# --- spares -----------------------------------------------------------------


def test_spares_fill_launch_takes_one_and_the_shelf_refills():
    pool = WorkerPool(name="nu-test-spares", spares=2)
    pool.setup(None)  # type: ignore[arg-type]
    try:
        # Warming spares are registered but never listed.
        assert _sync_until(lambda: len(pool._workers) == 2)
        assert pool.workers() == []
        assert _sync_until(lambda: len(pool._shelf) == 2)
        shelf = list(pool._shelf)
        assert pool.workers() == []  # spares are not handed out yet

        start = time.monotonic()
        taken = pool.launch()
        assert time.monotonic() - start < 0.1  # a list pop, not a spawn
        assert taken == shelf[0]
        assert pool.workers() == [taken]
        assert pool.teleport(taken, nu.Add(1, 1)) == 2

        # The take started a refill; it stays unlisted while it warms up.
        assert _sync_until(lambda: len(pool._workers) == 3)
        assert pool.workers() == [taken]
        assert _sync_until(lambda: len(pool._shelf) == 2)
        assert taken not in pool._shelf

        # An init of its own is never a spare.
        cold = pool.launch(nu.Provide(dict, {}))
        assert cold not in shelf and cold not in pool._shelf
        pids = [pool.status(w).pid for w in [*pool.workers(), *pool._shelf]]
    finally:
        pool.cleanup()
    assert pool._shelf == []
    assert pool.workers() == []
    assert not any(_pid_alive(pid) for pid in pids)


async def test_a_spare_that_died_on_the_shelf_is_never_handed_out():
    pool = WorkerPool(name="nu-test-spares-dead", spares=1)
    await pool.asetup(None)  # type: ignore[arg-type]
    try:
        assert await _until(lambda: len(pool._shelf) == 1)
        dead = pool._shelf[0]
        os.kill(pool.status(dead).pid, signal.SIGKILL)
        assert (await pool.await_exit(dead, timeout=5.0)).exitcode == -signal.SIGKILL
        assert await _until(lambda: dead not in pool._shelf)
        taken = await pool.alaunch()
        assert taken != dead
        assert pool.status(taken).state == "idle"
        assert dead not in pool.workers()
    finally:
        await pool.acleanup()


async def test_spares_in_a_tree_through_the_preset_leave_nothing_behind():
    ref = PoolRef()
    tree = pool_preset(
        name="nu-test-spares-tree",
        spares=1,
        body=nu.mem.Frame(Local, Status(worker=Local.w), w=ref.launch()),
    )
    status, _ = await nu.arun(tree)
    assert status.state == "idle"
    assert not _pid_alive(status.pid)


def test_spares_in_a_sync_tree():
    ref = PoolRef()
    tree = pool_preset(
        name="nu-test-spares-sync",
        spares=1,
        body=nu.mem.Frame(Local, Status(worker=Local.w), w=ref.launch()),
    )
    status, _ = nu.run(tree)
    assert status.state == "idle"
    assert not _pid_alive(status.pid)


async def test_closing_mid_refill_leaves_no_worker():
    """The close lands while every spare is still coming up: none of them survives it."""
    pids: list[int] = []

    class _Spy(WorkerPool):
        def _spawn(self, wid, bracket):
            handle = super()._spawn(wid, bracket)
            pids.append(handle.pid)
            return handle

    pool = _Spy(name="nu-test-early", spares=3, grace=2.0)
    await pool.asetup(None)  # type: ignore[arg-type]
    await asyncio.sleep(0.05)
    start = time.monotonic()
    await pool.acleanup()
    assert time.monotonic() - start < 2.3
    # Refill threads past the close refuse to spawn; the rest were stopped.
    assert await _until(lambda: pool._filling == 0)
    assert pool._shelf == [] and pool.workers() == []
    assert all(not _pid_alive(pid) for pid in pids)
