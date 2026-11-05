"""Containment and identity: groups, the parent watch, signals in the worker, names.

Real processes, checked by pid and pgid: ``os.kill(pid, 0)`` for a process,
``os.killpg(pgid, 0)`` for a whole group, ``/bin/ps`` for one that is dead
but not reaped yet. The host-side scenarios run a helper host process
(``_support.pool_host``) so the host itself can be SIGKILLed or signalled as
a group.
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from _support import pool_host
from _support.pool_workers import (
    RESIDENT,
    CrashInInit,
    Die,
    Guarded,
    NestedSpawn,
    Shell,
    Sleeper,
    SlowTouch,
    Spin,
    Touch,
)

import nu
from nustd.mp_pool import (
    Interrupted,
    UnknownWorker,
    WorkerGone,
    WorkerPool,
    WorkerStatus,
    resources,
)


pytestmark = pytest.mark.slow

# A worker handles SIGTERM itself (``SystemExit``), so a clean exit on it is 143.
TERMED = 128 + signal.SIGTERM


# --- helpers ----------------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
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


@pytest.fixture
def pool():
    p = WorkerPool(name="nu-test-contain")
    p.setup(None)
    try:
        yield p
    finally:
        p.cleanup()


class _Host:
    """The helper host process, its JSON lines read on a thread so a wait can time out."""

    def __init__(self, mode: str, *, own_group: bool = False) -> None:
        lib = Path(pool_host.__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONPATH": str(lib)}
        self.proc = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "_support.pool_host", mode],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            start_new_session=own_group,
        )
        self._lines: queue.Queue = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._lines.put(line)
        self._lines.put(None)

    def line(self, timeout: float = 30.0) -> dict:
        line = self._lines.get(timeout=timeout)
        assert line is not None, f"host ended early: {self.proc.stderr.read()}"  # type: ignore[union-attr]
        return json.loads(line)

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=10)


# --- the host goes away -------------------------------------------------------


def test_host_sigkilled_leaves_nothing():
    """Idle, sync-blocked and subprocess-holding workers all end within ~2s of the host's SIGKILL."""
    host = _Host("kill")
    try:
        state = host.line()
        pids = [pid for _, pid, _ in state["workers"]]
        pgids = [pgid for _, _, pgid in state["workers"]]
        sleeper = state["sleeper"]
        assert all(_pid_alive(pid) for pid in pids)
        assert _pid_alive(sleeper)
        assert pgids == pids  # each worker leads its own group
        assert os.getpgid(sleeper) in pgids  # the subprocess is in its worker's group

        host.proc.kill()  # SIGKILL: no cleanup of any kind on the host side
        host.proc.wait(timeout=10)
        start = time.monotonic()
        assert _wait(lambda: all(_dead(pid) for pid in [*pids, sleeper]), timeout=2.5)
        assert _wait(lambda: not any(_group_alive(pgid) for pgid in pgids), timeout=2.5)
        assert time.monotonic() - start < 2.5
    finally:
        host.close()


def test_sigint_to_the_hosts_group_reaches_only_the_host():
    """Workers are outside the host's group: a group SIGINT interrupts the host alone."""
    host = _Host("sigint", own_group=True)
    try:
        state = host.line()
        assert state["ready"]
        pids = state["pids"]
        os.killpg(host.proc.pid, signal.SIGINT)  # the whole group, as a terminal would
        report = host.line()
        assert report["interrupted"] is True
        assert report["spin_running"] is True  # the sync body never saw the SIGINT
        assert report["idle_answers"] == 3
        done = host.line()
        assert done["cleaned"] is True and done["workers"] == []
        assert host.proc.wait(timeout=10) == 0
        assert all(not _pid_alive(pid) for pid in pids)
    finally:
        host.close()


def test_host_exit_without_cleanup_neither_hangs_nor_leaks():
    """Not daemon processes, so only the pool's atexit hook keeps the interpreter from joining them."""
    host = _Host("exit")
    try:
        state = host.line()
        pids = state["pids"]
        start = time.monotonic()
        assert host.proc.wait(timeout=10) == 0
        assert time.monotonic() - start < 3.0
        assert _wait(lambda: all(_dead(pid) for pid in pids), timeout=2.0)
    finally:
        host.close()


# --- SIGINT in the worker ------------------------------------------------------


def test_sigint_interrupts_a_sync_busy_body_and_the_worker_serves_on(pool):
    w = pool.launch()
    pgid = pool.status(w).pgid
    outcome: list[object] = []

    def call() -> None:
        try:
            outcome.append(pool.teleport(w, Spin(30)))
        except BaseException as exc:
            outcome.append(exc)

    t = threading.Thread(target=call, daemon=True)
    t.start()
    time.sleep(0.3)  # the body is spinning and holds the worker's loop
    start = time.monotonic()
    os.killpg(pgid, signal.SIGINT)
    t.join(timeout=5)
    assert not t.is_alive()
    assert time.monotonic() - start < 1.0
    assert isinstance(outcome[0], Interrupted)
    assert outcome[0].wid == w
    # The worker is still there and serves the next request.
    assert pool.status(w).state != "exited"
    assert pool.teleport(w, nu.Add(1, 2)) == 3


def test_sigint_ends_a_dispatched_sync_body(pool):
    w = pool.launch()
    pool.dispatch(w, Spin(30))
    assert bool(pool.status(w).jobs)
    time.sleep(0.2)
    os.killpg(pool.status(w).pgid, signal.SIGINT)
    assert _wait(lambda: not bool(pool.status(w).jobs), timeout=2.0)
    assert pool.teleport(w, nu.Add(2, 2)) == 4


def test_sigint_cancels_an_idle_workers_async_body_cooperatively(pool):
    """No sync body on the main thread: the jobs are cancelled instead, and the worker stays."""
    w = pool.launch()
    pool.dispatch(w, RESIDENT)
    assert bool(pool.status(w).jobs)
    os.killpg(pool.status(w).pgid, signal.SIGINT)
    assert _wait(lambda: not bool(pool.status(w).jobs), timeout=2.0)
    assert pool.status(w).state != "exited"
    assert pool.teleport(w, nu.Add(3, 4)) == 7


def test_sigint_on_a_quiet_worker_is_harmless(pool):
    w = pool.launch()
    os.killpg(pool.status(w).pgid, signal.SIGINT)
    time.sleep(0.1)
    assert pool.status(w).state != "exited"
    assert pool.teleport(w, nu.Add(5, 5)) == 10


def test_sigint_with_a_busy_body_ends_the_other_jobs_too(pool):
    """One interrupt, one blast radius: the busy body and the resident one both end."""
    w = pool.launch()
    pool.dispatch(w, RESIDENT)
    outcome: list[object] = []

    def call() -> None:
        try:
            outcome.append(pool.teleport(w, Spin(30)))
        except BaseException as exc:
            outcome.append(exc)

    t = threading.Thread(target=call, daemon=True)
    t.start()
    time.sleep(0.3)
    os.killpg(pool.status(w).pgid, signal.SIGINT)
    t.join(timeout=5)
    assert isinstance(outcome[0], Interrupted)
    assert _wait(lambda: not bool(pool.status(w).jobs), timeout=2.0)
    assert pool.teleport(w, nu.Add(1, 1)) == 2


# --- SIGTERM in the worker ---------------------------------------------------


def test_sigterm_runs_init_teardown_and_the_bodys_finally(tmp_path):
    torn = tmp_path / "torn"
    fin = tmp_path / "finally"
    pool = WorkerPool(name="nu-test-term", init=nu.Provide(Touch, {"path": str(torn)}))
    pool.setup(None)
    try:
        w = pool.launch()
        pool.dispatch(w, Guarded(str(fin), 30))  # sync sleep: holds the loop
        time.sleep(0.2)
        os.kill(pool.status(w).pid, signal.SIGTERM)
        assert pool.wait(w, timeout=5.0).exitcode == TERMED
        assert fin.read_text() == "finally ran"
        assert torn.read_text() == "torn down"
        # A SIGTERM the pool did not send is a loss, not a stop.
        assert (pool.status(w).exitcode, pool.status(w).cause) == (TERMED, "crashed")
    finally:
        pool.cleanup()


def test_kill_skips_the_teardown(tmp_path):
    """Kill is SIGKILL to the group: nothing in the worker runs, ``Stop`` is the polite one."""
    torn = tmp_path / "torn"
    pool = WorkerPool(name="nu-test-killterm", init=nu.Provide(Touch, {"path": str(torn)}))
    pool.setup(None)
    try:
        w = pool.launch()
        pool.kill(w)
        assert not torn.exists()
        assert (pool.status(w).exitcode, pool.status(w).cause) == (-signal.SIGKILL, "killed")
    finally:
        pool.cleanup()


def test_cause_tells_the_pools_own_kill_from_an_outside_signal():
    """``killed`` only when the pool sent the signal; any other signal reads ``crashed``."""
    pool = WorkerPool(name="nu-test-cause")
    pool.setup(None)
    try:
        own, sigkilled, sigtermed = pool.launch(), pool.launch(), pool.launch()
        pool.kill(own)
        os.kill(pool.status(sigkilled).pid, signal.SIGKILL)
        os.kill(pool.status(sigtermed).pid, signal.SIGTERM)
        for w in (sigkilled, sigtermed):
            assert pool.wait(w, timeout=5.0).state == "exited"
        assert (pool.status(own).exitcode, pool.status(own).cause) == (-signal.SIGKILL, "killed")
        assert (pool.status(sigkilled).exitcode, pool.status(sigkilled).cause) == (
            -signal.SIGKILL,
            "crashed",
        )
        assert pool.status(sigtermed).exitcode in (TERMED, -signal.SIGTERM)
        assert pool.status(sigtermed).cause == "crashed"
        for w, cause in ((own, "killed"), (sigkilled, "crashed")):
            with pytest.raises(WorkerGone) as gone:
                pool.teleport(w, nu.Add(1, 1))
            assert gone.value.cause == cause
    finally:
        pool.cleanup()


def test_sigterm_outside_a_body_winds_the_worker_down_in_order(tmp_path):
    """No body on the main thread (idle in select, or a resident async body): still a clean 143."""
    marks = [tmp_path / "idle", tmp_path / "resident"]
    pool = WorkerPool(name="nu-test-termidle")
    pool.setup(None)
    try:
        idle = pool.launch(nu.Provide(Touch, {"path": str(marks[0])}))
        resident = pool.launch(nu.Provide(Touch, {"path": str(marks[1])}))
        pool.dispatch(resident, RESIDENT)
        for w in (idle, resident):
            os.kill(pool.status(w).pid, signal.SIGTERM)
            assert pool.wait(w, timeout=5.0).exitcode == TERMED
        for mark in marks:
            assert mark.read_text() == "torn down"
    finally:
        pool.cleanup()


def test_a_second_sigterm_does_not_cut_the_teardown(tmp_path):
    """The worker's SIGTERM is one-shot: repeats land during the teardown and are ignored."""
    mark = tmp_path / "torn"
    pool = WorkerPool(
        name="nu-test-twoterm",
        init=nu.Provide(SlowTouch, {"path": str(mark), "seconds": 0.4}),
    )
    pool.setup(None)
    try:
        w = pool.launch()
        pid = pool.status(w).pid
        for _ in range(3):
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
        assert pool.wait(w, timeout=5.0).exitcode == TERMED
        assert mark.read_text() == "torn down"
    finally:
        pool.cleanup()


def test_cleanup_lets_every_worker_finish_init_teardown(tmp_path):
    """The close's stop frame lets every teardown run in full, in parallel; each exits 0."""
    for round_ in range(3):
        pool = WorkerPool(name="nu-test-close-teardown")
        pool.setup(None)
        marks = []
        for i, seconds in enumerate((0.6, 0.2, 0.2)):
            mark = tmp_path / f"r{round_}-w{i}"
            marks.append(mark)
            pool.launch(nu.Provide(SlowTouch, {"path": str(mark), "seconds": seconds}))
        ids = pool.workers()
        start = time.monotonic()
        pool.cleanup()
        assert 0.6 <= time.monotonic() - start < 1.5  # the slowest teardown, not their sum
        for mark in marks:
            assert mark.read_text() == "torn down"
        assert [pool.status(w).exitcode for w in ids] == [0] * 3
        assert {pool.status(w).cause for w in ids} == {"stopped"}


async def test_every_exit_code_is_recorded_across_many_cleanups():
    """Nothing polls a process another thread is reaping, so no code is lost to ECHILD."""
    codes: list[int | None] = []
    for _ in range(30):
        pool = WorkerPool(name="nu-test-codes")
        pool.setup(None)
        ids = await asyncio.gather(pool.alaunch(), pool.alaunch())
        pool.cleanup()
        codes.extend(pool.status(w).exitcode for w in ids)
    assert codes == [0] * 60


# --- the group ---------------------------------------------------------------


def test_kill_takes_a_bodys_subprocess_with_it(pool):
    w = pool.launch()
    sleeper = pool.teleport(w, Sleeper(600))
    assert _pid_alive(sleeper)
    assert os.getpgid(sleeper) == pool.status(w).pgid
    pool.kill(w)
    assert _wait(lambda: _dead(sleeper), timeout=2.0)


def test_cleanup_takes_every_groups_subprocesses_with_it():
    pool = WorkerPool(name="nu-test-groups")
    pool.setup(None)
    ids = [pool.launch() for _ in range(2)]
    sleepers = [pool.teleport(w, Sleeper(600)) for w in ids]
    pgids = [pool.status(w).pgid for w in ids]
    pool.cleanup()
    assert _wait(lambda: all(_dead(pid) for pid in sleepers), timeout=2.0)
    assert _wait(lambda: not any(_group_alive(pgid) for pgid in pgids), timeout=2.0)


def test_signals_go_to_the_pid_alone_until_the_group_is_known(pool, monkeypatch):
    """Before ``ready`` there is no group to trust, and the host's own group is never it."""
    w = pool.launch()
    handle = pool._workers[w]
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(resources.os, "kill", lambda pid, sig: calls.append(("kill", pid)))
    monkeypatch.setattr(resources.os, "killpg", lambda pgid, sig: calls.append(("killpg", pgid)))

    handle._signal(0)
    assert calls == [("killpg", handle.pid)]  # ready came: the group

    handle.pgid = None  # as before ready
    handle._signal(0)
    assert calls[-1] == ("kill", handle.pid)

    handle.pgid = os.getpgrp()  # the child failed to leave our group
    handle._signal(0)
    assert calls[-1] == ("kill", handle.pid)
    handle.pgid = handle.pid


def test_a_crash_during_init_still_sweeps_the_group(tmp_path):
    """The group is reported before init runs, so a subprocess init started dies with the worker."""
    pidfile = tmp_path / "sleeper"
    pool = WorkerPool(name="nu-test-initcrash")
    pool.setup(None)
    try:
        with pytest.raises(WorkerGone):
            pool.launch(nu.Provide(CrashInInit, {"path": str(pidfile), "code": 3}))
        sleeper = int(pidfile.read_text())
        assert _wait(lambda: _dead(sleeper), timeout=2.0)
        assert pool.workers() == []
        assert (pool.status(0).exitcode, pool.status(0).cause) == (3, "init_failed")
    finally:
        pool.cleanup()


def test_a_shell_child_does_not_hold_the_workers_pipe_open(pool, tmp_path):
    """Inherited descriptors are closed on exec: a crash is seen even with a shell child alive."""
    pidfile = tmp_path / "sleeper"
    w = pool.launch()
    pool.teleport(w, Shell(f"/bin/sleep 600 & echo $! > {pidfile}"))
    sleeper = int(pidfile.read_text())
    assert _pid_alive(sleeper)
    with pytest.raises(WorkerGone) as gone:
        pool.teleport(w, Die(3))
    assert (gone.value.cause, gone.value.exitcode) == ("crashed", 3)
    assert pool.wait(w, timeout=4.0).exitcode == 3
    assert _wait(lambda: _dead(sleeper), timeout=2.0)


def test_a_body_can_use_multiprocessing(pool):
    """Workers are not daemon processes, so a body may spawn children of its own."""
    w = pool.launch()
    assert pool._workers[w].proc.daemon is False
    pid, pgid = pool.teleport(w, NestedSpawn())
    assert pid != pool.status(w).pid
    assert pgid == pool.status(w).pgid  # in the worker's group, where every killpg reaches it
    assert _wait(lambda: _dead(pid), timeout=2.0)


# --- identity ------------------------------------------------------------------


def test_pid_pgid_and_name_are_readable_alive_and_after_exit(pool):
    before = time.time()
    w = pool.launch()
    status = pool.status(w)
    assert isinstance(status, WorkerStatus)
    assert status.wid == w
    assert status.pid == pool._workers[w].proc.pid
    assert status.pgid == status.pid == os.getpgid(status.pid)
    assert status.pgid != os.getpgrp()
    assert status.name == f"nu:{pool.name}-{w}"
    assert before <= status.started_at <= time.time()
    assert (status.state, status.exitcode, status.cause) == ("idle", None, None)

    pool.kill(w)
    assert w not in pool.workers()
    after = pool.status(w)
    assert after.pid == status.pid and after.pgid == status.pgid and after.name == status.name
    assert after.started_at == status.started_at
    assert (after.state, after.exitcode, after.cause) == ("exited", -signal.SIGKILL, "killed")
    with pytest.raises(UnknownWorker):
        pool.status(999)


def test_name_is_visible_in_ps(pool):
    w = pool.launch()
    pid, name = pool.status(w).pid, pool.status(w).name
    if sys.platform.startswith("linux"):
        assert Path(f"/proc/{pid}/comm").read_text().strip() == name[:15]
    try:
        import setproctitle  # noqa: F401
    except ImportError:
        if not sys.platform.startswith("linux"):
            pytest.skip("setproctitle not installed: no way to title a process on mac")
        return
    command = subprocess.run(  # noqa: S603
        ["/bin/ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True, check=False
    ).stdout.strip()
    assert command.startswith(name)


def test_non_spawn_start_methods_are_refused():
    with pytest.raises(ValueError, match="spawn"):
        WorkerPool(start_method="fork")
    with pytest.raises(ValueError, match="spawn"):
        WorkerPool(start_method="forkserver")
