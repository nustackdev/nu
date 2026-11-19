"""Lock, Hold and FsHeld: in this process, against another process, sync and async."""

from __future__ import annotations

import errno
import fcntl
import json
import os
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

import pytest

import nu
import nustd.fs.fabric as fabric_mod
from nu.lang import wire
from nustd import fs


data = fs.FsRef("data")
lock_file = data / "locks" / "job.lock"


def on(root, body, **kwargs):
    """``body`` run with ``root`` mounted under the ``data`` tag."""
    return fs.mount(root, tag="data", body=body, **kwargs)


# A process holding the lock on argv[1]; argv[2] "record" writes a holder
# record, "bare" leaves the file as it is. Holds until its stdin closes.
HOLDER = r"""
import fcntl, json, os, socket, sys, time
fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o644)
fcntl.lockf(fd, fcntl.LOCK_EX)
if sys.argv[2] == "record":
    os.ftruncate(fd, 0)
    record = {"host": socket.gethostname(), "pid": os.getpid(), "what": "other", "taken_at": time.time()}
    os.write(fd, (json.dumps(record) + "\n").encode())
print("ready", flush=True)
sys.stdin.readline()
"""


@contextmanager
def held_elsewhere(path, *, record=True):
    """Another process holding the lock on ``path`` for the with block."""
    path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(  # noqa: S603 - our own interpreter and script
        [sys.executable, "-c", HOLDER, str(path), "record" if record else "bare"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "ready"
        yield proc
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
        proc.wait(timeout=10)


def lock_path(root):
    return root / "locks" / "job.lock"


@pytest.fixture(autouse=True)
def _no_locks_left():
    yield
    assert fabric_mod.HELD == {}


# --- Lock in this process ---------------------------------------------------


def test_lock_runs_the_body_and_writes_the_record(go, root):
    got = go(on(root, fs.Lock(lock_file, "indexer", body=lock_file.held())))
    assert got["pid"] == os.getpid()
    assert got["host"] == socket.gethostname()
    assert got["what"] == "indexer"
    assert got["taken_at"] == pytest.approx(time.time(), abs=60)
    # Released, the file stays and names its last holder.
    assert json.loads(lock_path(root).read_text())["what"] == "indexer"
    assert go(on(root, lock_file.held())) is None


def test_lock_forwards_the_body_value_and_a_stream(go, root):
    assert go(on(root, fs.Lock(lock_file, body=data.read_text("a.txt")))) == "hello\nworld\n"
    lines = go(on(root, fs.Lock(lock_file, body=nu.Collect(data.lines("a.txt")))))
    assert list(lines) == ["hello", "world"]


def test_lock_inside_a_with(go, root):
    term = nu.With(fs.Lock(lock_file, "w"), body=lock_file.held())
    assert go(on(root, term))["what"] == "w"


def test_second_take_in_this_process_is_refused(go, root):
    inner = fs.Lock(lock_file, "inner", body=data.read_text("a.txt"))
    with pytest.raises(fs.FsLocked, match="this process") as info:
        go(on(root, fs.Lock(lock_file, "outer", body=inner)))
    assert info.value.holder["pid"] == os.getpid()
    assert info.value.holder["what"] == "outer"


def test_second_take_in_this_process_waits_then_refuses(go, root):
    inner = fs.Lock(lock_file, wait=0.2, body=data.read_text("a.txt"))
    started = time.monotonic()
    with pytest.raises(fs.FsLocked):
        go(on(root, fs.Lock(lock_file, body=inner)))
    assert time.monotonic() - started >= 0.2


def test_a_raising_body_releases(go, root):
    with pytest.raises(FileNotFoundError):
        go(on(root, fs.Lock(lock_file, body=data.read_text("nope"))))
    assert go(on(root, lock_file.held())) is None


def test_parallel_takes_in_one_process_wait_their_turn(go, root):
    def arm(name):
        return fs.Lock(lock_file, name, wait=5, body=(data / name).write_text(name))

    go(on(root, nu.Parallel(arm("one"), arm("two"))))
    assert (root / "one").read_text() == "one"
    assert (root / "two").read_text() == "two"


def test_lock_path_can_be_a_term(go, root):
    f = data / nu.Literal("dyn") / "x.lock"
    assert go(on(root, fs.Lock(f, "dyn", body=f.held())))["what"] == "dyn"
    assert (root / "dyn" / "x.lock").exists()


def test_lock_refuses_a_bad_file_or_wait():
    with pytest.raises(TypeError, match="FileRef"):
        fs.Lock("job.lock")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="wait"):
        fs.Lock(lock_file, wait=-1)
    with pytest.raises(TypeError, match="FileRef"):
        fs.Hold(data, "x")  # type: ignore[arg-type]


def test_lock_on_a_readonly_mount(go, root):
    with pytest.raises(fs.FsReadOnly):
        go(on(root, fs.Lock(lock_file, body=data.read_text("a.txt")), readonly=True))


def test_lock_escape(go, root):
    with pytest.raises(fs.FsEscape):
        go(on(root, fs.Lock(data / ".." / "x.lock", body=data.read_text("a.txt"))))


def test_lock_unbound_hints_the_tag(go):
    with pytest.raises(RuntimeError, match="tag='data'"):
        go(fs.Lock(lock_file, body=nu.Literal(1)))


def test_a_file_system_that_cannot_lock_warns_and_goes_on(go, root, monkeypatch):
    def no_locks(fd, op, *args):
        raise OSError(errno.ENOLCK, "no locks available")

    monkeypatch.setattr(fcntl, "lockf", no_locks)
    with pytest.warns(fs.FsLockWarning, match="going on without"):
        got = go(on(root, fs.Lock(lock_file, body=data.read_text("a.txt"))))
    assert got == "hello\nworld\n"


def test_lock_travels_on_the_wire(go, root):
    app = on(root, fs.Lock(lock_file, "wire", wait=1, body=lock_file.held()))
    assert go(wire.loads(wire.dumps(app)))["what"] == "wire"


# --- Lock against another process -------------------------------------------


def test_lock_held_by_another_process_is_refused(go, root):
    with held_elsewhere(lock_path(root)) as proc:
        with pytest.raises(fs.FsLocked, match=f"pid {proc.pid}") as info:
            go(on(root, fs.Lock(lock_file, body=data.read_text("a.txt"))))
        assert info.value.holder["pid"] == proc.pid
        assert info.value.holder["what"] == "other"
        assert go(on(root, lock_file.held()))["pid"] == proc.pid
    assert go(on(root, lock_file.held())) is None


def test_a_holder_without_a_record(go, root):
    with held_elsewhere(lock_path(root), record=False):
        with pytest.raises(fs.FsLocked, match="left no record") as info:
            go(on(root, fs.Lock(lock_file, body=data.read_text("a.txt"))))
        assert info.value.holder == {}
        assert go(on(root, lock_file.held())) == {}


def test_lock_waits_for_another_process_to_release(go, root):
    with held_elsewhere(lock_path(root)) as proc:
        assert proc.stdin is not None
        threading.Timer(0.3, proc.stdin.close).start()
        got = go(on(root, fs.Lock(lock_file, "mine", wait=True, body=lock_file.held())))
    assert got["pid"] == os.getpid()


def test_lock_wait_runs_out_against_another_process(go, root):
    with held_elsewhere(lock_path(root)):
        started = time.monotonic()
        with pytest.raises(fs.FsLocked):
            go(on(root, fs.Lock(lock_file, wait=0.2, body=data.read_text("a.txt"))))
        assert time.monotonic() - started >= 0.2


def test_a_lock_this_process_holds_is_refused_to_another(root):
    script = (
        "import fcntl, os, sys\n"
        "fd = os.open(sys.argv[1], os.O_RDWR)\n"
        "try:\n"
        "    fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "except OSError:\n"
        "    print('refused')\n"
        "else:\n"
        "    print('taken')\n"
    )

    def probe():
        out = subprocess.run(  # noqa: S603 - our own interpreter and script
            [sys.executable, "-c", script, str(lock_path(root))],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()

    seen = []
    with _held_by_us(root):
        seen.append(probe())
    seen.append(probe())
    assert seen == ["refused", "taken"]


@contextmanager
def _held_by_us(root):
    """The lock on ``root/locks/job.lock`` taken by this process, through the fabric."""
    mount = fabric_mod.FsFabric(path=root)
    mount.setup(None)  # type: ignore[arg-type]
    full, fd = mount.lock("locks/job.lock", "us")
    try:
        # Reading the record through FsHeld keeps the lock.
        assert mount.held("locks/job.lock")["what"] == "us"
        yield
    finally:
        mount.unlock(full, fd)
        mount.cleanup()


def test_remove_if_holds_keeps_a_held_file(go, root):
    text = None
    with held_elsewhere(lock_path(root)):
        text = lock_path(root).read_text()
        go(on(root, data.remove_if_holds("locks/job.lock", text)))
        assert lock_path(root).exists()
    go(on(root, data.remove_if_holds("locks/job.lock", text)))
    assert not lock_path(root).exists()


# --- FsHeld -----------------------------------------------------------------


def test_held_of_missing_and_free_files(go, root):
    assert go(on(root, data.held("nope.lock"))) is None
    assert go(on(root, data.held("a.txt"))) is None


def test_held_on_a_readonly_mount_probes(go, root):
    with held_elsewhere(lock_path(root)) as proc:
        got = go(on(root, lock_file.held(), readonly=True))
    assert got["pid"] == proc.pid


# --- Hold -------------------------------------------------------------------


def test_hold_writes_for_the_body_and_removes_after(go, root):
    owner = data / "run" / "owner"
    got = go(on(root, fs.Hold(owner, "red 1", body=owner.read_text())))
    assert got == "red 1"
    assert not (root / "run" / "owner").exists()


def test_hold_keeps_a_file_someone_else_took(go, root):
    owner = data / "owner"
    go(on(root, fs.Hold(owner, "red 1", body=owner.write_text("blue 2"))))
    assert (root / "owner").read_text() == "blue 2"


def test_hold_removes_after_a_raising_body(go, root):
    owner = data / "owner"
    with pytest.raises(FileNotFoundError):
        go(on(root, fs.Hold(owner, "red 1", body=data.read_text("nope"))))
    assert not (root / "owner").exists()


def test_hold_refuses_bytes_and_readonly(go, root):
    with pytest.raises(TypeError, match="str"):
        go(on(root, fs.Hold(data / "owner", b"x", body=nu.Literal(1))))  # type: ignore[arg-type]
    with pytest.raises(fs.FsReadOnly):
        go(on(root, fs.Hold(data / "owner", "x", body=nu.Literal(1)), readonly=True))
    assert not (root / "owner").exists()


def test_lock_and_hold_together(go, root):
    owner = data / "owner"
    term = nu.With(
        fs.Lock(lock_file, "serve"),
        fs.Hold(owner, "red 1"),
        body=owner.read_text(),
    )
    assert go(on(root, term)) == "red 1"
    assert not (root / "owner").exists()


# --- the package example ----------------------------------------------------


def test_the_package_example_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes = data / "notes"
    save = fs.mount(
        "./data",
        tag="data",
        body=fs.Lock(
            data / "notes.lock",
            "notes",
            wait=5,
            body=(notes / "today.md").write_text("# today\n"),
        ),
    )
    nu.run(save)
    listing = nu.Collect(notes.list(pattern="*.md"))
    entries = nu.run(fs.mount("./data", tag="data", body=listing))[0]
    assert [e["name"] for e in entries] == ["today.md"]
