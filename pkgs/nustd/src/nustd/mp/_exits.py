"""``ExitWatch``: "this process has exited" as a descriptor that turns readable.

The pool learns that a worker is gone from the process itself, not from its
pipe. A pipe or the spawn sentinel reads EOF only once *every* holder of
the write end has closed it, and a grandchild a body forked holds a copy, so
a worker that crashed can look alive for as long as that grandchild lives.
The kernel's own exit notification has no such blind spot:

- Linux: ``pidfd_open(pid)``, readable once the process has exited. Through
  ``os.pidfd_open`` when Python has it, else the raw syscall through
  ``ctypes``: the Pythons uv installs are built against old kernel headers
  and lack ``os.pidfd_open`` even on a kernel that has the call (5.3+).
- mac and the BSDs: a ``kqueue`` with ``EVFILT_PROC`` / ``NOTE_EXIT`` on the
  pid; the kqueue descriptor turns readable once the exit event is queued.
  Registering on a process that already exited fails with ESRCH, which is
  read as "exited".
- anything else: the spawn sentinel, which is what ``multiprocessing`` itself
  waits on, with its blind spot.

All three are plain descriptors, so one ``wait`` covers the pipe and the
exit together, and an event loop could ``add_reader`` either. Nothing here
reaps: readable means the process is a zombie (or gone), and the one reaper
is the handle's reader thread.
"""

from __future__ import annotations

import contextlib
import ctypes
import errno
import os
import select
import sys
from multiprocessing.connection import wait as _wait


__all__ = ["ExitWatch"]


# ``pidfd_open`` in the unified syscall table every Linux architecture shares.
_SYS_PIDFD_OPEN = 434


def _pidfd_open_syscall(pid: int) -> int:
    """``pidfd_open(pid, 0)`` through ``syscall(2)``; raises ``OSError`` like ``os.pidfd_open``."""
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(_SYS_PIDFD_OPEN, ctypes.c_int(pid), ctypes.c_uint(0))
    if fd < 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))
    return int(fd)


def _pidfd_opener() -> object:
    """``os.pidfd_open``, the syscall on a Linux Python without it, else None."""
    opener = getattr(os, "pidfd_open", None)
    if opener is None and sys.platform.startswith("linux"):
        opener = _pidfd_open_syscall
    return opener


class ExitWatch:
    """A readable-on-exit descriptor for one child process.

    Args:
        pid: the child's process id. Must be our own child, not yet reaped.
        sentinel: the spawn sentinel, used when the OS offers nothing better.

    Notes:
        - ``kind`` says which mechanism is in use: ``"pidfd"``, ``"kqueue"``,
          ``"sentinel"``, or ``"gone"`` when the process had already exited
          at construction (the descriptor is then always readable).
        - The descriptor stays readable after the exit: nothing ever drains
          the kqueue, and a pidfd is level triggered.
        - ``close`` releases what this watch opened; the sentinel belongs to
          the ``Process`` and is left alone.
    """

    def __init__(self, pid: int, sentinel: int) -> None:
        self.pid = pid
        self.kind = "sentinel"
        self._fd = sentinel
        self._owned: object = None
        self._open(pid)

    def _open(self, pid: int) -> None:
        pidfd_open = _pidfd_opener()
        if pidfd_open is not None:
            try:
                fd = pidfd_open(pid)  # type: ignore[operator]
            except (OSError, AttributeError) as exc:
                if getattr(exc, "errno", None) == errno.ESRCH:
                    self._gone()
                    return
                # ENOSYS on an old kernel, or no libc syscall: the next mechanism
            else:
                os.set_inheritable(fd, False)
                self.kind, self._fd, self._owned = "pidfd", fd, fd
                return
        if hasattr(select, "kqueue"):
            kq = select.kqueue()
            event = select.kevent(
                pid,
                filter=select.KQ_FILTER_PROC,
                flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                fflags=select.KQ_NOTE_EXIT,
            )
            try:
                kq.control([event], 0, 0)
            except ProcessLookupError:
                kq.close()
                self._gone()
                return
            except OSError:
                kq.close()
                return
            self.kind, self._fd, self._owned = "kqueue", kq.fileno(), kq

    def _gone(self) -> None:
        """Already exited at construction: a pipe whose read end is always readable."""
        r, w = os.pipe()
        os.close(w)
        self.kind, self._fd, self._owned = "gone", r, r

    def fileno(self) -> int:
        """The descriptor that turns readable once the process has exited."""
        return self._fd

    def wait(self, timeout: float | None = None) -> bool:
        """Block until the process has exited, at most ``timeout``; whether it has."""
        try:
            return bool(_wait([self._fd], timeout))
        except (OSError, ValueError):
            return True  # closed under us: the record is in, or on its way

    def close(self) -> None:
        """Release the descriptor this watch opened. Idempotent."""
        owned, self._owned = self._owned, None
        with contextlib.suppress(OSError):
            if isinstance(owned, int):
                os.close(owned)
            elif owned is not None:
                owned.close()  # type: ignore[attr-defined]
