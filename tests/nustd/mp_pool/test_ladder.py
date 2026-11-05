"""The ladder, the toolkit verbs and the status record. Real processes, checked by pid.

The close and ``Stop`` climb one ladder under one budget: the ``stop`` frame,
SIGINT at 60% of ``grace``, SIGTERM at 80%, SIGKILL at 95%, done by
``grace``. Each kind of worker here is built to end at one rung:

- cooperative: an idle loop or an async body, gone on the frame, exit 0
- sync-stuck: a busy loop the frame never reaches, ended by SIGINT, exit 0
- deaf to SIGINT: a busy loop that swallows ``KeyboardInterrupt``, ended by
  SIGTERM (``SystemExit``), exit 143
- wedged: deaf to SIGINT and ignoring SIGTERM, ended by SIGKILL, exit -9
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import os
import signal
import subprocess
import sys
import threading
import time

import pytest
from _support.pool_workers import (
    RESIDENT,
    AGuarded,
    Die,
    ForkSleeper,
    IgnoreTerm,
    SlowInit,
    Spin,
    Stubborn,
    Touch,
)

import nu
from nustd.mp_pool import (
    Cancel,
    Dispatch,
    Interrupt,
    Interrupted,
    Launch,
    PoolRef,
    Status,
    Stop,
    UnknownWorker,
    WorkerGone,
    WorkerPool,
    Workers,
    resources,
)
from nustd.mp_pool import (
    pool as pool_preset,
)


pytestmark = pytest.mark.slow

TERMED = 128 + signal.SIGTERM
KILLED = -signal.SIGKILL
# What a close or a stop may overrun its budget by.
EPSILON = 0.3


class Local(nu.Shape):
    """The worker a tree launched, held for the rest of the tree."""

    w = nu.mem.IntRef.slot()


W = Local.w


# --- helpers ----------------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _dead(pid: int) -> bool:
    """Gone, or a zombie nobody has reaped yet."""
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


@pytest.fixture
def pool():
    p = WorkerPool(name="nu-test-ladder", grace=2.0)
    p.setup(None)  # type: ignore[arg-type]
    try:
        yield p
    finally:
        p.cleanup()


def _mixed(pool: WorkerPool) -> dict[str, int]:
    """One worker per rung, each already in the state that makes it end there."""
    workers = {
        "cooperative": pool.launch(),
        "sync_stuck": pool.launch(),
        "deaf_to_int": pool.launch(),
        "wedged": pool.launch(nu.Provide(IgnoreTerm, {})),
    }
    pool.dispatch(workers["cooperative"], RESIDENT)
    pool.dispatch(workers["sync_stuck"], Spin(60))
    pool.dispatch(workers["deaf_to_int"], Stubborn(60))
    pool.dispatch(workers["wedged"], Stubborn(60))
    time.sleep(0.2)  # every busy loop is holding its worker's loop by now
    return workers


# Where each kind ends, as (exit code, cause, earliest share of grace, latest share).
RUNGS = {
    "cooperative": (0, "stopped", 0.0, 0.6),
    "sync_stuck": (0, "stopped", 0.6, 0.8),
    "deaf_to_int": (TERMED, "killed", 0.8, 0.95),
    "wedged": (KILLED, "killed", 0.95, 1.0),
}


def _watch_exits(pool: WorkerPool, workers: dict[str, int]) -> dict[str, float]:
    """When each worker's exit lands, measured by a thread per worker blocked in ``wait``."""
    ended: dict[str, float] = {}

    def watch(kind: str, wid: int) -> None:
        pool.wait(wid)
        ended[kind] = time.monotonic()

    for kind, wid in workers.items():
        threading.Thread(target=watch, args=(kind, wid), daemon=True).start()
    return ended


def _assert_rungs(pool, workers, ended, start, grace):
    for kind, wid in workers.items():
        code, cause, earliest, latest = RUNGS[kind]
        status = pool.status(wid)
        assert (kind, status.state, status.exitcode, status.cause) == (kind, "exited", code, cause)
        took = ended[kind] - start
        assert earliest * grace - 0.05 <= took < latest * grace + EPSILON, (kind, took)
        assert _dead(status.pid)


# --- the ladder ---------------------------------------------------------------


def test_close_climbs_one_ladder_for_every_worker_within_grace():
    pool = WorkerPool(name="nu-test-mixed", grace=2.0)
    pool.setup(None)  # type: ignore[arg-type]
    workers = _mixed(pool)
    ended = _watch_exits(pool, workers)

    start = time.monotonic()
    pool.cleanup()
    took = time.monotonic() - start
    assert took < pool.grace + EPSILON
    assert _wait(lambda: len(ended) == len(workers), timeout=1.0)
    _assert_rungs(pool, workers, ended, start, pool.grace)


async def test_acleanup_climbs_the_same_ladder_and_never_blocks_the_loop():
    pool = WorkerPool(name="nu-test-amixed", grace=2.0)
    pool.setup(None)  # type: ignore[arg-type]
    workers = _mixed(pool)
    ended = _watch_exits(pool, workers)

    ticks: list[float] = []

    async def ticker() -> None:
        while True:
            ticks.append(time.monotonic())
            await asyncio.sleep(0.01)

    tick = asyncio.create_task(ticker())
    await asyncio.sleep(0.05)
    start = time.monotonic()
    await pool.acleanup()
    took = time.monotonic() - start
    tick.cancel()

    assert took < pool.grace + EPSILON
    during = [t for t in ticks if start <= t <= start + took]
    gaps = [b - a for a, b in itertools.pairwise(during)]
    assert len(during) >= took / 0.01 * 0.5  # the loop kept turning the whole time
    assert max(gaps) < 0.1
    assert _wait(lambda: len(ended) == len(workers), timeout=1.0)
    _assert_rungs(pool, workers, ended, start, pool.grace)


def test_stop_on_a_cooperative_worker_runs_finally_and_teardown(tmp_path):
    torn, fin = tmp_path / "torn", tmp_path / "finally"
    pool = WorkerPool(name="nu-test-stop", init=nu.Provide(Touch, {"path": str(torn)}))
    pool.setup(None)  # type: ignore[arg-type]
    try:
        w = pool.launch()
        pool.dispatch(w, AGuarded(str(fin), 60))
        start = time.monotonic()
        status = pool.stop(w)
        assert time.monotonic() - start < 1.0
        assert (status.state, status.exitcode, status.cause) == ("exited", 0, "stopped")
        assert fin.read_text() == "finally ran"
        assert torn.read_text() == "torn down"
        assert w not in pool.workers()
    finally:
        pool.cleanup()


def test_stop_on_a_wedged_worker_ends_by_sigkill_within_grace(pool):
    w = pool.launch(nu.Provide(IgnoreTerm, {}))
    pool.dispatch(w, Stubborn(60))
    time.sleep(0.1)
    start = time.monotonic()
    status = pool.stop(w, grace=1.0)
    took = time.monotonic() - start
    assert 0.9 <= took < 1.0 + EPSILON
    assert (status.state, status.exitcode, status.cause) == ("exited", KILLED, "killed")
    assert _dead(status.pid)


async def test_astop_on_a_wedged_worker_ends_by_sigkill_within_grace(pool):
    w = await pool.alaunch(nu.Provide(IgnoreTerm, {}))
    await pool.adispatch(w, Stubborn(60))
    await asyncio.sleep(0.1)
    ctx = nu.Context().bind(WorkerPool, pool)
    start = time.monotonic()
    status, _ = await nu.arun(Stop(worker=nu.Literal(w), grace=1.0), ctx)
    assert 0.9 <= time.monotonic() - start < 1.0 + EPSILON
    assert (status.exitcode, status.cause) == (KILLED, "killed")


async def test_a_cancelled_astop_kills_the_worker(pool):
    w = await pool.alaunch(nu.Provide(IgnoreTerm, {}))
    await pool.adispatch(w, Stubborn(60))
    task = asyncio.create_task(pool.astop(w, grace=10.0))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    status = await pool.await_exit(w, timeout=2.0)
    assert (status.state, status.exitcode, status.cause) == ("exited", KILLED, "killed")


def test_stop_on_a_gone_worker_answers_its_record(pool):
    w = pool.launch()
    first = pool.stop(w)
    assert pool.stop(w) == first
    with pytest.raises(UnknownWorker):
        pool.stop(999)


# --- death seen by pid ----------------------------------------------------------


def test_the_exit_watch_uses_the_platform_mechanism(pool):
    """A pidfd on Linux (the syscall when ``os`` lacks it), a kqueue on mac. Never the sentinel."""
    w = pool.launch()
    kind = pool._workers[w]._watch.kind
    if sys.platform.startswith("linux"):
        assert kind == "pidfd"
    elif sys.platform == "darwin":
        assert kind == "kqueue"
    else:
        pytest.skip(f"no exit watch expectation for {sys.platform}")


async def test_a_crash_is_seen_by_pid_while_a_forked_child_holds_the_pipe(pool):
    """A plain fork keeps every descriptor: only the pid watch sees the worker go.

    Bounded hard: with the pid watch missing this would wait out the child.
    """
    w = await pool.alaunch()
    child = await asyncio.wait_for(pool.ateleport(w, ForkSleeper(20)), 5.0)
    assert _pid_alive(child)
    start = time.monotonic()
    with pytest.raises(WorkerGone) as gone:
        await asyncio.wait_for(pool.ateleport(w, Die(3)), 5.0)
    assert time.monotonic() - start < 1.0
    assert (gone.value.cause, gone.value.exitcode, gone.value.wid) == ("crashed", 3, w)
    assert w not in pool.workers()
    status = pool.wait(w, timeout=1.0)
    assert (status.state, status.exitcode, status.cause) == ("exited", 3, "crashed")
    assert _wait(lambda: _dead(child), timeout=2.0)  # swept with the group


def test_workers_drops_a_worker_that_died_by_itself(pool):
    a, b = pool.launch(), pool.launch()
    os.kill(pool.status(a).pid, signal.SIGKILL)
    assert pool.wait(a, timeout=5.0).exitcode == KILLED
    assert pool.workers() == [b]
    ctx = nu.Context().bind(WorkerPool, pool)
    assert nu.run(nu.Collect(Workers()), ctx)[0] == [b]
    assert pool.status(a).cause == "crashed"  # not the pool's own kill


def test_exited_records_are_bounded(pool, monkeypatch):
    monkeypatch.setattr(resources, "_KEPT_EXITED", 2)
    ids = [pool.launch() for _ in range(3)]
    for w in ids:
        pool.kill(w)
    with pytest.raises(UnknownWorker):
        pool.status(ids[0])
    assert [pool.status(w).state for w in ids[1:]] == ["exited", "exited"]


# --- interrupt ----------------------------------------------------------------


async def test_interrupt_ends_every_job_with_interrupted_and_the_worker_serves_on(pool):
    w = await pool.alaunch()
    ctx = nu.Context().bind(WorkerPool, pool)
    # The resident jobs first, then the spin: a frame still in the pipe when
    # the SIGINT lands is not running yet, so the spin must be the last in.
    resident = asyncio.create_task(pool.ateleport(w, RESIDENT))
    await pool.adispatch(w, RESIDENT)
    await asyncio.sleep(0.2)
    stuck = asyncio.create_task(pool.ateleport(w, Spin(30)))
    await asyncio.sleep(0.3)
    assert len(pool.status(w).jobs) == 3

    start = time.monotonic()
    await nu.arun(Interrupt(worker=nu.Literal(w)), ctx)
    for task in (stuck, resident):
        with pytest.raises(Interrupted) as interrupted:
            await asyncio.wait_for(task, 2.0)
        assert interrupted.value.wid == w
    assert time.monotonic() - start < 1.0
    assert await _until(lambda: pool.status(w).jobs == ())
    assert pool.status(w).state == "idle"
    assert await pool.ateleport(w, nu.Add(1, 2)) == 3

    # And again, from the sync path.
    outcome: list[object] = []
    t = threading.Thread(
        target=lambda: outcome.append(_catch(lambda: pool.teleport(w, Spin(30)))), daemon=True
    )
    t.start()
    await asyncio.sleep(0.3)
    pool.interrupt(w)
    t.join(timeout=2.0)
    assert isinstance(outcome[0], Interrupted)
    assert await pool.ateleport(w, nu.Add(2, 2)) == 4


def _catch(call):
    try:
        return call()
    except BaseException as exc:
        return exc


PARALLEL_SPIN = nu.Parallel((Spin(4), "async"), (Spin(4), "async"))


async def test_interrupt_reaches_a_sync_body_in_a_sub_task(pool):
    """A body whose sync stretch runs in a task of its own: still interrupted at once."""
    w = await pool.alaunch()
    call = asyncio.create_task(pool.ateleport(w, PARALLEL_SPIN))
    await asyncio.sleep(0.5)
    start = time.monotonic()
    pool.interrupt(w)
    with pytest.raises(Interrupted):
        await asyncio.wait_for(call, 3.0)
    assert time.monotonic() - start < 1.0
    assert await _until(lambda: pool.status(w).jobs == ())
    assert await pool.ateleport(w, nu.Add(1, 1)) == 2


def test_stop_reaches_a_sync_body_in_a_sub_task_at_the_sigint_rung(tmp_path):
    torn = tmp_path / "torn"
    pool = WorkerPool(name="nu-test-substop", init=nu.Provide(Touch, {"path": str(torn)}))
    pool.setup(None)  # type: ignore[arg-type]
    try:
        w = pool.launch()
        pool.dispatch(w, PARALLEL_SPIN)
        time.sleep(0.3)
        start = time.monotonic()
        status = pool.stop(w, grace=2.0)
        took = time.monotonic() - start
        assert 1.15 <= took < 1.6  # the SIGINT rung, not SIGKILL
        assert (status.exitcode, status.cause) == (0, "stopped")
        assert torn.read_text() == "torn down"
    finally:
        pool.cleanup()


def test_interrupt_on_a_gone_or_unknown_worker_is_a_no_op(pool):
    w = pool.launch()
    pool.kill(w)
    pool.interrupt(w)
    pool.interrupt(999)


# --- status -----------------------------------------------------------------


async def test_status_through_a_whole_life():
    pool = WorkerPool(name="nu-test-status", grace=1.0)
    await pool.asetup(None)  # type: ignore[arg-type]
    try:
        launching = asyncio.create_task(pool.alaunch(nu.Provide(SlowInit, {"seconds": 0.6})))
        assert await _until(lambda: 0 in pool._workers)
        assert pool.status(0).state == "starting"
        assert pool.status(0).started_at is None
        w = await launching
        assert w == 0
        assert pool.status(w).state == "idle"
        assert pool.status(w).pgid == pool.status(w).pid

        job = await pool.adispatch(w, RESIDENT)
        status = pool.status(w)
        assert (status.state, status.jobs) == ("busy", (job,))
        await pool.acancel(w, job)
        assert await _until(lambda: pool.status(w).state == "idle")

        # Stopping: a stop under way on a worker that does not answer the frame.
        await pool.adispatch(w, Stubborn(60))
        stopping = asyncio.create_task(pool.astop(w))
        assert await _until(lambda: pool.status(w).state == "stopping")
        status = await stopping
        # Deaf to the frame and to SIGINT: the SIGTERM rung ends it, the pool's own signal.
        assert (status.state, status.exitcode, status.cause) == ("exited", TERMED, "killed")

        crashing = await pool.alaunch()
        with pytest.raises(WorkerGone):
            await pool.ateleport(crashing, Die(5))
        status = pool.status(crashing)
        assert (status.state, status.exitcode, status.cause) == ("exited", 5, "crashed")
        assert status.jobs == ()
        assert status.pid and status.name == f"nu:nu-test-status-{crashing}"
    finally:
        await pool.acleanup()


# --- dispatch and cancel ------------------------------------------------------


async def test_dispatch_yields_a_job_id_that_cancel_takes(tmp_path):
    fin = tmp_path / "finally"
    statuses: list = []

    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    def keep(status: object) -> None:
        statuses.append(status)

    body = nu.let(
        Dispatch(body=AGuarded(str(fin), 60), worker=W),
        lambda job: nu.Sequential(
            keep(Status(worker=W)),
            Cancel(worker=W, job=job),
            nu.Delay(0.3),
            keep(Status(worker=W)),
        ),
    )
    tree = pool_preset(name="nu-test-cancel", body=nu.mem.Frame(Local, body, w=Launch()))
    await nu.arun(tree)
    busy, after = statuses
    assert busy.state == "busy" and len(busy.jobs) == 1
    assert after.jobs == ()
    assert fin.read_text() == "finally ran"


def test_a_dispatched_bodys_error_is_logged_and_kept_on_status(pool, caplog):
    w = pool.launch()
    with caplog.at_level(logging.ERROR, logger="nustd.mp_pool"):
        job = pool.dispatch(w, nu.Div(1, 0))
        assert _wait(lambda: pool.status(w).errors != ())
    ((failed, exc),) = pool.status(w).errors
    assert failed == job
    assert isinstance(exc, ZeroDivisionError)
    assert any(f"dispatched job {job} raised" in r.getMessage() for r in caplog.records)
    assert pool.status(w).state == "idle"  # the worker is fine


# --- tagged refs --------------------------------------------------------------


def test_two_tagged_pools_in_one_scope():
    a, b = PoolRef("a"), PoolRef("b")
    statuses: list = []

    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    def keep(status: object) -> None:
        statuses.append(status)

    body = nu.let(
        a.launch(),
        lambda wa: nu.let(
            b.launch(),
            lambda wb: nu.Sequential(
                keep(a.status(wa)),
                keep(b.status(wb)),
                keep(b.stop(wb)),
                keep(a.status(wa)),
            ),
        ),
    )
    tree = pool_preset(name="pb", tags=("b",), body=pool_preset(name="pa", tags=("a",), body=body))
    nu.run(tree)
    in_a, in_b, stopped_b, still_a = statuses
    assert (in_a.name, in_b.name) == ("nu:pa-0", "nu:pb-0")
    assert stopped_b.state == "exited"
    assert still_a.state == "idle"  # stopping b's worker 0 left a's worker 0 alone


def test_a_tagged_pool_is_not_the_untagged_one():
    tree = pool_preset(name="pa", tags=("a",), body=Launch())
    with pytest.raises(RuntimeError, match="no WorkerPool is bound"):
        nu.run(tree)
