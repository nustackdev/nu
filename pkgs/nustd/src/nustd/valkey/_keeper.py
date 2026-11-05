"""The keeper: the process a private ``valkey-server`` runs under.

Run as a script by ``ValkeyServer``, never imported by it: ``python -I -S
_keeper.py OWNER GRACE WATCH SOCKET BINARY CONF``. Stdlib only, and few
imports: isolated mode, no ``site`` and no ``pathlib`` keep its start cheap.

The keeper spawns the server as its own child, prints the server's pid on
stdout, then waits. It stops the server, SIGTERM then SIGKILL after
``GRACE`` seconds, and exits once it has reaped it, when:

- the owner writes ``stop`` on stdin, a pipe only the owner holds the write
  end of (its cleanup);
- that pipe reads EOF, or the keeper's parent is no longer ``OWNER``: the
  owner died by any means, SIGKILL included, even with a forked child of the
  owner still holding the write end (``WATCH`` 0 ignores both);
- the keeper gets SIGTERM, SIGINT or SIGHUP.

Whatever signal mask the owner's thread had, the keeper clears its own and
starts the server with none blocked: a server spawned with SIGTERM blocked
ignores every stop request, which is how servers leaked from mp_pool workers.

The server is the keeper's child, so the pid it signals cannot have been
reused: it is not reaped until the keeper waits on it. If the server exits
on its own, the keeper exits with its code. A unix socket nothing answers on
any more is removed on the way out, so ``/tmp`` keeps no stale ``nu-vk-*``.
"""

from __future__ import annotations

import os
import select
import signal
import sys
import time


_STOP_SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
# How often the keeper checks it still has its owner, between wakeups.
_WATCH_EVERY = 0.25


def _reaped(pid: int) -> int | None:
    """The server's exit code once reaped, else None while it runs."""
    try:
        done, status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return 0
    if not done:
        return None
    return os.waitstatus_to_exitcode(status)


def _stop(pid: int, grace: float) -> int:
    """SIGTERM the server, SIGKILL it after ``grace``, reap it. Returns its exit code."""
    code = _reaped(pid)
    if code is not None:
        return code
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        code = _reaped(pid)
        if code is not None:
            return code
        time.sleep(0.005)
    os.kill(pid, signal.SIGKILL)
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def _drop_stale_socket(path: str) -> None:
    """Remove ``path`` if it is a socket nobody listens on any more."""
    import socket  # only on the way out: keeps the keeper's start cheap

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        try:
            sock.connect(path)
        except FileNotFoundError:
            return
        except OSError:
            try:
                os.unlink(path)  # noqa: PTH108 - pathlib costs the keeper's start
            except FileNotFoundError:
                pass


def main(argv: list[str]) -> int:
    owner, grace, watch, sock_path = int(argv[1]), float(argv[2]), argv[3] == "1", argv[4]
    command = argv[5:]

    stops: list[int] = []
    for sig in _STOP_SIGNALS:
        signal.signal(sig, lambda signum, _frame: stops.append(signum))
    # A wakeup fd turns every signal (SIGCHLD included) into a readable byte,
    # so the wait below never sleeps through a stop or the server's exit.
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_w, False)
    signal.set_wakeup_fd(wake_w)
    signal.signal(signal.SIGCHLD, lambda _signum, _frame: None)
    # A signal mask survives fork and exec. Spawned from a thread that blocks
    # SIGTERM and SIGINT (mp_pool's quiet threads do), the keeper and the
    # server would both hold every stop request pending forever. Clear it,
    # handlers first so a pending stop lands on them.
    signal.pthread_sigmask(signal.SIG_SETMASK, ())

    devnull = os.open(os.devnull, os.O_RDWR)
    pid = os.posix_spawn(
        command[0],
        command,
        os.environ,
        file_actions=[
            (os.POSIX_SPAWN_DUP2, devnull, 0),
            (os.POSIX_SPAWN_DUP2, devnull, 1),
        ],
        # The server starts with no signal blocked and default dispositions,
        # whatever its owner's thread had, so a SIGTERM always stops it.
        setsigmask=(),
        setsigdef=(signal.SIGPIPE, signal.SIGXFSZ, signal.SIGTERM, signal.SIGINT, signal.SIGHUP),
    )
    sys.stdout.write(f"{pid}\n")
    sys.stdout.flush()
    os.dup2(devnull, 1)  # let go of the owner's pipe

    watching = [0, wake_r]
    code: int | None = None
    while not stops:
        ready, _, _ = select.select(watching, [], [], _WATCH_EVERY)
        if wake_r in ready:
            os.read(wake_r, 512)
        if 0 in ready:
            data = os.read(0, 512)
            if b"stop" in data:
                break
            if not data:
                if watch:
                    break
                watching.remove(0)
        code = _reaped(pid)
        if code is not None:
            break
        if watch and os.getppid() != owner:
            break
    if code is None:
        code = _stop(pid, grace)
    _drop_stale_socket(sock_path)
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
