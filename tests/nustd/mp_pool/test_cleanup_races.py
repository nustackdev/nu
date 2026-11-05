"""Close racing launches, kills and cancelled awaits. Real processes, checked by pid.

Every test here ends with nothing alive that the pool spawned, and says so by
pid: ``os.kill(pid, 0)`` for a process that is gone, ``/bin/ps`` for one that
is dead but not yet reaped. Never ``active_children``, which only sees what
``multiprocessing`` still has on its own books.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import subprocess
import threading
import time
from types import SimpleNamespace

import pytest
from _support.pool_workers import RESIDENT, Block, IgnoreTerm, Stubborn

import nu
from nustd.mp_pool import PoolClosed, WorkerGone, WorkerPool, resources


pytestmark = pytest.mark.slow

KILLED = -signal.SIGKILL


# --- helpers ----------------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _dead(pid: int) -> bool:
    """Gone, or a zombie: killed and not reaped yet, which only a join can finish."""
    if not _pid_alive(pid):
        return True
    out = subprocess.run(  # noqa: S603
        ["/bin/ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    ).stdout.strip()
    return out == "" or out.startswith("Z")


def _wait(check, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.01)
    return False


async def _until(check, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        await asyncio.sleep(0.01)
    return False


def _quiet(pool: WorkerPool) -> bool:
    """No worker tracked, no launch between spawn and registration, no kill reaping."""
    with pool._lock:
        return not pool._workers and not pool._launching and not pool._dying


@pytest.fixture
def spy(monkeypatch):
    """Every handle the pool builds, by pid, with a hold right after the spawn when asked.

    The hold is the window the reopen flake lived in: the process exists,
    the pool does not know it yet. ``began`` fires on entering it; a test
    that puts an Event in ``hold`` keeps the launch there until it sets it.
    """
    state = SimpleNamespace(pids=[], handles=[], began=threading.Event(), hold=[])

    class Spying(resources._WorkerHandle):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            state.pids.append(self.proc.pid)
            state.handles.append(self)
            state.began.set()
            if state.hold:
                state.hold[0].wait(10)

    monkeypatch.setattr(resources, "_WorkerHandle", Spying)
    return state


@pytest.fixture
def pool():
    p = WorkerPool(name="nu-test-races")
    p.setup(None)
    try:
        yield p
    finally:
        p.cleanup()


# --- closed -----------------------------------------------------------------


def test_launch_on_a_closed_pool_is_refused(spy):
    pool = WorkerPool(name="nu-test-closed")
    pool.setup(None)
    pool.cleanup()

    start = time.monotonic()
    with pytest.raises(PoolClosed):
        pool.launch()
    # Refused before anything is spawned: no process, no handle, at once.
    assert time.monotonic() - start < 0.1
    assert spy.pids == []
    assert pool.workers() == []
    pool.cleanup()  # idempotent


async def test_alaunch_on_a_closed_pool_is_refused(spy):
    pool = WorkerPool(name="nu-test-aclosed")
    pool.setup(None)
    pool.cleanup()
    with pytest.raises(WorkerGone):
        await pool.alaunch()
    assert spy.pids == []


def test_a_launch_landing_after_close_kills_its_own_worker(spy):
    """Close gives up waiting on a launch (grace is short); the launch then reaps itself."""
    pool = WorkerPool(name="nu-test-late", grace=0.2)
    pool.setup(None)
    release = threading.Event()
    spy.hold.append(release)
    outcome: list[object] = []

    def launching() -> None:
        try:
            outcome.append(pool.launch())
        except BaseException as exc:
            outcome.append(exc)

    t = threading.Thread(target=launching, daemon=True)
    t.start()
    assert spy.began.wait(10)

    start = time.monotonic()
    pool.cleanup()  # the launch is held, so this times out its wait
    assert 0.2 <= time.monotonic() - start < 1.0
    assert _pid_alive(spy.pids[0])  # held past the close, the pool cannot see it

    release.set()
    t.join(timeout=10)
    assert not t.is_alive()
    assert isinstance(outcome[0], PoolClosed)
    assert not _pid_alive(spy.pids[0])
    assert _quiet(pool)


def test_cleanup_waits_for_a_launch_in_flight(spy):
    """A launch between spawn and registration lands before close returns, and dies."""
    pool = WorkerPool(name="nu-test-inflight", grace=2.0)
    pool.setup(None)
    release = threading.Event()
    spy.hold.append(release)
    outcome: list[object] = []

    def launching() -> None:
        try:
            outcome.append(pool.launch())
        except BaseException as exc:
            outcome.append(exc)

    t = threading.Thread(target=launching, daemon=True)
    t.start()
    assert spy.began.wait(10)

    threading.Timer(0.1, release.set).start()
    pool.cleanup()
    # No polling: close waited for the launch to land and for its kill to reap.
    assert not _pid_alive(spy.pids[0])
    assert _quiet(pool)
    t.join(timeout=10)
    assert isinstance(outcome[0], WorkerGone)


# --- the flake shape ----------------------------------------------------------


async def test_launch_racing_cleanup_leaves_nothing(spy):
    """``alaunch`` cancelled with its thread just past the spawn, close right behind it.

    The window is not held here, so whether the cancel lands before or after
    registration is chance; a smoke loop over the shape. The held version is
    ``test_cleanup_waits_for_a_launch_in_flight``.
    """
    for _ in range(5):
        pool = WorkerPool(name="nu-test-flake")
        pool.setup(None)
        spy.began.clear()
        task = asyncio.create_task(pool.alaunch())
        assert await _until(spy.began.is_set)

        task.cancel()
        pool.cleanup()
        with contextlib.suppress(asyncio.CancelledError, WorkerGone):
            await task

        # Close already returned, so no grace here: that is the assertion.
        assert not _pid_alive(spy.pids[-1])
        assert _quiet(pool)
    assert len(spy.pids) == 5


# --- cancelled awaits ---------------------------------------------------------


async def test_cancelled_alaunch_leaves_no_process(spy, pool):
    """Cancelled while the child is still coming up: the thread kills what it launched."""
    task = asyncio.create_task(pool.alaunch())
    assert await _until(spy.began.is_set)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert await _until(lambda: _quiet(pool))
    assert not _pid_alive(spy.pids[0])


async def test_alaunch_cancelled_as_it_lands_leaves_no_process(spy, pool, monkeypatch):
    """Cancelled after the thread landed the id but before the awaiter took it."""
    landed = threading.Event()
    land = resources._Landing.land

    def landing(self, wid):
        ok = land(self, wid)
        landed.set()
        return ok

    monkeypatch.setattr(resources._Landing, "land", landing)
    task = asyncio.create_task(pool.alaunch())
    assert await _until(landed.is_set)

    if task.cancel():
        with pytest.raises(asyncio.CancelledError):
            await task
        # The awaiter found the id landed, so the worker was its to kill:
        # off the books at once, reaped on a thread.
        assert pool.workers() == []
    else:
        pool.kill(await task)  # delivered before the cancel could land

    assert await _until(lambda: _quiet(pool))
    assert not _pid_alive(spy.pids[0])


async def test_cancelled_adispatch_cancels_the_body_it_cannot_hand_back(spy, pool):
    w = await pool.alaunch()
    handle = pool._workers[w]
    # Hold the worker's loop so the ack cannot come before the cancel does.
    await pool.adispatch(w, Block(0.5))

    call = asyncio.create_task(pool.adispatch(w, RESIDENT))
    await asyncio.sleep(0.1)  # the frame is out, the ack is stuck behind Block
    call.cancel()
    with pytest.raises(asyncio.CancelledError):
        await call

    # Once free the worker acks, then reads the cancel: the body never settles in.
    assert await _until(lambda: not pool.status(w).jobs, timeout=5.0)
    assert handle._pending == {}
    assert await pool.ateleport(w, nu.Add(1, 2)) == 3

    pool.cleanup()
    assert not _pid_alive(spy.pids[0])


async def test_adispatch_cancelled_before_its_frame_is_out_cancels_the_body(spy, pool):
    w = await pool.alaunch()
    handle = pool._workers[w]
    handle._send_lock.acquire()  # the sender thread blocks here
    try:
        call = asyncio.create_task(pool.adispatch(w, RESIDENT))
        await asyncio.sleep(0.1)
        call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await call
    finally:
        handle._send_lock.release()

    # The frame goes out now, its cancel right behind it.
    assert await _until(lambda: handle._pending == {} and not pool.status(w).jobs, timeout=5.0)
    assert await pool.ateleport(w, nu.Add(2, 2)) == 4
    pool.cleanup()
    assert not _pid_alive(spy.pids[0])


def test_dispatch_ack_timeout_pops_pending_and_cancels_the_body(spy, pool):
    w = pool.launch()
    handle = pool._workers[w]
    pool.dispatch(w, Block(0.8))
    pool.ack_timeout = 0.2

    with pytest.raises(TimeoutError):
        pool.dispatch(w, RESIDENT)
    assert handle._pending == {}
    assert _wait(lambda: not pool.status(w).jobs, timeout=5.0)
    assert pool.teleport(w, nu.Add(1, 1)) == 2
    pool.cleanup()
    assert not _pid_alive(spy.pids[0])


async def test_adispatch_ack_timeout_pops_pending_and_cancels_the_body(spy, pool):
    w = await pool.alaunch()
    handle = pool._workers[w]
    await pool.adispatch(w, Block(0.8))
    pool.ack_timeout = 0.2

    with pytest.raises(TimeoutError):
        await pool.adispatch(w, RESIDENT)
    assert handle._pending == {}
    assert await _until(lambda: not pool.status(w).jobs, timeout=5.0)
    assert await pool.ateleport(w, nu.Add(1, 1)) == 2
    pool.cleanup()
    assert not _pid_alive(spy.pids[0])


async def test_a_cancel_landing_as_the_ack_resolves_still_cancels(spy, pool):
    """The ack resolves and the caller is cancelled in the same breath: the cancel wins.

    ``wait_for`` on 3.10 hands the result back in this ordering and the
    cancel is lost; the plain ``asyncio.wait`` the pool uses does not.
    """
    w = await pool.alaunch()
    handle = pool._workers[w]
    await pool.adispatch(w, Block(0.5))  # the real ack for the next one is held back

    call = asyncio.create_task(pool.adispatch(w, RESIDENT))
    assert await _until(lambda: bool(handle._pending))
    token, reply = next(iter(handle._pending.items()))
    assert await _until(lambda: reply.sent)

    # The reader resolves the ack, and the cancel lands on the very next step.
    handle._handle(("ack", token))
    asyncio.get_running_loop().call_soon(call.cancel)
    with pytest.raises(asyncio.CancelledError):
        await call

    assert await _until(lambda: not pool.status(w).jobs, timeout=5.0)
    assert handle._pending == {}
    assert await pool.ateleport(w, nu.Add(2, 3)) == 5
    pool.cleanup()
    assert not _pid_alive(spy.pids[0])


async def test_cancelled_akill_has_still_killed_the_worker(spy):
    """The SIGKILL is out before akill's first await: cancelling it changes nothing."""
    pool = WorkerPool(name="nu-test-akill", grace=0.5)
    pool.setup(None)
    w = pool.launch(nu.Provide(IgnoreTerm, {}))  # SIGTERM ignored: only SIGKILL ends it
    pid = spy.pids[0]
    handle = spy.handles[0]

    task = asyncio.create_task(pool.akill(w))
    await asyncio.sleep(0)  # one step: the signal is out
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert pool.workers() == []
    assert handle.wait_exit(2.0)
    assert pool.status(w).exitcode == KILLED
    assert not _pid_alive(pid)
    start = time.monotonic()
    pool.cleanup()
    assert time.monotonic() - start < 0.2
    assert _quiet(pool)


async def test_a_close_right_behind_an_akill_waits_for_its_reap(spy, pool):
    w = await pool.alaunch()
    handle = pool._workers[w]
    task = asyncio.create_task(pool.akill(w))
    await asyncio.sleep(0)  # one step: parked as dying, SIGKILL sent
    task.cancel()

    start = time.monotonic()
    pool.cleanup()  # waits for that reap, not for grace to run out
    assert time.monotonic() - start < 1.0
    assert handle.wait_exit(2.0)
    assert pool.status(w).exitcode == KILLED
    assert _quiet(pool)
    assert not _pid_alive(spy.pids[0])
    with pytest.raises(asyncio.CancelledError):
        await task


# --- interrupted cleanup ------------------------------------------------------


def test_cleanup_interrupted_by_keyboard_interrupt_leaves_no_process(spy):
    """A second Ctrl+C lands inside close: SIGKILL to everything, no waits, re-raised."""
    pool = WorkerPool(name="nu-test-ctrlc", grace=5.0)
    pool.setup(None)
    plain = pool.launch()
    stubborn = pool.launch(nu.Provide(IgnoreTerm, {}))
    pool.dispatch(stubborn, Stubborn(60))  # deaf to the stop frame and SIGINT, no SIGTERM
    assert pool.workers() == [plain, stubborn]
    pids = list(spy.pids)

    threading.Timer(0.3, os.kill, (os.getpid(), signal.SIGINT)).start()
    start = time.monotonic()
    with pytest.raises(KeyboardInterrupt):
        pool.cleanup()
    assert time.monotonic() - start < 2.0

    # The plain one stopped on the frame; the stubborn one got the SIGKILL.
    assert _wait(lambda: all(_dead(pid) for pid in pids), timeout=2.0)
    assert spy.handles[0].wait_exit(2.0) and spy.handles[1].wait_exit(2.0)
    assert pool.status(plain).exitcode == 0
    assert pool.status(stubborn).exitcode == KILLED
    assert _quiet(pool)
    assert all(not _pid_alive(pid) for pid in pids)


class _Interrupt(BaseException):
    """Stands in for whatever lands on the closing thread mid-ladder."""


def test_cleanup_interrupted_mid_ladder_kills_everything_and_records_every_exit(spy, monkeypatch):
    """The ladder blows up: every worker gets SIGKILL and every exit is still recorded."""
    pool = WorkerPool(name="nu-test-base", grace=5.0)
    pool.setup(None)
    ids = [pool.launch(nu.Provide(IgnoreTerm, {})) for _ in range(2)]
    pids = list(spy.pids)

    def blowing_up(handles, start, grace):
        raise _Interrupt

    monkeypatch.setattr(resources, "_climb", blowing_up)
    with pytest.raises(_Interrupt):
        pool.cleanup()
    assert _wait(lambda: all(_dead(pid) for pid in pids), timeout=2.0)
    for handle in spy.handles:
        assert handle.wait_exit(2.0)
    assert [pool.status(w).exitcode for w in ids] == [KILLED, KILLED]
    assert _wait(lambda: _quiet(pool), timeout=2.0)
    assert all(not _pid_alive(pid) for pid in pids)


async def test_acleanup_cancelled_mid_ladder_kills_everything(spy):
    """A cancellation landing inside ``acleanup``: SIGKILL to every group, then it goes on up."""
    pool = WorkerPool(name="nu-test-acancel", grace=5.0)
    pool.setup(None)
    w = await pool.alaunch(nu.Provide(IgnoreTerm, {}))
    await pool.adispatch(w, Stubborn(60))
    waiter = asyncio.create_task(pool.await_exit(w))

    task = asyncio.create_task(pool.acleanup())
    await asyncio.sleep(0.3)  # in the polite rung, which this worker never answers
    assert not task.done()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    status = await asyncio.wait_for(waiter, timeout=2.0)
    assert (status.exitcode, status.cause) == (KILLED, "killed")
    assert _wait(lambda: not _pid_alive(spy.pids[0]), timeout=2.0)
    assert _quiet(pool)


# --- spares -----------------------------------------------------------------


async def test_closing_the_pool_mid_refill_leaves_no_worker(spy):
    """Spares still coming up when the close lands: each one is stopped or never spawned."""
    pool = WorkerPool(name="nu-test-refill", spares=2, grace=2.0)
    await pool.asetup(None)  # type: ignore[arg-type]
    assert await _until(spy.began.is_set)  # at least one refill past its spawn

    await pool.acleanup()
    assert pool._shelf == []
    assert await _until(lambda: _quiet(pool) and pool._filling == 0)
    assert spy.pids
    assert all(not _pid_alive(pid) for pid in spy.pids)
