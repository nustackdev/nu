"""``ValkeyServer``: the fabric that owns one private Valkey server process.

The server is the bundled ``valkey-server`` binary from the ``valkeylite``
wheel, spawned directly rather than through ``valkeylite.ValkeyServer``. That
class is fine for a test fixture and wrong for a host that has to come back
after a crash, so the parts that matter are done here instead:

- **One data dir, one server.** The dir holds ``valkey.conf``, ``valkey.pid``
  (the server's pid), ``valkey.owner`` (the pid of the process that owns it)
  and ``valkey.log``.
- **A known address before start.** The unix socket path is derived from the
  data dir by hash, ``/tmp/nu-vk-<hash>.sock``, so every process can build the
  URL on its own and it stays under macOS's 104 byte socket path limit
  however deep the dir is.
- **No orphans.** A small ``sh`` watchdog holds the read end of a pipe whose
  write end only the owner has. When the owner dies by any means, even
  SIGKILL, the pipe closes and the watchdog sends the server SIGTERM. If the
  watchdog is gone too, the next start in the same dir reaps the leftover
  server from its pid file.
- **Fast start.** Readiness is a raw RESP ``PING`` polled every millisecond
  or so, not every 100ms, so the bracket opens as soon as the server answers.
- **Own session.** Server and watchdog run in their own session, so a Ctrl-C
  on the terminal reaches the host, whose bracket then stops the server in
  order, instead of killing the server under whatever still talks to it.

``valkeylite`` is imported only to find the binary, at setup, so importing
this module (and building a URL in a worker) needs nothing installed.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = [
    "ValkeyInUse",
    "ValkeyServer",
    "ValkeyStartupError",
    "socket_path_for",
    "url_for",
]


_PID_FILE = "valkey.pid"
_OWNER_FILE = "valkey.owner"
_CONF_FILE = "valkey.conf"
_PING = b"*1\r\n$4\r\nPING\r\n"
_SHUTDOWN = b"*2\r\n$8\r\nSHUTDOWN\r\n$6\r\nNOSAVE\r\n"
# The watchdog: block on stdin (a pipe only the owner writes to), and once it
# reads EOF because the owner is gone, stop the server it was handed.
_WATCHDOG = 'read _; kill -TERM "$1" 2>/dev/null'


class ValkeyStartupError(RuntimeError):
    """Raised when the server process died or never answered during startup."""


class ValkeyInUse(RuntimeError):  # noqa: N818 - a state, not an error kind
    """Raised when another live process already owns the server for this dir."""


# --- addressing -------------------------------------------------------------


def socket_path_for(data_dir: str | os.PathLike[str]) -> str:
    """The unix socket path the server for ``data_dir`` listens on.

    Deterministic: the same absolute dir always maps to the same path, so any
    process can compute it without asking the owner, before the server is up.
    Short: ``/tmp`` plus a hash, well under the 104 byte limit macOS puts on a
    socket path, however long ``data_dir`` is.
    """
    key = str(Path(data_dir).resolve())
    digest = hashlib.sha1(key.encode(), usedforsecurity=False).hexdigest()[:16]
    return f"/tmp/nu-vk-{digest}.sock"  # noqa: S108 - short on purpose, see above


def url_for(data_dir: str | os.PathLike[str], socket_path: str | None = None) -> str:
    """The ``unix://`` URL a Redis client uses to reach the server for ``data_dir``.

    ``socket_path`` overrides the derived path, and has to match the one the
    server was started with.
    """
    return f"unix://{socket_path or socket_path_for(data_dir)}"


# --- process helpers --------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _is_valkey(pid: int) -> bool:
    """Whether ``pid`` is a ``valkey-server`` process, checked before killing it."""
    try:
        out = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["ps", "-p", str(pid), "-o", "command="],  # noqa: S607 - ps is on every PATH
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return "valkey-server" in out


def _wait_pid_gone(pid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.005)
    return not _pid_alive(pid)


def _kill_pid(pid: int, grace: float) -> None:
    """SIGTERM a process that is not our child, then SIGKILL if it lingers."""
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGTERM)
    if not _wait_pid_gone(pid, grace):
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
        _wait_pid_gone(pid, grace)


def _send(path: str, payload: bytes, timeout: float) -> bytes:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(path)
        sock.sendall(payload)
        return sock.recv(64)


def ping(path: str, timeout: float = 1.0) -> bool:
    """Whether a server on the unix socket ``path`` answers ``PING`` with ``PONG``."""
    try:
        return _send(path, _PING, timeout).startswith(b"+PONG")
    except OSError:
        return False


async def aping(path: str, timeout: float = 1.0) -> bool:
    """Async ``ping``: the same RESP exchange without blocking the loop."""

    async def exchange() -> bytes:
        reader, writer = await asyncio.open_unix_connection(path)
        try:
            writer.write(_PING)
            await writer.drain()
            return await reader.read(64)
        finally:
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()

    try:
        reply = await asyncio.wait_for(exchange(), timeout)
    except (OSError, asyncio.TimeoutError):
        return False
    return reply.startswith(b"+PONG")


def _conf_value(value: object) -> str:
    if value == "" or value is None:
        return '""'
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return str(value)


# --- the fabric -------------------------------------------------------------


class ValkeyServer:
    """A private Valkey server for one data dir, owned by one bracket.

    Provided once near the top of a tree, around whatever talks to it::

        With(
            Provide(ValkeyServer, {"data_dir": d}),
            sqlite_navigator_redis(db, redis_url=url_for(d)),
            body=program,
        )

    Setup reaps a server a crashed owner left behind in the same dir, starts a
    fresh one on the dir's unix socket and returns once it answers ``PING``.
    Cleanup stops it and removes its pid, owner and socket files.

    Args:
        data_dir: the directory the server owns. Created if missing. Holds the
            config, pid file, owner file and log.
        socket_path: an explicit unix socket path, overriding the one derived
            from ``data_dir``. Every client has to be told the same path.
        logfile: where the server logs, relative to ``data_dir`` unless
            absolute. None discards the log.
        config: extra Valkey config directives, name to value, applied over
            the defaults (no RDB, no AOF, no TCP port).
        ready_timeout: how long setup waits for the first ``PONG``.
        grace: how long a SIGTERM is given before SIGKILL, on stop and on reap.
        watchdog: run the ``sh`` watchdog that stops the server when this
            process dies. Off leaves only the reap at next start.

    Notes:
        - No persistence by default: ``save ""`` and ``appendonly no``. The
          server is a notification bus, its keyspace is disposable.
        - ``port 0``: unix socket only, nothing listens on TCP.
        - A live server whose owner is also alive is not reaped; setup raises
          ``ValkeyInUse`` instead, so two hosts on one dir do not keep killing
          each other's server.
        - Both lifecycles are supported. ``asetup`` polls readiness with
          ``asyncio.sleep``; ``acleanup`` runs inline with no await points, so
          a cancellation cannot abandon a half-stopped server.
    """

    def __init__(
        self,
        *,
        data_dir: str | os.PathLike[str],
        socket_path: str | None = None,
        logfile: str | None = "valkey.log",
        config: dict[str, object] | None = None,
        ready_timeout: float = 10.0,
        grace: float = 2.0,
        watchdog: bool = True,
    ) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.socket_path = socket_path or socket_path_for(self.data_dir)
        self.logfile = logfile
        self.config = dict(config or {})
        self.ready_timeout = ready_timeout
        self.grace = grace
        self.watchdog = watchdog
        self._proc: subprocess.Popen | None = None
        self._watchdog: subprocess.Popen | None = None
        self._watchdog_fd: int | None = None

    # --- identity ----------------------------------------------------------

    @property
    def url(self) -> str:
        """The ``unix://`` URL a Redis client connects with."""
        return f"unix://{self.socket_path}"

    @property
    def pid(self) -> int | None:
        """The server's pid while it runs, else None."""
        proc = self._proc
        return proc.pid if proc is not None and proc.poll() is None else None

    def ping(self, timeout: float = 1.0) -> bool:
        """Whether the server answers ``PING`` right now."""
        return ping(self.socket_path, timeout)

    async def aping(self, timeout: float = 1.0) -> bool:
        """Async ``ping``."""
        return await aping(self.socket_path, timeout)

    # --- lifecycle -------------------------------------------------------

    def setup(self, ctx: Context | None) -> None:
        """Reap what a dead owner left behind, start the server, wait for PONG."""
        self._spawn()
        try:
            deadline = time.monotonic() + self.ready_timeout
            delay = 0.001
            while not self._ready_step(deadline):
                time.sleep(delay)
                delay = min(delay * 1.5, 0.005)
        except BaseException:
            self.cleanup()
            raise

    def cleanup(self) -> None:
        """Stop the watchdog, then the server, and remove the dir's run files."""
        self._stop_watchdog()
        proc, self._proc = self._proc, None
        if proc is not None:
            with contextlib.suppress(Exception):
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=self.grace)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=self.grace)
            self._remove_run_files(proc.pid)

    async def asetup(self, ctx: Context | None) -> None:
        """Async lifecycle: spawn inline, poll readiness without holding the loop."""
        self._spawn()
        try:
            deadline = time.monotonic() + self.ready_timeout
            delay = 0.001
            while not self._ready_step(deadline):
                await asyncio.sleep(delay)
                delay = min(delay * 1.5, 0.005)
        except BaseException:
            self.cleanup()
            raise

    async def acleanup(self) -> None:
        """Async lifecycle, deliberately with no await points (see ``WorkerPool``)."""
        self.cleanup()

    # --- internals -------------------------------------------------------

    def _spawn(self) -> None:
        try:
            from valkeylite._binary import get_binary_path
        except ImportError as exc:
            msg = "nustd.valkey needs the server binary: pip install nustd[valkey]"
            raise ImportError(msg) from exc

        binary = get_binary_path()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._reap()
        conf = self.data_dir / _CONF_FILE
        conf.write_text(self._render_config())
        log_path = self._log_path()
        stderr = open(log_path, "ab") if log_path is not None else subprocess.DEVNULL  # noqa: PTH123
        try:
            self._proc = subprocess.Popen(  # noqa: S603 - our own binary and config
                [str(binary), str(conf)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=stderr,
                cwd=str(self.data_dir),
                start_new_session=True,
            )
        finally:
            if stderr is not subprocess.DEVNULL:
                stderr.close()
        # The server writes its own pid file once it is up; writing it here as
        # well closes the window where a crash would leave no record at all.
        (self.data_dir / _PID_FILE).write_text(f"{self._proc.pid}\n")
        (self.data_dir / _OWNER_FILE).write_text(f"{os.getpid()}\n")
        if self.watchdog:
            self._start_watchdog(self._proc.pid)

    def _ready_step(self, deadline: float) -> bool:
        """One readiness probe: True once PONG, raise if dead or out of time."""
        proc = self._proc
        if proc is None or proc.poll() is not None:
            code = None if proc is None else proc.returncode
            msg = f"valkey-server exited during startup (code {code}){self._log_tail()}"
            raise ValkeyStartupError(msg)
        if ping(self.socket_path, timeout=0.5):
            return True
        if time.monotonic() > deadline:
            msg = f"valkey-server did not answer within {self.ready_timeout}s{self._log_tail()}"
            raise ValkeyStartupError(msg)
        return False

    def _render_config(self) -> str:
        directives: dict[str, object] = {
            "port": 0,
            "bind": "127.0.0.1",
            "protected-mode": "yes",
            "daemonize": "no",
            "save": "",
            "appendonly": "no",
            "loglevel": "notice",
        }
        directives.update(self.config)
        log_path = self._log_path()
        directives.update(
            {
                "dir": str(self.data_dir),
                "unixsocket": self.socket_path,
                "unixsocketperm": "700",
                "pidfile": str(self.data_dir / _PID_FILE),
                "logfile": str(log_path) if log_path is not None else "/dev/null",
            },
        )
        lines = ["# written by nustd.valkey; rewritten on every start"]
        lines += [f"{key} {_conf_value(value)}" for key, value in directives.items()]
        return "\n".join(lines) + "\n"

    def _log_path(self) -> Path | None:
        if self.logfile is None:
            return None
        path = Path(self.logfile)
        return path if path.is_absolute() else self.data_dir / path

    def _log_tail(self) -> str:
        path = self._log_path()
        if path is None:
            return ""
        try:
            tail = path.read_bytes()[-2000:].decode(errors="replace")
        except OSError:
            return ""
        return f"\n--- {path} ---\n{tail}"

    def _reap(self) -> None:
        """Clear the dir for a fresh start: stop a leftover server, drop stale files.

        A server is only left behind when its owner died without the watchdog
        doing its job (the watchdog was killed too, or turned off). The pid
        file names it; it is killed only if it really is a ``valkey-server``.
        A server still answering on the socket with no usable pid file is shut
        down over the socket. Either way, if the recorded owner is a live
        process other than this one, the server is someone else's and setup
        refuses rather than pulling it out from under them.
        """
        pid_file = self.data_dir / _PID_FILE
        owner = _read_pid(self.data_dir / _OWNER_FILE)
        pid = _read_pid(pid_file)
        live_server = pid is not None and _pid_alive(pid) and _is_valkey(pid)
        answering = ping(self.socket_path, 0.5)
        if (live_server or answering) and owner not in (None, os.getpid()) and _pid_alive(owner):
            msg = (
                f"a valkey-server for {self.data_dir} is already owned by live pid {owner}; "
                f"stop that process or use another data dir"
            )
            raise ValkeyInUse(msg)
        if live_server:
            _kill_pid(pid, self.grace)  # type: ignore[arg-type]
        if ping(self.socket_path, 0.5):
            with contextlib.suppress(OSError):
                _send(self.socket_path, _SHUTDOWN, 1.0)
            deadline = time.monotonic() + self.grace
            while time.monotonic() < deadline and ping(self.socket_path, 0.1):
                time.sleep(0.005)
        for stale in (Path(self.socket_path), pid_file, self.data_dir / _OWNER_FILE):
            with contextlib.suppress(FileNotFoundError):
                stale.unlink()

    def _start_watchdog(self, server_pid: int) -> None:
        read_fd, write_fd = os.pipe()  # both non-inheritable by default
        try:
            self._watchdog = subprocess.Popen(  # noqa: S603 - fixed script, no user input
                ["/bin/sh", "-c", _WATCHDOG, "nu-valkey-watchdog", str(server_pid)],
                stdin=read_fd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except BaseException:
            os.close(write_fd)
            raise
        finally:
            os.close(read_fd)
        self._watchdog_fd = write_fd

    def _stop_watchdog(self) -> None:
        """Kill the watchdog before the server stops, so it never signals a stale pid."""
        dog, self._watchdog = self._watchdog, None
        if dog is not None:
            with contextlib.suppress(Exception):
                dog.kill()
                dog.wait(timeout=self.grace)
        fd, self._watchdog_fd = self._watchdog_fd, None
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)

    def _remove_run_files(self, pid: int) -> None:
        """Drop the pid, owner and socket files, if they are still ours."""
        pid_file = self.data_dir / _PID_FILE
        if _read_pid(pid_file) == pid:
            with contextlib.suppress(FileNotFoundError):
                pid_file.unlink()
        owner_file = self.data_dir / _OWNER_FILE
        if _read_pid(owner_file) == os.getpid():
            with contextlib.suppress(FileNotFoundError):
                owner_file.unlink()
        if not ping(self.socket_path, 0.1):
            with contextlib.suppress(FileNotFoundError):
                Path(self.socket_path).unlink()
