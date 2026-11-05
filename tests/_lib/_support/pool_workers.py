"""Helpers for the ``nustd.mp_pool`` tests that have to survive a ``spawn``.

Under the default ``spawn`` start method a worker's ``init`` bracket is pickled
into the child, and a class is pickled *by reference*. Anything a test wants a
worker to come up holding therefore has to live in an importable module, not in
the test file (which pytest imports by path under ``--import-mode=importlib``).

Nu terms are different: they pickle by value, so a resident body or a teleported
tree can be built inline in a test. The trees here are shared only because more
than one test wants them.
"""

from __future__ import annotations

import asyncio
import gc
import multiprocessing
import os
import signal
import socket
import subprocess
import time
from multiprocessing.connection import Connection
from pathlib import Path
from typing import TYPE_CHECKING

import nu
from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "RESIDENT",
    "AGuarded",
    "Block",
    "CrashInInit",
    "Die",
    "ForkSleeper",
    "Guarded",
    "HoldAfterHangup",
    "IgnoreTerm",
    "Marker",
    "NestedSpawn",
    "Shell",
    "Sleeper",
    "SlowInit",
    "SlowTouch",
    "Spin",
    "Stubborn",
    "Touch",
]


class Marker:
    """A trivial fabric a worker can be brought up holding, to prove ``init`` ran.

    Bound on the child's Context by an ``init`` bracket; a teleported
    ``FabricRef(Marker)`` read then sees it.
    """

    def __init__(self, label: str = "unset") -> None:
        self.label = label

    def setup(self, ctx: object) -> None:
        """Nothing to build; the instance is the whole fabric."""


class IgnoreTerm:
    """A fabric whose setup makes the worker ignore SIGTERM, so a kill has to escalate.

    Brought up through ``init``: the worker's main thread runs the bracket,
    which is where a signal disposition can be set. A kill then spends its
    full grace in the SIGTERM wait before SIGKILL ends it.
    """

    def setup(self, ctx: object) -> None:
        """Install SIG_IGN for SIGTERM in the worker."""
        signal.signal(signal.SIGTERM, signal.SIG_IGN)


class Block(ScalarQuery):
    """Holds the loop it runs on for ``seconds``, so nothing else on it runs meanwhile.

    Dispatched to a worker, it keeps the worker from reading its pipe, so
    the ack for whatever is sent next is delayed by that long.
    """

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._payload = {"seconds": seconds}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            time.sleep(self._payload["seconds"])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            time.sleep(self._payload["seconds"])  # blocking is the point

        return athunk


class Spin(ScalarQuery):
    """A sync busy loop for ``seconds``: never yields, never sleeps, holds the worker's loop.

    The shape a cooperative cancel cannot reach; only a signal into the
    body ends it early. Yields how long it actually spun.
    """

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._payload = {"seconds": seconds}

    def _spin(self) -> float:
        start = time.monotonic()
        deadline = start + self._payload["seconds"]
        while time.monotonic() < deadline:
            pass
        return time.monotonic() - start

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return self._spin()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._spin()

        return athunk


class Touch:
    """A fabric whose teardown writes ``path``: proof that init teardown ran in a worker."""

    def __init__(self, path: str) -> None:
        self.path = path

    def setup(self, ctx: object) -> None:
        """Nothing to build."""

    def cleanup(self) -> None:
        """Leave the mark."""
        Path(self.path).write_text("torn down")


class SlowTouch(Touch):
    """``Touch`` whose teardown takes ``seconds`` first: one a second SIGTERM could cut short."""

    def __init__(self, path: str, seconds: float) -> None:
        super().__init__(path)
        self.seconds = seconds

    def cleanup(self) -> None:
        """Take a while, then leave the mark."""
        time.sleep(self.seconds)
        super().cleanup()


class CrashInInit:
    """A fabric whose setup starts ``sleep`` in the worker's group, notes its pid, then exits hard.

    The worker dies before ``ready``: what the parent can still sweep then
    is the question.
    """

    def __init__(self, path: str, code: int) -> None:
        self.path = path
        self.code = code

    def setup(self, ctx: object) -> None:
        """Start the sleeper, write its pid to ``path``, ``os._exit``."""
        proc = subprocess.Popen(["/bin/sleep", "600"])
        Path(self.path).write_text(str(proc.pid))
        os._exit(self.code)


class Shell(ScalarQuery):
    """Runs ``cmd`` through ``os.system``: a shell child that inherits whatever is inheritable."""

    def __init__(self, cmd: str) -> None:
        super().__init__()
        self._payload = {"cmd": cmd}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return os.system(self._payload["cmd"])  # noqa: S605

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return os.system(self._payload["cmd"])  # noqa: S605

        return athunk


class Die(ScalarQuery):
    """``os._exit(code)`` from inside a body: the worker crashes, no teardown, no reply."""

    def __init__(self, code: int) -> None:
        super().__init__()
        self._payload = {"code": code}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            os._exit(self._payload["code"])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            os._exit(self._payload["code"])

        return athunk


class Guarded(ScalarQuery):
    """Sleeps ``seconds`` inside a ``try``/``finally`` that writes ``path`` on the way out.

    How a body's own ``finally`` is observed from outside the worker,
    whatever ended the body: a cancel, an interrupt or a SIGTERM.
    """

    def __init__(self, path: str, seconds: float) -> None:
        super().__init__()
        self._payload = {"path": path, "seconds": seconds}

    def _run(self) -> None:
        try:
            time.sleep(self._payload["seconds"])
        finally:
            Path(self._payload["path"]).write_text("finally ran")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            self._run()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            self._run()

        return athunk


class Sleeper(ScalarQuery):
    """Starts ``sleep seconds`` as a subprocess of the worker and yields its pid.

    The subprocess is left running, in the worker's process group, which is
    what the pool's ``killpg`` and the worker's parent watch are for.
    """

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._payload = {"seconds": seconds}

    def _start(self) -> int:
        proc = subprocess.Popen(["/bin/sleep", str(self._payload["seconds"])])  # noqa: S603
        return proc.pid

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return self._start()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._start()

        return athunk


def _grandchild(queue: object) -> None:
    """What ``NestedSpawn`` runs in the worker's own child: report pid and pgid."""
    queue.put((os.getpid(), os.getpgrp()))  # type: ignore[attr-defined]


class NestedSpawn(ScalarQuery):
    """A body that uses ``multiprocessing`` itself: spawn one child, yield its (pid, pgid).

    Only possible because workers are not daemon processes.
    """

    def _nest(self) -> tuple[int, int]:
        ctx = multiprocessing.get_context("spawn")
        queue = ctx.SimpleQueue()
        proc = ctx.Process(target=_grandchild, args=(queue,))
        proc.start()
        try:
            return queue.get()
        finally:
            proc.join(timeout=10)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return self._nest()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._nest()

        return athunk


class SlowInit:
    """A fabric whose setup takes ``seconds``: a worker that stays ``starting`` that long."""

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    def setup(self, ctx: object) -> None:
        """Take a while."""
        time.sleep(self.seconds)


class Stubborn(ScalarQuery):
    """A sync busy loop that swallows ``KeyboardInterrupt`` and keeps going, for ``seconds``.

    The body the SIGINT rung cannot end: only SIGTERM (``SystemExit``) or
    SIGKILL do. Holds the worker's loop the whole time.
    """

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._payload = {"seconds": seconds}

    def _spin(self) -> None:
        deadline = time.monotonic() + self._payload["seconds"]
        while time.monotonic() < deadline:
            try:
                while time.monotonic() < deadline:
                    pass
            except KeyboardInterrupt:
                continue

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            self._spin()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            self._spin()

        return athunk


class AGuarded(ScalarQuery):
    """An async sleep of ``seconds`` in a ``try``/``finally`` that writes ``path``.

    The cooperative twin of ``Guarded``: it yields to the loop, so a cancel
    reaches it and its ``finally`` runs.
    """

    def __init__(self, path: str, seconds: float) -> None:
        super().__init__()
        self._payload = {"path": path, "seconds": seconds}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "AGuarded is async only; pool workers run bodies async"
            raise NotImplementedError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            try:
                await asyncio.sleep(self._payload["seconds"])
            finally:
                Path(self._payload["path"]).write_text("finally ran")

        return athunk


class ForkSleeper(ScalarQuery):
    """A plain ``os.fork`` child that sleeps ``seconds``; yields its pid.

    Unlike an exec'd child it keeps every descriptor the worker has,
    inheritable or not: the worker's pipe and its exit sentinel stay open
    for as long as it lives, so only a watch on the worker's pid sees the
    worker go.
    """

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._payload = {"seconds": seconds}

    def _fork(self) -> int:
        pid = os.fork()
        if pid == 0:
            time.sleep(self._payload["seconds"])
            os._exit(0)
        return pid

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return self._fork()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._fork()

        return athunk


class HoldAfterHangup(ScalarQuery):
    """Hangs up the worker's pipe to the parent, then holds the loop for ``seconds``.

    The shape "the pipe closed but the process lingers": the parent reads EOF
    while the worker is still very much there.
    """

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._payload = {"seconds": seconds}

    def _run(self) -> None:
        for obj in gc.get_objects():
            if isinstance(obj, Connection) and not obj.closed:
                with socket.socket(fileno=os.dup(obj.fileno())) as sock:
                    sock.shutdown(socket.SHUT_RDWR)
        time.sleep(self._payload["seconds"])

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            self._run()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            self._run()

        return athunk


# A body that never terminates: the thing Dispatch exists for. It holds no
# state across calls, so a test watches it through the pool (running, cancel,
# kill), never by reading back what it wrote.
RESIDENT = nu.ForeverDo(nu.Delay(0.005))
