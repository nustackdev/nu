"""Resource and bracket tests for ``nustd.valkey``. Real servers, no mocks."""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from pathlib import Path

import pytest

import nu
from nustd.valkey import (
    Ping,
    Url,
    ValkeyInUse,
    ValkeyRef,
    ValkeyServer,
    server,
    socket_path_for,
    url_for,
)
from nustd.valkey.resources import aping


pytestmark = pytest.mark.slow


# --- helpers ----------------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # A reaped-by-nobody zombie still answers kill(0); ps knows better.
    out = subprocess.run(  # noqa: S603
        ["ps", "-p", str(pid), "-o", "stat="],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(out.stdout.strip()) and not out.stdout.strip().startswith("Z")


def _wait_gone(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def data_dir():
    # Short and outside pytest's tmp_path on purpose: the socket lives in /tmp
    # regardless, and a stray server is easier to spot by this prefix.
    d = tempfile.mkdtemp(prefix="nu-vk-test-")
    try:
        yield d
    finally:
        sock = socket_path_for(d)
        if Path(sock).exists():
            Path(sock).unlink()
        shutil.rmtree(d, ignore_errors=True)


# --- addressing ---------------------------------------------------------------


def test_socket_path_is_short_and_deterministic_for_a_very_long_dir(tmp_path):
    deep = tmp_path.joinpath(*(["a_rather_long_directory_name"] * 12))
    assert len(str(deep)) > 300
    path = socket_path_for(deep)
    assert len(path) < 104
    assert path == socket_path_for(str(deep))
    assert path == socket_path_for(deep / "x" / "..")
    assert path != socket_path_for(deep / "other")
    assert url_for(deep) == f"unix://{path}"


def test_url_for_takes_an_explicit_socket():
    assert url_for("/anything", socket_path="/tmp/mine.sock") == "unix:///tmp/mine.sock"


def test_a_very_long_data_dir_starts_a_server(data_dir):
    deep = Path(data_dir).joinpath(*(["a_rather_long_directory_name"] * 6))
    srv = ValkeyServer(data_dir=deep)
    srv.setup(None)
    try:
        assert srv.ping()
        assert srv.url == url_for(deep)
    finally:
        srv.cleanup()


# --- ping -------------------------------------------------------------------


async def _silent_server(path: str) -> tuple[asyncio.Server, asyncio.Event]:
    """A unix socket server that reads and never answers; the event is set when the client hangs up."""
    hung_up = asyncio.Event()

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while await reader.read(64):
            pass
        hung_up.set()
        writer.close()

    return await asyncio.start_unix_server(handle, path), hung_up


async def test_aping_times_out_on_a_silent_server_and_hangs_up(data_dir):
    srv, hung_up = await _silent_server(socket_path_for(data_dir))
    async with srv:
        assert await aping(socket_path_for(data_dir), timeout=0.05) is False
        await asyncio.wait_for(hung_up.wait(), 1.0)


async def test_aping_cancelled_raises_the_cancel_and_hangs_up(data_dir):
    srv, hung_up = await _silent_server(socket_path_for(data_dir))
    async with srv:
        task = asyncio.ensure_future(aping(socket_path_for(data_dir), timeout=5.0))
        await asyncio.sleep(0.05)
        task.cancel()
        await asyncio.wait({task})
        assert task.cancelled()
        await asyncio.wait_for(hung_up.wait(), 1.0)


# --- lifecycle --------------------------------------------------------------


def test_start_ping_stop(data_dir):
    srv = ValkeyServer(data_dir=data_dir)
    srv.setup(None)
    pid = srv.pid
    try:
        assert srv.ping()
        assert Path(data_dir, "valkey.pid").read_text().strip() == str(pid)
        assert Path(data_dir, "valkey.log").stat().st_size > 0
        conf = Path(data_dir, "valkey.conf").read_text()
        assert "port 0" in conf
        assert 'save ""' in conf
        assert "appendonly no" in conf
    finally:
        srv.cleanup()
    assert _wait_gone(pid)
    assert not srv.ping()
    assert not Path(socket_path_for(data_dir)).exists()
    assert not Path(data_dir, "valkey.pid").exists()
    assert not Path(data_dir, "valkey.owner").exists()


def test_logfile_none_discards_the_log(data_dir):
    srv = ValkeyServer(data_dir=data_dir, logfile=None)
    srv.setup(None)
    try:
        assert srv.ping()
    finally:
        srv.cleanup()
    assert not Path(data_dir, "valkey.log").exists()


def test_explicit_socket_path(data_dir):
    sock = f"/tmp/nu-vk-test-{os.getpid()}.sock"
    srv = ValkeyServer(data_dir=data_dir, socket_path=sock)
    srv.setup(None)
    try:
        assert srv.url == url_for(data_dir, socket_path=sock)
        assert Path(sock).exists()
        assert srv.ping()
    finally:
        srv.cleanup()
    assert not Path(sock).exists()


def test_the_bracket_starts_answers_and_stops(data_dir):
    tree = nu.With(
        server(data_dir),
        body=nu.Dict.of(url=Url(), up=ValkeyRef().ping()),
    )
    value, _ = nu.run(tree)
    assert value == {"url": url_for(data_dir), "up": True}
    assert not Path(socket_path_for(data_dir)).exists()


async def test_the_bracket_starts_answers_and_stops_async(data_dir):
    tree = nu.With(
        server(data_dir),
        body=nu.Dict.of(url=ValkeyRef().url(), up=Ping()),
    )
    value, _ = await nu.arun(tree)
    assert value == {"url": url_for(data_dir), "up": True}
    assert not Path(socket_path_for(data_dir)).exists()


def test_reads_without_a_server_bound_say_so():
    with pytest.raises(RuntimeError, match="no ValkeyServer is bound"):
        nu.run(Url())


def test_the_same_dir_restarts_after_a_clean_stop(data_dir):
    for _ in range(3):
        srv = ValkeyServer(data_dir=data_dir)
        srv.setup(None)
        assert srv.ping()
        srv.cleanup()


# --- crashes ----------------------------------------------------------------
#
# Each test runs the owner as a real process and ends it the way a host ends
# in the wild, then checks no server outlives it. These are the leak paths
# found on a dev machine: a server left running with no owner and no keeper.


OWNER = textwrap.dedent(
    """
    import os, signal, sys, time
    import nu
    from nustd.valkey import ValkeyServer, server

    data_dir, mode = sys.argv[1], sys.argv[2]

    def report(s):
        print(s._server_pid, s._keeper.pid, flush=True)

    if mode == "bracket":
        # Ctrl-C reaches the owner while a nu bracket holds the server.
        import subprocess
        class Report:
            def setup(self, ctx):
                pid = open(os.path.join(data_dir, "valkey.pid")).read().strip()
                keeper = subprocess.run(
                    ["ps", "-o", "ppid=", "-p", pid], capture_output=True, text=True
                ).stdout.strip()
                print(pid, keeper, flush=True)
            async def asetup(self, ctx):
                self.setup(ctx)
        import asyncio
        asyncio.run(nu.arun(nu.With(server(data_dir), nu.Provide(Report, {}), body=nu.Park())))
        sys.exit(0)

    s = ValkeyServer(data_dir=data_dir)
    if mode == "masked":
        # spawned from a thread that blocks SIGINT and SIGTERM, as mp_pool's are
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    if mode == "interrupted-startup":
        def interrupted(deadline):
            report(s)
            raise KeyboardInterrupt
        s._ready_step = interrupted
        try:
            s.setup(None)
        except KeyboardInterrupt:
            pass
        time.sleep(600)
    s.setup(None)
    report(s)
    if mode == "killed-in-cleanup":
        # cleanup gets as far as waiting on the keeper, then the owner is killed
        s._keeper.wait = lambda timeout=None: time.sleep(600)
        signal.signal(signal.SIGUSR1, lambda *_: s.cleanup())
    if mode == "forked":
        # a fork child inherits the keeper pipe's write end and outlives us
        if os.fork() == 0:
            time.sleep(600)
            os._exit(0)
    time.sleep(600)
    """,
)


def _spawn_owner(data_dir: str, mode: str = "plain") -> tuple[subprocess.Popen, int, int]:
    owner = subprocess.Popen(  # noqa: S603
        [sys.executable, "-c", OWNER, data_dir, mode],
        stdout=subprocess.PIPE,
        text=True,
    )
    server_pid, keeper_pid = (int(x) for x in owner.stdout.readline().split())
    return owner, server_pid, keeper_pid


def _kill(proc: subprocess.Popen) -> None:
    proc.kill()
    proc.wait()
    proc.stdout.close()


def _assert_no_server_left(data_dir: str, server_pid: int, keeper_pid: int) -> None:
    try:
        assert _wait_gone(server_pid), "valkey-server outlived its owner"
        assert _wait_gone(keeper_pid)
        assert not Path(socket_path_for(data_dir)).exists(), "stale socket left in /tmp"
    finally:
        for pid in (server_pid, keeper_pid):
            if _pid_alive(pid):
                os.kill(pid, signal.SIGKILL)


def test_a_clean_stop_leaves_no_process(data_dir):
    srv = ValkeyServer(data_dir=data_dir)
    srv.setup(None)
    server_pid, keeper_pid = srv.pid, srv._keeper.pid
    srv.cleanup()
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_the_keeper_stops_the_server_when_the_owner_is_sigkilled(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir)
    _kill(owner)
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_the_server_stops_when_the_owner_is_sigtermed(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir)
    owner.terminate()
    owner.wait()
    owner.stdout.close()
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_ctrl_c_on_the_owner_stops_the_server_through_the_bracket(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir, "bracket")
    owner.send_signal(signal.SIGINT)
    try:
        owner.wait(timeout=10)
    finally:
        if owner.poll() is None:
            owner.kill()
        owner.stdout.close()
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_an_owner_killed_inside_cleanup_still_stops_the_server(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir, "killed-in-cleanup")
    owner.send_signal(signal.SIGUSR1)
    time.sleep(0.3)
    _kill(owner)
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_an_interrupted_startup_stops_the_server(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir, "interrupted-startup")
    try:
        # the owner lives on: the cleanup in setup alone has to stop it
        _assert_no_server_left(data_dir, server_pid, keeper_pid)
    finally:
        _kill(owner)


def test_the_server_stops_when_a_forked_child_outlives_the_owner(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir, "forked")
    children = subprocess.run(  # noqa: S603
        ["pgrep", "-P", str(owner.pid)],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    forks = [int(c) for c in children if int(c) not in (server_pid, keeper_pid)]
    try:
        _kill(owner)
        _assert_no_server_left(data_dir, server_pid, keeper_pid)
    finally:
        for pid in forks:
            if _pid_alive(pid):
                os.kill(pid, signal.SIGKILL)


def test_a_server_spawned_with_stop_signals_blocked_still_dies_with_its_owner(data_dir):
    """The leak seen in the wild: a blocked mask is inherited, SIGTERM is held forever."""
    owner, server_pid, keeper_pid = _spawn_owner(data_dir, "masked")
    _kill(owner)
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_a_server_spawned_with_stop_signals_blocked_stops_on_sigterm(data_dir):
    def blocked_setup(srv: ValkeyServer) -> None:
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        srv.setup(None)

    srv = ValkeyServer(data_dir=data_dir, grace=30.0)
    thread = threading.Thread(target=blocked_setup, args=(srv,))
    thread.start()
    thread.join()
    server_pid, keeper_pid = srv.pid, srv._keeper.pid
    t = time.monotonic()
    srv.cleanup()
    assert time.monotonic() - t < 5.0, "SIGTERM was ignored, cleanup fell back to SIGKILL"
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


def test_a_sigtermed_keeper_takes_the_server_down(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir)
    try:
        os.kill(keeper_pid, signal.SIGTERM)
        _assert_no_server_left(data_dir, server_pid, keeper_pid)
    finally:
        _kill(owner)


def test_a_crashed_server_leaves_no_socket(data_dir):
    srv = ValkeyServer(data_dir=data_dir)
    srv.setup(None)
    server_pid, keeper_pid = srv.pid, srv._keeper.pid
    try:
        os.kill(server_pid, signal.SIGKILL)
        _assert_no_server_left(data_dir, server_pid, keeper_pid)
    finally:
        srv.cleanup()


def test_an_orphan_is_reaped_at_the_next_start(data_dir):
    """Owner and keeper both SIGKILLed: the server is left running, then reaped."""
    owner, server_pid, keeper_pid = _spawn_owner(data_dir)
    os.kill(keeper_pid, signal.SIGKILL)
    _kill(owner)
    time.sleep(0.2)
    assert _pid_alive(server_pid), "the setup under test needs a real orphan"
    try:
        srv = ValkeyServer(data_dir=data_dir)
        srv.setup(None)
        try:
            assert srv.ping()
            assert srv.pid != server_pid
            assert _wait_gone(server_pid)
        finally:
            srv.cleanup()
    finally:
        if _pid_alive(server_pid):
            os.kill(server_pid, signal.SIGKILL)


def test_a_server_whose_owner_is_alive_is_not_taken(data_dir):
    owner, server_pid, keeper_pid = _spawn_owner(data_dir)
    try:
        with pytest.raises(ValkeyInUse):
            ValkeyServer(data_dir=data_dir).setup(None)
        assert _pid_alive(server_pid)
    finally:
        _kill(owner)
    _assert_no_server_left(data_dir, server_pid, keeper_pid)


# --- startup time -----------------------------------------------------------


def test_startup_is_fast(data_dir):
    """Sanity, not a benchmark: well under valkeylite's fixed 100ms poll."""
    times = []
    for _ in range(7):
        srv = ValkeyServer(data_dir=data_dir)
        t = time.perf_counter()
        srv.setup(None)
        times.append(time.perf_counter() - t)
        srv.cleanup()
    assert statistics.median(times) < 0.5
