"""``Wait`` and the ``spares`` preset. Real processes, no mocks, spawns kept few."""

from __future__ import annotations

import asyncio
import multiprocessing
import os
import signal
import time

import pytest

import nu
from nustd.mp_pool import Alive, Kill, Launch, PoolRef, Wait, WorkerPool
from nustd.mp_pool.presets import Spares, TakeSpare, spares


pytestmark = pytest.mark.slow


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


# --- Wait -------------------------------------------------------------------


async def test_wait_on_a_killed_worker_returns_at_once(ctx, pool):
    wid = pool.launch()
    pool.kill(wid)
    value, _ = await asyncio.wait_for(nu.arun(Wait(worker=nu.Literal(wid)), ctx), 1.0)
    assert value is None
    # The sync path answers the same, without blocking.
    assert nu.run(PoolRef().wait(nu.Literal(wid)), ctx)[0] is None


async def test_wait_on_an_unknown_id_returns_none(ctx):
    value, _ = await asyncio.wait_for(nu.arun(Wait(worker=nu.Literal(999)), ctx), 1.0)
    assert value is None


async def test_wait_completes_when_another_branch_kills_the_worker(ctx, pool):
    wid = pool.launch()
    tree = nu.Gather(
        nu.SetCmd(nu.AttrRef("code"), Wait(worker=nu.Literal(wid))),
        nu.DelayedDo(0.2, Kill(worker=nu.Literal(wid))),
    )
    start = time.monotonic()
    _, out = await asyncio.wait_for(nu.arun(tree, ctx), 5.0)
    assert time.monotonic() - start >= 0.2
    assert out.attrs["code"] == -signal.SIGTERM
    assert not pool.alive(wid)


async def test_wait_sees_a_worker_that_exits_on_its_own(ctx, pool):
    """No kill at all: the child leaves on a stop frame and Wait reads its code."""
    tree = nu.Let("w", Launch(), Wait(worker=nu.AttrRef("w")))
    task = asyncio.ensure_future(nu.arun(tree, ctx))
    assert await _until(lambda: pool.workers() and pool._workers[pool.workers()[0]]._ready.is_set())
    handle = pool._workers[pool.workers()[0]]
    await asyncio.sleep(0.05)
    assert not task.done()
    handle.conn.send(("stop",))
    value, _ = await asyncio.wait_for(task, 5.0)
    assert value == 0


async def test_a_cancelled_wait_leaves_no_waiter_behind(ctx, pool):
    wid = pool.launch()
    task = asyncio.ensure_future(nu.arun(Wait(worker=nu.Literal(wid)), ctx))
    handle = pool._workers[wid]
    assert await _until(lambda: bool(handle._exit_waiters))
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert handle._exit_waiters == []
    assert pool.alive(wid)


# --- spares -----------------------------------------------------------------


async def test_spares_take_refill_and_cleanup(ctx, pool):
    shelf = Spares(size=1)
    await shelf.asetup(ctx)
    assert await _until(lambda: len(shelf.shelf) == 1)
    first = shelf.shelf[0]

    taken, _ = await nu.arun(TakeSpare(), ctx.bind(Spares, shelf))
    assert taken == first
    assert pool.alive(taken)

    # The take started a refill; a fresh worker lands on the shelf.
    assert await _until(lambda: len(shelf.shelf) == 1)
    spare = shelf.shelf[0]
    assert spare != taken
    spare_pid = pool._workers[spare].proc.pid

    await shelf.acleanup()
    assert shelf.shelf == []
    assert spare not in pool.workers()
    assert not _pid_alive(spare_pid)
    # The taken worker is the pool's now, not the shelf's.
    assert pool.alive(taken)


async def test_spares_skip_a_worker_that_died_on_the_shelf(ctx, pool):
    shelf = Spares(size=1)
    await shelf.asetup(ctx)
    try:
        assert await _until(lambda: len(shelf.shelf) == 1)
        dead = shelf.shelf[0]
        os.kill(pool._workers[dead].proc.pid, signal.SIGKILL)
        assert pool.wait(dead, timeout=5.0) == -signal.SIGKILL
        taken = await shelf.atake()
        assert taken != dead
        assert pool.alive(taken)
        assert dead not in pool.workers()
    finally:
        await shelf.acleanup()


async def test_take_spare_in_a_tree_leaves_nothing_behind():
    pids: list[int] = []

    class _Spy(WorkerPool):
        def launch(self, init=None):
            wid = super().launch(init)
            pids.append(self._workers[wid].proc.pid)
            return wid

    tree = nu.Provide(
        _Spy,
        {"name": "nu-test-spares"},
        nu.With(
            spares(1),
            body=nu.Let("w", TakeSpare(), Alive(worker=nu.AttrRef("w"))),
        ),
        bind_as=WorkerPool,
    )
    value, _ = await nu.arun(tree)
    assert value is True
    assert pids
    assert await _until(lambda: not any(_pid_alive(p) for p in pids))


def test_take_spare_without_a_shelf_launches_cold(ctx, pool):
    value, _ = nu.run(TakeSpare(), ctx)
    assert pool.workers() == [value]
    assert pool.alive(value)


async def test_spares_closed_mid_refill_leaves_no_workers():
    # Close the shelf while all its refills are still launching. Each launch
    # outlives the teardown on its thread and must kill its own worker.
    def ours():
        return [p for p in multiprocessing.active_children() if p.name.startswith("nu-test-early")]

    tree = nu.Provide(
        WorkerPool,
        {"name": "nu-test-early"},
        nu.With(spares(3), body=nu.Literal(1)),
    )
    value, _ = await nu.arun(tree)
    assert value == 1
    assert await _until(lambda: not ours(), timeout=4.0), ours()
