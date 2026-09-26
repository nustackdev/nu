"""Resource and bracket tests for ``nustd.valkey``. Real servers, no mocks."""

from __future__ import annotations

import os
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import textwrap
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


OWNER = textwrap.dedent(
    """
    import sys, time
    from nustd.valkey import ValkeyServer
    s = ValkeyServer(data_dir=sys.argv[1])
    s.setup(None)
    print(s.pid, s._watchdog.pid, flush=True)
    time.sleep(600)
    """,
)


def _spawn_owner(data_dir: str) -> tuple[subprocess.Popen, int, int]:
    owner = subprocess.Popen(  # noqa: S603
        [sys.executable, "-c", OWNER, data_dir],
        stdout=subprocess.PIPE,
        text=True,
    )
    server_pid, dog_pid = (int(x) for x in owner.stdout.readline().split())
    return owner, server_pid, dog_pid


def _kill(proc: subprocess.Popen) -> None:
    proc.kill()
    proc.wait()
    proc.stdout.close()


def test_the_watchdog_stops_the_server_when_the_owner_is_sigkilled(data_dir):
    owner, server_pid, dog_pid = _spawn_owner(data_dir)
    _kill(owner)
    assert _wait_gone(server_pid)
    assert _wait_gone(dog_pid)
    assert not Path(socket_path_for(data_dir)).exists()


def test_an_orphan_is_reaped_at_the_next_start(data_dir):
    """Owner and watchdog both SIGKILLed: the server is left running, then reaped."""
    owner, server_pid, dog_pid = _spawn_owner(data_dir)
    os.kill(dog_pid, signal.SIGKILL)
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
    owner, server_pid, _ = _spawn_owner(data_dir)
    try:
        with pytest.raises(ValkeyInUse):
            ValkeyServer(data_dir=data_dir).setup(None)
        assert _pid_alive(server_pid)
    finally:
        _kill(owner)
    assert _wait_gone(server_pid)


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
