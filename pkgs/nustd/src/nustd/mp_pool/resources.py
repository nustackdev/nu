"""``WorkerPool``: the fabric that owns N worker processes.

Where ``nustd.mp.MpWorker`` is the fabric of *one* process - its whole lifecycle
is the ``Provide`` bracket - ``WorkerPool`` is the fabric of the *fleet*. One
``Provide`` at the top of a tree owns ``{id -> process}``, and because the
fabric spans many processes it legitimately carries interactions over them:
launch one, run a tree on one, interrupt, stop or kill one, read its status.

Deliberately absent: size, scheduling, acquire/release. Those are policy and
belong to callers. The one convenience the pool does keep is warmth: with
``spares=N`` it holds N idle workers ready, and ``launch`` takes one of those
before it spawns.

Parent-side shape, per worker:

- a ``Process`` and its half of a duplex ``Pipe``
- its identity: pid from the spawn, pgid and start time from the ``ready``
  frame, the title it runs under
- an exit watch (``_exits.ExitWatch``): a pidfd on Linux, a kqueue on mac,
  the spawn sentinel elsewhere. Readable once the process has exited, whoever
  else still holds its pipe.
- a daemon reader thread waiting on the pipe and the exit watch together. It
  resolves waiters by token, and it is the one reaper: when the process is
  gone it reaps it, records the exit code and the cause, fails every pending
  request with ``WorkerGone``, sweeps the process group and wakes whoever
  waits on the exit, sync or async.
- the jobs it runs (teleports in flight, dispatched bodies acked and not
  finished), and the last errors its dispatched bodies raised

Ending a worker is a ladder under one budget, ``grace``: a ``stop`` frame
first (polite, up to 60%), then SIGINT to its group (60%), SIGTERM (80%),
SIGKILL (95%), and the ladder returns by ``grace`` whatever happened. The
ratios are fixed. ``Stop`` runs it for one worker, the pool's close runs it
for every worker at once. Nothing on that path joins or blocks: the sync
form waits on events, the async form awaits futures the reader thread
resolves through the loop, and both give up at the deadline.

Containment is the worker's own doing (see ``_worker``): it leads its own
process group, so signals from here go to the group, the worker and every
subprocess its bodies started, in one ``killpg``. Only once the child has told
us the group though, and never a group that is our own: before that the pid
alone is signalled. Spawned with SIGINT and SIGTERM masked, so the window
between the spawn and the child's own handlers is closed. Not daemon
processes, so bodies can use ``multiprocessing``; an ``atexit`` hook SIGKILLs
whatever is still up at interpreter exit, so that exit never joins a worker.

And for the pool itself, books that close cannot miss: a closed flag no
launch gets past, a count of launches between spawn and registration, and
the workers being ended on other threads. Close waits on both, within the
same budget, so a thread a cancelled await left behind never owns a process
the pool has forgotten.

Worker ids are monotonic ints and are never reused, so a stale id is
detectably dead rather than silently a different worker. What an exited
worker left behind (its ``WorkerStatus``) stays readable, for the last
``_KEPT_EXITED`` exits.
"""

from __future__ import annotations

import asyncio
import atexit
import collections
import contextlib
import itertools
import logging
import multiprocessing as _mp
import multiprocessing.util  # its atexit joins every child; ours must register after it
import os
import signal
import threading
import time
from dataclasses import dataclass
from multiprocessing import resource_tracker as _tracker
from multiprocessing.connection import wait as _wait_fds
from typing import TYPE_CHECKING

from nu.lang import wire

from ._exits import ExitWatch
from ._worker import _GUARD, _pool_worker_main


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from multiprocessing.connection import Connection
    from multiprocessing.context import BaseContext, Process

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Context


__all__ = [
    "Interrupted",
    "PoolClosed",
    "UnknownWorker",
    "WorkerGone",
    "WorkerPool",
    "WorkerStatus",
]


log = logging.getLogger("nustd.mp_pool")

# The ladder, as shares of ``grace``: polite until the first rung, then each
# signal at its mark. Fixed on purpose; only ``grace`` is a knob.
_POLITE = 0.6
_RUNGS = ((0.6, signal.SIGINT), (0.8, signal.SIGTERM), (0.95, signal.SIGKILL))
# How many exited workers' records the pool keeps for ``status`` and ``wait``.
_KEPT_EXITED = 1024
# How many dispatched-body errors each worker's status keeps, newest last.
_KEPT_ERRORS = 16
# The pipe closed with the process still up: how long to wait for its exit
# before failing pending requests without an exit code.
_EOF_GRACE = 0.2
# Who ended a worker, strongest last: a later, stronger claim wins.
_HINT_RANK = {"stopped": 0, "killed": 1, "init_failed": 2, "parent_died": 3}


class WorkerGone(RuntimeError):  # noqa: N818 - a state, not an error kind
    """Raised when the worker a call targets is gone, or went while it waited.

    Args:
        message: what happened, for the traceback.
        wid: the worker's id, when there is one.
        cause: why it ended, the same word ``WorkerStatus.cause`` has, or None
            when that is not known yet.
        exitcode: its exit code, or None when not known yet.
    """

    def __init__(
        self,
        message: str = "the worker is gone",
        *,
        wid: int | None = None,
        cause: str | None = None,
        exitcode: int | None = None,
    ) -> None:
        super().__init__(message)
        self.wid = wid
        self.cause = cause
        self.exitcode = exitcode


class PoolClosed(WorkerGone):
    """Raised by a launch on a pool that is closed or closing."""


class Interrupted(RuntimeError):  # noqa: N818 - a state, not an error kind
    """Raised by a ``Teleport`` whose body was ended by ``Interrupt``. The worker is still up.

    Args:
        message: what happened, for the traceback.
        wid: the worker's id.
        job: the request's job id.
    """

    def __init__(
        self, message: str = "interrupted", *, wid: int | None = None, job: int | None = None
    ) -> None:
        super().__init__(message)
        self.wid = wid
        self.job = job


class UnknownWorker(KeyError):  # noqa: N818 - a state, not an error kind
    """Raised when a worker id was never launched here, or its record is long gone."""


@dataclass(frozen=True)
class WorkerStatus:
    """One worker, as the pool knows it: a snapshot, readable alive and after it is gone.

    Attributes:
        wid: the worker id.
        state: ``"starting"`` (spawned, no ``ready`` yet), ``"idle"`` (ready,
            no jobs), ``"busy"`` (one or more jobs), ``"stopping"`` (a stop or
            kill is under way) or ``"exited"``.
        pid: the process id, known from the spawn.
        pgid: the process group it leads; None until the child reported it.
        name: the title it runs under, ``nu:{pool name}-{wid}``.
        started_at: wall clock time of ``ready``; None before that.
        jobs: the ids of the jobs running on it: teleports in flight and
            dispatched bodies acked and not finished. Empty once exited.
        exitcode: the exit code once it is gone and reaped, else None.
            Negative for a signal, 143 for a SIGTERM the worker handled.
        cause: once exited, why: ``"stopped"`` (a stop that ended politely
            or at the SIGINT rung, or a clean exit 0), ``"killed"`` (the pool
            signalled it: a Kill, or a stop that reached SIGTERM or SIGKILL),
            ``"crashed"`` (any other exit nobody asked for, a signal the pool
            did not send included),
            ``"init_failed"`` (gone before ``ready``) or ``"parent_died"``
            (ended by the host's own exit). None while it runs.
        errors: the last few ``(job, exception)`` pairs its dispatched bodies
            raised, oldest first. Each is also logged when it arrives.
    """

    wid: int
    state: str
    pid: int
    pgid: int | None
    name: str
    started_at: float | None
    jobs: tuple[int, ...] = ()
    exitcode: int | None = None
    cause: str | None = None
    errors: tuple[tuple[int, BaseException], ...] = ()


class _Reply:
    """A one-shot slot a reader thread fills and a caller waits on.

    A sync caller blocks on ``event``. An async caller hands its loop in and
    awaits ``future``, which ``set`` resolves through that loop, so no thread
    is held while it waits and cancelling the await is a plain cancellation.
    """

    __slots__ = ("cancelled", "event", "future", "kind", "loop", "sent", "value")

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self.event = threading.Event()
        self.kind: str | None = None
        self.value: object = None
        self.loop = loop
        self.future: asyncio.Future | None = None if loop is None else loop.create_future()
        # Both guarded by the handle's state lock. See ``_WorkerHandle.cancel``.
        self.sent = False
        self.cancelled = False

    def set(self, kind: str, value: object) -> None:
        """Fill the slot and wake the waiter. Safe from any thread."""
        self.kind = kind
        self.value = value
        self.event.set()
        if self.future is not None:
            with contextlib.suppress(RuntimeError):  # that loop is closed already
                self.loop.call_soon_threadsafe(_resolve, self.future, None)  # type: ignore[union-attr]

    def result(self) -> object:
        """What came back: the value, or the error raised."""
        if self.kind in ("err", "gone"):
            raise self.value  # type: ignore[misc]
        return self.value

    def wait(self, timeout: float | None) -> object:
        """Block for the reply; raise what came back, or time out."""
        if not self.event.wait(timeout):
            raise TimeoutError("worker did not reply in time")
        return self.result()

    async def await_(self, timeout: float | None = None) -> object:
        """Wait for the reply on the loop it was made for; raise what came back, or time out.

        The timeout is a plain ``asyncio.wait``, which leaves the future
        alone and raises a cancellation as a cancellation. ``wait_for`` on
        3.10 would hand the result back instead when the reply resolves in
        the same moment the caller is cancelled.
        """
        if timeout is None:
            await self.future  # type: ignore[misc]
        else:
            done, _ = await asyncio.wait({self.future}, timeout=timeout)  # type: ignore[type-var]
            if not done:
                raise TimeoutError("worker did not reply in time")
        return self.result()


class _WorkerHandle:
    """Parent-side handle on one worker process: pipe, exit watch, reader thread, books.

    Its reader thread is the only thing that reaps the process. Everything
    else that ends a worker (stop, the ladder's signals, kill) only signals
    and then waits for the exit record the reader fills in.
    """

    def __init__(
        self,
        wid: int,
        proc: Process,
        conn: Connection,
        *,
        name: str = "nu",
        on_exit: Callable[[_WorkerHandle], None] | None = None,
    ) -> None:
        self.wid = wid
        self.proc = proc
        self.conn = conn
        self.name = name
        self._on_exit = on_exit
        # Identity. The pid is known from the spawn; the group and the start
        # time arrive from the child. Until the group does, every signal goes
        # to the pid alone.
        self.pid: int = proc.pid  # type: ignore[assignment]
        self.pgid: int | None = None
        self.started_at: float | None = None
        self._tokens = itertools.count()
        self._send_lock = threading.Lock()
        self._state = threading.Lock()
        self._pending: dict[int, _Reply] = {}
        # Jobs running: exec tokens from open to their last frame, dispatch
        # tokens from the ack to their last frame.
        self._running: set[int] = set()
        self._dispatched: set[int] = set()
        self._errors: collections.deque[tuple[int, BaseException]] = collections.deque(
            maxlen=_KEPT_ERRORS
        )
        self._ready = threading.Event()
        self._ready_error: BaseException | None = None
        self._closed = False
        # Who started this worker's end, for the cause. See ``mark``.
        self._hint: str | None = None
        self._stop_sent = False
        # SIGTERM goes out once. In the worker it is one-shot too; a repeat
        # would cut the teardown the first one started.
        self._termed = False
        # Exit record, filled once on the reader thread. ``_recorded`` flips
        # first (code and cause are in), ``_exited`` last, once the pool's
        # books have the record too: whoever wakes on it finds them current.
        # ``_exit_waiters`` are futures on some loop, each woken through that
        # loop's ``call_soon_threadsafe``.
        self._recorded = False
        self._exited = threading.Event()
        self.exitcode: int | None = None
        self.cause: str | None = None
        self._exit_waiters: list[tuple[asyncio.AbstractEventLoop, asyncio.Future]] = []
        self._watch = ExitWatch(self.pid, proc.sentinel)
        self._reader = threading.Thread(
            target=self._read_loop,
            name=f"nu-mp-pool-reader-{wid}",
            daemon=True,
        )
        _live_add(self)
        self._reader.start()

    # --- reader thread ---------------------------------------------------

    def _read_loop(self) -> None:
        """Serve the pipe until the process is gone, then reap it and record the exit.

        The pipe and the exit watch are waited on together, so a worker that
        is gone is seen as gone even when a grandchild still holds its pipe.
        A pipe that closes first (the worker is on its way out) gets a short
        wait for the exit; past that, pending requests are failed without a
        code and the thread waits for the exit itself, however long it takes.
        """
        exited = False
        try:
            exited = self._serve_pipe()
        except Exception:
            log.exception("worker %s: the reader failed", self.wid)
        finally:
            if not exited and not self._watch.wait(_EOF_GRACE):
                self._abandon(
                    lambda: WorkerGone(f"worker {self.wid} closed its pipe", wid=self.wid)
                )
                self._watch.wait(None)
            self._record(self._reap())

    def _serve_pipe(self) -> bool:
        """Frames until the pipe closes (False) or the process is gone (True)."""
        exit_fd = self._watch.fileno()
        while True:
            try:
                ready = _wait_fds([self.conn, exit_fd])
            except (OSError, ValueError):
                return False
            if exit_fd in ready:
                # Gone. Whatever it said on the way out is still in the pipe.
                self._drain()
                return True
            try:
                frame = wire.recv(self.conn)
            except (EOFError, OSError, ValueError):
                return False
            self._handle(frame)

    def _drain(self) -> None:
        """Read what is left in the pipe without blocking."""
        with contextlib.suppress(EOFError, OSError, ValueError):
            while self.conn.poll(0):
                self._handle(wire.recv(self.conn))

    def _reap(self) -> int | None:
        """The process is gone: reap it and read its code.

        The exit watch says the process has exited, so the ``waitpid`` behind
        ``join`` returns at once. Only this thread reaps. ``multiprocessing``
        itself polls its children now and then (``Process.start``,
        ``active_children``) and may get there first, which ``_code_of`` waits
        out. With only the sentinel to go by the process may still be on its
        way out, and the join waits for it.
        """
        try:
            self.proc.join()
            return _code_of(self.proc)
        except Exception:
            return None

    def _handle(self, frame: tuple) -> None:
        kind = frame[0]
        if kind == "group":
            # ('group', pgid): sent before the child's init runs, so even a
            # crash in there leaves a group to sweep. Trusted only when the
            # child leads it (``_leads_group``).
            self.pgid = frame[1]
            return
        if kind == "ready":
            # ('ready', pid, pgid, started_at)
            _, _pid, self.pgid, self.started_at = frame
            self._ready.set()
            return
        if kind == "failed":
            self._ready_error = frame[1]
            self._ready.set()
            return
        token = frame[1]
        with self._state:
            dispatched = token in self._dispatched
            if kind == "ack":
                self._running.add(token)
                self._dispatched.add(token)
            else:
                self._running.discard(token)
                self._dispatched.discard(token)
            reply = self._pending.pop(token, None)
        if reply is None:
            if kind == "err" and dispatched:
                self._dispatch_failed(token, frame[2])
            return
        if kind == "ack":
            reply.set("ack", None)
        elif kind == "ok":
            reply.set("ok", frame[2])
        elif kind == "err":
            reply.set("err", frame[2])
        elif kind == "interrupted":
            reply.set(
                "err",
                Interrupted(
                    f"worker {self.wid}: job {token} was interrupted", wid=self.wid, job=token
                ),
            )
        elif kind == "cancelled":
            # ``cancel`` takes the waiter off the books before it sends the
            # frame that leads here, so a waiter still on them means the body
            # cancelled itself in the worker.
            reply.set(
                "err", RuntimeError(f"worker {self.wid}: job {token} was cancelled in the worker")
            )

    def _dispatch_failed(self, token: int, exc: BaseException) -> None:
        """A dispatched body raised. Nobody waits on it: log it, keep it on the status."""
        with self._state:
            self._errors.append((token, exc))
        log.error(
            "worker %s (%s): dispatched job %s raised %s: %s",
            self.wid,
            self.name,
            token,
            type(exc).__name__,
            exc,
            exc_info=exc,
        )

    def _abandon(self, error: Callable[[], WorkerGone]) -> None:
        """Fail everything still waiting, each with an error of its own; take no more requests."""
        with self._state:
            self._closed = True
            pending = list(self._pending.values())
            self._pending.clear()
        for reply in pending:
            reply.set("gone", error())
        if not self._ready.is_set():
            self._ready_error = error()
            self._ready.set()

    def _record(self, code: int | None) -> None:
        """The exit, once: code and cause, group swept, books moved, then everyone woken.

        Runs on the reader thread, after the reap. The group is swept here, at
        the reap, while its id still means that group: whatever a body left
        behind gets SIGKILL. Then the pool is told, so the worker drops out of
        its books and its status moves to the exited records, and only then
        are pending requests failed and the exit's waiters woken, so what they
        read next is current.
        """
        with self._state:
            if self._recorded:
                return
            self._recorded = True
            self.exitcode = code
            self.cause = self._cause_of(code)
            self._closed = True
            self._running.clear()
            self._dispatched.clear()
        self._sweep()
        _live_discard(self)
        # Not ``proc.close()``: ``multiprocessing`` polls every child it
        # still lists from any thread's ``Process.start``, and a closed one
        # has no ``_popen`` to poll. The handle is dropped after this, and
        # the ``Process`` with it.
        for closing in (self.conn.close, self._watch.close):
            with contextlib.suppress(Exception):
                closing()
        if self._on_exit is not None:
            try:
                self._on_exit(self)
            except Exception:
                log.exception("worker %s: recording its exit failed", self.wid)
        self._abandon(self._gone)
        with self._state:
            self._exited.set()
            waiters, self._exit_waiters = self._exit_waiters, []
        for loop, fut in waiters:
            with contextlib.suppress(RuntimeError):  # that loop is closed already
                loop.call_soon_threadsafe(_resolve, fut, None)

    def _cause_of(self, code: int | None) -> str:
        """Why the worker ended: who started its end, else what the exit says.

        ``killed`` only when the pool signalled the end itself: a Kill, or a
        ladder that reached its SIGTERM rung. A signal the pool did not send
        (another process, the OOM killer) reads ``crashed``, so a caller can
        tell its own kill from a loss.
        """
        hint = self._hint
        if hint == "stopped":
            if self._termed:
                return "killed"
            # The pool sent no SIGKILL yet, so a -9 came from outside.
            return "crashed" if code == -signal.SIGKILL else "stopped"
        if hint is not None:
            return hint
        if self.started_at is None:
            return "init_failed"
        return "stopped" if code == 0 else "crashed"

    def _gone(self) -> WorkerGone:
        return WorkerGone(
            f"worker {self.wid} is gone ({self.cause}, exit code {self.exitcode})",
            wid=self.wid,
            cause=self.cause,
            exitcode=self.exitcode,
        )

    # --- signals -----------------------------------------------------------

    def _leads_group(self) -> bool:
        """Whether the worker leads a group of its own that we may signal.

        True only once the child reported it: before that a ``killpg`` on the
        child's group would be a ``killpg`` on ours. And never when the
        group is ours, however it came to be.
        """
        return self.pgid is not None and self.pgid == self.pid and self.pgid != os.getpgrp()

    def _signal(self, sig: int) -> None:
        """Send ``sig`` to the worker: its whole group once it leads one, the pid alone before.

        Never blocks and never polls: a ``waitpid`` here would race the
        reaper for the exit code. A process known reaped is skipped; one that
        is gone but not reaped yet is a zombie, which a signal does not hurt
        and whose group still holds its leftovers.
        """
        if _reaped(self.proc):
            return
        with contextlib.suppress(OSError):
            if self._leads_group():
                os.killpg(self.pid, sig)
            else:
                os.kill(self.pid, sig)

    def _sweep(self) -> None:
        """SIGKILL whatever is left in the worker's group, now that the worker itself is gone."""
        if self._leads_group():
            with contextlib.suppress(OSError):
                os.killpg(self.pid, signal.SIGKILL)

    def mark(self, hint: str) -> None:
        """Note who is ending this worker, for its cause, and take no more requests.

        The stronger claim wins: a kill after a stop makes it ``killed``.
        """
        with self._state:
            self._closed = True
            if self._hint is None or _HINT_RANK[hint] > _HINT_RANK[self._hint]:
                self._hint = hint

    def send_stop(self, deadline: float) -> None:
        """The polite rung: the ``stop`` frame, once, on a thread so a full pipe never blocks us."""
        with self._state:
            sent, self._stop_sent = self._stop_sent, True
        if sent or self.exited:
            return

        def send() -> None:
            with contextlib.suppress(Exception), self._send_lock:
                wire.send(self.conn, ("stop", deadline))

        threading.Thread(target=send, name=f"nu-mp-pool-stop-{self.wid}", daemon=True).start()

    def escalate(self, sig: int) -> None:
        """One of the ladder's signals. SIGTERM goes out once."""
        if sig == signal.SIGTERM:
            with self._state:
                sent, self._termed = self._termed, True
            if sent:
                return
        self._signal(sig)

    def kill_now(self, hint: str = "killed") -> None:
        """SIGKILL the worker's group now. No wait: the reader records the exit."""
        self.mark(hint)
        self._signal(signal.SIGKILL)

    def interrupt(self) -> None:
        """SIGINT to the worker's group: every job ends, the worker serves on."""
        self._signal(signal.SIGINT)

    # --- reads -------------------------------------------------------------

    @property
    def exited(self) -> bool:
        """Whether the exit is recorded: code and cause are in."""
        return self._recorded

    def status(self) -> WorkerStatus:
        """A snapshot of this worker."""
        with self._state:
            if self._recorded:
                state = "exited"
            elif self._hint is not None:
                state = "stopping"
            elif self.started_at is None:
                state = "starting"
            elif self._running:
                state = "busy"
            else:
                state = "idle"
            return WorkerStatus(
                wid=self.wid,
                state=state,
                pid=self.pid,
                pgid=self.pgid,
                name=self.name,
                started_at=self.started_at,
                jobs=tuple(sorted(self._running)),
                exitcode=self.exitcode,
                cause=self.cause,
                errors=tuple(self._errors),
            )

    # --- parent-side calls -----------------------------------------------

    def wait_ready(self, timeout: float | None) -> None:
        """Block until the child has built its Context, or blow up trying."""
        if not self._ready.wait(timeout):
            raise TimeoutError(f"worker {self.wid} did not come up in time")
        if self._ready_error is not None:
            raise self._ready_error

    def open(
        self, loop: asyncio.AbstractEventLoop | None = None, *, job: bool = False
    ) -> tuple[int, _Reply]:
        """Register a waiter for a new request, without sending anything yet.

        ``job`` counts the request as running from here on (a teleport); a
        dispatch counts once the child acked it.
        """
        token = next(self._tokens)
        reply = _Reply(loop)
        with self._state:
            if self._closed:
                raise self._refusal()
            self._pending[token] = reply
            if job:
                self._running.add(token)
        return token, reply

    def _refusal(self) -> WorkerGone:
        if self._recorded:
            return self._gone()
        return WorkerGone(f"worker {self.wid} is going away", wid=self.wid)

    def send(self, kind: str, token: int, reply: _Reply, tree: object, attrs: dict | None) -> None:
        """Send an opened request's frame. A cancel that came in meanwhile follows it out."""
        try:
            with self._send_lock:
                wire.send(self.conn, (kind, token, tree, attrs))
        except (OSError, ValueError, BrokenPipeError) as exc:
            with self._state:
                self._pending.pop(token, None)
                self._running.discard(token)
            raise self._refusal() from exc
        with self._state:
            reply.sent = True
            cancelled = reply.cancelled
        if cancelled:
            self._send_cancel(token)

    def request(self, kind: str, tree: object, attrs: dict | None) -> tuple[int, _Reply]:
        """Register a waiter, send the frame, hand the token and the slot back."""
        token, reply = self.open(job=kind == "exec")
        self.send(kind, token, reply, tree, attrs)
        return token, reply

    def cancel(self, token: int) -> None:
        """Have the worker cancel request ``token``. A no-op once it has finished.

        The waiter comes off the books first, so a reply racing the cancel
        wakes nobody. A request whose frame is not out yet is only flagged:
        its sender sends the cancel right after it, so the worker never sees
        a cancel ahead of the request it names.
        """
        with self._state:
            if self._recorded:
                return
            reply = self._pending.pop(token, None)
            if reply is not None:
                reply.cancelled = True
                if not reply.sent:
                    return
            elif token not in self._running:
                return
        self._send_cancel(token)

    def _send_cancel(self, token: int) -> None:
        with contextlib.suppress(OSError, ValueError), self._send_lock:
            wire.send(self.conn, ("cancel", token))

    def wait_exit(self, timeout: float | None = None) -> bool:
        """Block until the exit is recorded, at most ``timeout``; whether it is."""
        return self._exited.wait(timeout)

    def exit_future(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        """A future on ``loop`` that resolves once the exit is recorded.

        Registered under the state lock, so an exit landing between the
        check and the registration is not missed. ``drop`` it when done.
        """
        fut: asyncio.Future = loop.create_future()
        with self._state:
            if self._exited.is_set():
                fut.set_result(None)
            else:
                self._exit_waiters.append((loop, fut))
        return fut

    def drop(self, fut: asyncio.Future) -> None:
        """Forget an exit future nobody waits on any more."""
        with self._state:
            self._exit_waiters = [entry for entry in self._exit_waiters if entry[1] is not fut]

    async def await_exit(self, timeout: float | None = None) -> bool:
        """Wait for the exit record without holding a thread; whether it came in time."""
        fut = self.exit_future(asyncio.get_running_loop())
        try:
            done, _ = await asyncio.wait({fut}, timeout=timeout)
            return bool(done)
        finally:
            self.drop(fut)


def _resolve(fut: asyncio.Future, value: object) -> None:
    """Set ``fut`` unless its waiter already went away. Runs on ``fut``'s loop."""
    if not fut.done():
        fut.set_result(value)


def _reaped(proc: Process) -> bool:
    """Whether the process has been reaped, read off its ``Popen`` with no ``waitpid``.

    ``is_alive`` and ``exitcode`` both poll, and a poll losing the race to
    the reap on another thread reads ECHILD as "not mine", so neither is
    safe to ask from a path that only wants to know whether to signal. A
    closed ``Process`` has nothing left to signal either.
    """
    popen = getattr(proc, "_popen", None)
    return popen is None or popen.returncode is not None


def _code_of(proc: Process) -> int | None:
    """The exit code after a join, patient with a reap another thread got to first.

    ``multiprocessing`` polls every child of its own (``Process.start``,
    ``active_children``), so our ``waitpid`` can lose to one of those: it
    gets ECHILD, the winner stores the code on the shared ``Popen`` a moment
    later. A few reads cover that moment; a process still up reads None.
    """
    for _ in range(20):
        code = proc.exitcode
        if code is not None:
            return code
        time.sleep(0.001)
    return None


# --- the ladder ---------------------------------------------------------------


def _ladder(handles: list[_WorkerHandle], start: float, grace: float) -> Iterator[float]:
    """The rungs for ``handles``, all at once, under one budget from ``start`` (monotonic).

    Sends the ``stop`` frame to each, then yields the time the next rung is
    due; the driver waits until then or until every handle has exited, and
    the generator applies the rung to whoever is still up. The last yield is
    ``start + grace``, the end of the budget. Shared by the sync and async
    drivers, so both climb exactly the same ladder.
    """
    polite_end = time.time() + (start + _POLITE * grace - time.monotonic())
    for handle in handles:
        handle.mark("stopped")
        handle.send_stop(polite_end)
    for share, sig in _RUNGS:
        yield start + share * grace
        for handle in handles:
            if not handle.exited:
                handle.escalate(sig)
    yield start + grace


def _climb(handles: list[_WorkerHandle], start: float, grace: float) -> None:
    """The ladder, waiting on threads' events. Returns by ``start + grace``."""
    for until in _ladder(handles, start, grace):
        for handle in handles:
            left = until - time.monotonic()
            if left <= 0:
                break
            handle.wait_exit(left)
        if all(handle.exited for handle in handles):
            return


async def _aclimb(handles: list[_WorkerHandle], start: float, grace: float) -> None:
    """The ladder, awaiting exit futures on the loop. Returns by ``start + grace``.

    Nothing here blocks the loop: every wait is an ``asyncio.wait`` on
    futures the reader threads resolve. A cancellation raises out as is;
    the caller decides what that means for the processes.
    """
    loop = asyncio.get_running_loop()
    futs = [(handle, handle.exit_future(loop)) for handle in handles]
    try:
        for until in _ladder(handles, start, grace):
            pending = [fut for _, fut in futs if not fut.done()]
            if not pending:
                return
            left = until - time.monotonic()
            if left > 0:
                await asyncio.wait(pending, timeout=left)
    finally:
        for handle, fut in futs:
            handle.drop(fut)


async def _until(check: Callable[[], bool], deadline: float) -> None:
    """Wait on the loop until ``check()`` or ``deadline`` (monotonic), in short steps."""
    while not check() and time.monotonic() < deadline:
        await asyncio.sleep(0.01)


# --- interpreter exit ---------------------------------------------------------

# Every handle whose process is not known to be gone, across all pools. The
# interpreter's exit SIGKILLs them: the workers are not daemon processes, and
# ``multiprocessing`` would otherwise join each one with no bound.
_live: set[_WorkerHandle] = set()
_live_lock = threading.Lock()


def _live_add(handle: _WorkerHandle) -> None:
    with _live_lock:
        _live.add(handle)


def _live_discard(handle: _WorkerHandle) -> None:
    with _live_lock:
        _live.discard(handle)


def _kill_all_at_exit() -> None:
    """SIGKILL every worker group still up, no joins. The interpreter is leaving."""
    with _live_lock:
        handles = list(_live)
    for handle in handles:
        handle.kill_now("parent_died")


# Registered after ``multiprocessing.util`` registered its own, so it runs
# first: atexit is LIFO, and theirs joins every non-daemon child.
atexit.register(_kill_all_at_exit)


def _start_masked(proc: Process) -> None:
    """``proc.start()`` with SIGINT and SIGTERM masked, so the child inherits the mask.

    The child unblocks them once it leads its own group and has its
    handlers in. The resource tracker is brought up first, on purpose: its
    own spawn ends by *unblocking* these two signals on the calling thread
    (bpo-33613), which would undo the mask under a first launch.
    """
    with contextlib.suppress(Exception):
        _tracker.ensure_running()
    old = signal.pthread_sigmask(signal.SIG_BLOCK, _GUARD)
    try:
        proc.start()
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, old)


class _Landing:
    """Where a launch on a thread meets its awaiter, so no worker is lost between them.

    The thread lands the id under the lock; the awaiter abandons under the
    same lock. Whichever comes second kills the worker: the thread when it
    finds the landing abandoned, the awaiter when it finds an id landed.
    """

    __slots__ = ("_abandoned", "_lock", "_wid")

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._abandoned = False
        self._wid: int | None = None

    def land(self, wid: int) -> bool:
        """Record the launched id; False when nobody is left to take it."""
        with self._lock:
            if self._abandoned:
                return False
            self._wid = wid
            return True

    def abandon(self) -> int | None:
        """Give up on the launch. An id that already landed is the caller's to kill."""
        with self._lock:
            self._abandoned = True
            return self._wid


class WorkerPool:
    """N worker processes owned by one bracket; the fleet itself is the fabric.

    Provided once at the top of a tree, usually through the ``pool(...)``
    preset::

        Provide(WorkerPool, {"init": With(...), "name": "nu", "spares": 2}, body)

    and from there the interactions in this fabric address workers by id:
    ``Launch`` takes a warm spare or spawns one and yields its id,
    ``Dispatch`` ships a resident tree to it and yields the job id,
    ``Teleport`` does request/reply, ``Interrupt``, ``Stop`` and ``Kill`` end
    work or the worker, ``Status`` and ``Wait`` read it. Bracket close stops
    every worker still up, all at once, under one budget.

    Args:
        init: the lifecycle bracket every worker comes up holding. Shipped to
            the child, entered there, and torn down LIFO when the worker
            stops. ``Launch`` can override it per worker.
        name: the pool's name. Each worker runs titled ``nu:{name}-{wid}``.
        grace: the whole budget for ending a worker, and for the pool's
            close: the ``stop`` frame until 60% of it, then SIGINT, SIGTERM at
            80%, SIGKILL at 95%. ``Stop`` takes its own. Also how long a kill
            waits for the process to be reaped.
        spares: how many idle workers to keep up, holding the pool's
            ``init``, so a ``Launch`` takes one instead of waiting for a
            spawn. Refilled in the background, best effort.
        ready_timeout: how long a launch waits for the child to finish
            building its Context.
        ack_timeout: how long a dispatch waits for the child to accept it.
        start_method: the ``multiprocessing`` start method. Only ``"spawn"``
            is accepted: the child gets a clean interpreter, and a forked one
            would carry every other worker's pipe ends and sentinels along.
            ``init`` travels through ``nu.lang.wire`` (cloudpickle), so
            closures and locally defined classes go along.

    Notes:
        - No size, no scheduling, no acquire/release. The pool owns processes
          and nothing else; policy is the caller's.
        - Ids are monotonic and never reused, so a stale id reads as gone
          rather than as a different worker.
        - Every method that waits has an async twin that never blocks the
          loop (``alaunch``, ``adispatch``, ``ateleport``, ``acancel``,
          ``astop``, ``akill``, ``await_exit``, ``acleanup``). The sync ones
          block the calling thread, always bounded except for a ``teleport``
          (which waits as long as its body runs) and a ``wait`` with no
          timeout. ``status``, ``workers`` and ``interrupt`` never wait and
          serve both.
        - Nothing outlives the bracket. Close refuses new launches, waits for
          launches and stops in flight, runs the ladder on every worker at
          once and returns by ``grace``. ``acleanup`` does all that on the
          loop; a cancellation landing in it SIGKILLs every group and goes
          on up. A second Ctrl+C in the sync ``cleanup`` does the same.
        - Nothing outlives the host either. Every worker leads its own
          process group and watches the parent: when the host is gone,
          however it went, the worker ends its group itself.
        - A worker that dies by itself is seen at once, through its exit
          watch, not its pipe: pending requests fail with ``WorkerGone``
          carrying cause and exit code, it drops out of ``workers``, and its
          status stays readable.
    """

    def __init__(
        self,
        *,
        init: _LifecycleBracket | None = None,
        name: str = "nu",
        grace: float = 5.0,
        spares: int = 0,
        ready_timeout: float = 30.0,
        ack_timeout: float = 10.0,
        start_method: str = "spawn",
    ) -> None:
        if start_method != "spawn":
            msg = (
                f"WorkerPool only supports the 'spawn' start method, not {start_method!r}: "
                "a forked worker inherits every other worker's pipe ends and sentinels"
            )
            raise ValueError(msg)
        self.init = init
        self.name = name
        self.grace = grace
        self.spares = spares
        self.ready_timeout = ready_timeout
        self.ack_timeout = ack_timeout
        self.start_method = start_method
        self._ids = itertools.count()
        self._lock = threading.Lock()
        # Live workers, spares included; ``_shelf`` is the spares' ids, in
        # the order they came up. A worker being ended moves to ``_dying``
        # until its exit is recorded, and then to ``_records``.
        self._workers: dict[int, _WorkerHandle] = {}
        self._shelf: list[int] = []
        # Spares between their spawn and the shelf: registered, not handed out.
        self._warming: set[int] = set()
        self._dying: dict[int, _WorkerHandle] = {}
        self._records: collections.OrderedDict[int, WorkerStatus] = collections.OrderedDict()
        # Close against the threads a cancelled ``alaunch`` or a refill
        # leaves behind: a launch counts itself in between spawn and
        # registration, and ``cleanup`` waits on that through ``_changed``.
        self._changed = threading.Condition(self._lock)
        self._closed = False
        self._launching = 0
        self._filling = 0

    # --- lifecycle -------------------------------------------------------

    def setup(self, ctx: Context) -> None:
        """Start filling the spares shelf, if there is one. Nothing else to build."""
        self._refill()

    async def asetup(self, ctx: Context) -> None:
        """Async lifecycle. The shelf fills on threads either way."""
        self.setup(ctx)

    def cleanup(self) -> None:
        """Stop every worker at once, launches and stops in flight included, within ``grace``.

        Closes the pool first, so no launch gets past this point. Then, all
        inside one budget: wait for launches between spawn and registration
        to land, run the ladder on every worker (newest first, all in
        parallel), wait for workers other threads are ending. Whatever is
        still up at the deadline has had its SIGKILL.

        A ``BaseException`` landing meanwhile (a second Ctrl+C) ends it the
        hard way: SIGKILL to every group still known, no waits, and the
        exception goes on up.
        """
        start = time.monotonic()
        end = start + self.grace
        try:
            with self._changed:
                self._closed = True
                self._changed.wait_for(
                    lambda: self._launching == 0, timeout=max(end - time.monotonic(), 0.0)
                )
                handles = self._close_books()
            _climb(handles, start, self.grace)
            with self._changed:
                self._changed.wait_for(
                    lambda: not self._dying, timeout=max(end - time.monotonic(), 0.0)
                )
                left = list(self._dying.values())
            for handle in left:
                handle.kill_now()
        except BaseException:
            self._kill_everything()
            raise

    async def acleanup(self) -> None:
        """Async ``cleanup``: the same ladder, on the loop, with no thread and no blocking.

        ``asyncio.to_thread(self.cleanup)`` would be the obvious shape and is
        the bug this avoids: a cancellation on the enclosing task raises out
        of the await at once and abandons the cleanup thread, leaving
        processes alive after the tree has completed. Here every wait is an
        await on exit futures, and a cancellation landing in one SIGKILLs
        every group the pool knows before it goes on up, so nothing is left
        running either way.
        """
        start = time.monotonic()
        end = start + self.grace
        try:
            with self._lock:
                self._closed = True
            await _until(lambda: self._launching == 0, end)
            with self._lock:
                handles = self._close_books()
            await _aclimb(handles, start, self.grace)
            await _until(lambda: not self._dying, end)
            with self._lock:
                left = list(self._dying.values())
            for handle in left:
                handle.kill_now()
        except BaseException:
            self._kill_everything()
            raise

    def _close_books(self) -> list[_WorkerHandle]:
        """Move every live worker to dying; every handle being ended, newest first. Lock held."""
        self._dying.update(self._workers)
        self._workers.clear()
        self._shelf.clear()
        self._warming.clear()
        return [self._dying[wid] for wid in sorted(self._dying, reverse=True)]

    def _kill_everything(self) -> None:
        """SIGKILL every process still known, with no waits. For an interrupted close."""
        with self._lock:
            self._closed = True
            known = [*self._workers.values(), *self._dying.values()]
        for handle in known:
            handle.kill_now()

    # --- books -------------------------------------------------------------

    def _on_exit(self, handle: _WorkerHandle) -> None:
        """A worker's exit is recorded (reader thread): off the books, into the records."""
        record = handle.status()
        with self._changed:
            wid = handle.wid
            if self._workers.get(wid) is handle:
                del self._workers[wid]
            if self._dying.get(wid) is handle:
                del self._dying[wid]
            if wid in self._shelf:
                self._shelf.remove(wid)
            self._warming.discard(wid)
            self._keep(record)
            self._changed.notify_all()

    def _keep(self, record: WorkerStatus) -> None:
        """File an exited worker's record, dropping the oldest past the bound. Lock held."""
        self._records[record.wid] = record
        while len(self._records) > _KEPT_EXITED:
            self._records.popitem(last=False)

    def _find(self, wid: object) -> tuple[_WorkerHandle | None, WorkerStatus | None]:
        """The live handle for ``wid``, or its exited record; both None if unknown."""
        with self._lock:
            handle = self._workers.get(wid) or self._dying.get(wid)  # type: ignore[call-overload]
            record = self._records.get(wid) if handle is None else None  # type: ignore[call-overload]
        return handle, record

    def _target(self, wid: object) -> _WorkerHandle:
        """The live handle a request goes to. Gone ones raise ``WorkerGone``, unknown ones ``UnknownWorker``."""
        handle, record = self._find(wid)
        if handle is not None:
            return handle
        if record is not None:
            raise WorkerGone(
                f"worker {wid} is gone ({record.cause}, exit code {record.exitcode})",
                wid=record.wid,
                cause=record.cause,
                exitcode=record.exitcode,
            )
        raise UnknownWorker(wid)

    def _ending(self, wid: object) -> tuple[_WorkerHandle | None, WorkerStatus | None]:
        """Take worker ``wid`` off the live books for an end; its handle, or its record if gone."""
        with self._lock:
            handle = self._workers.pop(wid, None)  # type: ignore[call-overload]
            if handle is not None:
                self._dying[handle.wid] = handle
                if handle.wid in self._shelf:
                    self._shelf.remove(handle.wid)
            else:
                handle = self._dying.get(wid)  # type: ignore[call-overload]
            record = self._records.get(wid) if handle is None else None  # type: ignore[call-overload]
        return handle, record

    # --- launch ------------------------------------------------------------

    def launch(self, init: _LifecycleBracket | None = None) -> int:
        """A worker ready to take requests: a warm spare when there is one, else a fresh spawn.

        ``init`` overrides the pool's bracket for this worker only, and a
        worker with its own bracket is always spawned cold; ``None`` means
        "the pool's". Returns once the child said ``ready``. A child that
        fails to come up is ended before the error propagates.
        """
        if init is None:
            wid = self._take_spare()
            if wid is not None:
                return wid
        return self._launch_cold(init)

    def _take_spare(self) -> int | None:
        """A spare off the shelf, or None; the shelf refills behind it. No waits."""
        if self.spares <= 0:
            return None
        with self._lock:
            wid = None
            while self._shelf:
                candidate = self._shelf.pop(0)
                handle = self._workers.get(candidate)
                if handle is not None and not handle.exited:
                    wid = candidate
                    break
        self._refill()
        return wid

    def _launch_cold(self, init: _LifecycleBracket | None, *, spare: bool = False) -> int:
        """Spawn a worker, register it, wait for ``ready``, return its id.

        A ``spare`` counts as warming from its id on, so ``workers`` never
        lists it; whoever launched it moves it to the shelf.
        """
        bracket = self.init if init is None else init
        with self._changed:
            if self._closed:
                raise PoolClosed("the pool is closed")
            wid = next(self._ids)
            self._launching += 1
            if spare:
                self._warming.add(wid)
        try:
            return self._bring_up(wid, bracket)
        except BaseException:
            if spare:
                with self._lock:
                    self._warming.discard(wid)
            raise

    def _bring_up(self, wid: int, bracket: _LifecycleBracket | None) -> int:
        """``_launch_cold``'s rest, once the id is taken and counted as launching."""
        try:
            handle = self._spawn(wid, bracket)
        except BaseException:
            with self._changed:
                self._launching -= 1
                self._changed.notify_all()
            raise
        with self._changed:
            self._launching -= 1
            late = self._closed
            # Registered in the same step that counts the launch out, so
            # ``cleanup`` never sees the count at zero with this worker
            # missing from the books. Closed meanwhile, it is ours to end.
            if handle.exited:
                self._keep(handle.status())  # gone before it was ever on the books
            elif late:
                self._dying[wid] = handle
            else:
                self._workers[wid] = handle
            self._changed.notify_all()
        if late:
            handle.kill_now()
            handle.wait_exit(self.grace)
            raise PoolClosed("the pool is closed")
        try:
            handle.wait_ready(self.ready_timeout)
        except BaseException as exc:
            self._fail_launch(handle, "init_failed" if isinstance(exc, Exception) else "killed")
            raise
        return wid

    def _fail_launch(self, handle: _WorkerHandle, hint: str) -> None:
        """A worker that did not come up: end it, unless a close already took it over."""
        with self._lock:
            owned = self._workers.pop(handle.wid, None) is handle
            if owned:
                self._dying[handle.wid] = handle
        if owned:
            handle.kill_now(hint)
            handle.wait_exit(self.grace)

    def _spawn(self, wid: int, bracket: _LifecycleBracket | None) -> _WorkerHandle:
        """Start worker ``wid``'s process and hand back its handle.

        Spawned with SIGINT and SIGTERM masked, and not as a daemon process,
        so its bodies may use ``multiprocessing`` themselves.
        """
        mp_ctx: BaseContext = _mp.get_context(self.start_method)
        title = f"nu:{self.name}-{wid}"
        parent_conn, child_conn = mp_ctx.Pipe(duplex=True)
        proc = mp_ctx.Process(  # type: ignore[attr-defined]
            target=_pool_worker_main,
            args=(child_conn, wire.dumps(bracket), title),
            name=title,
        )
        _start_masked(proc)
        child_conn.close()  # the parent keeps its end only
        try:
            return _WorkerHandle(wid, proc, parent_conn, name=title, on_exit=self._on_exit)
        except BaseException:
            # Started, but with no handle nobody could ever reach it. No
            # group known yet, so the pid alone.
            with contextlib.suppress(Exception):
                proc.kill()
                proc.join(timeout=self.grace)
            with contextlib.suppress(Exception):
                parent_conn.close()
            raise

    def _refill(self) -> None:
        """Top the shelf back up to ``spares``, each launch on a daemon thread of its own."""
        if self.spares <= 0:
            return
        with self._lock:
            if self._closed:
                return
            missing = self.spares - len(self._shelf) - self._filling
            if missing <= 0:
                return
            self._filling += missing
        for _ in range(missing):
            threading.Thread(target=self._fill_one, name="nu-mp-pool-spare", daemon=True).start()

    def _fill_one(self) -> None:
        """Launch one spare and shelve it. Best effort: a failure here has nobody to raise at."""
        wid: int | None = None
        try:
            wid = self._launch_cold(None, spare=True)
        except BaseException:
            log.debug("a spare failed to come up", exc_info=True)
        finally:
            with self._lock:
                self._filling -= 1
                if wid is not None:
                    self._warming.discard(wid)
                    # A close meanwhile took the worker over; it is ending it.
                    if not self._closed and wid in self._workers:
                        self._shelf.append(wid)

    # --- run work ----------------------------------------------------------

    def dispatch(self, wid: object, tree: object, attrs: dict | None = None) -> int:
        """Ship ``tree`` to worker ``wid`` and return its job id once the child acked it.

        The body keeps running in the child afterwards. Nothing is ever
        awaited on its result, which is what makes this usable for resident,
        never-terminating trees. ``cancel`` takes the job id. A caller that
        does not get it, because the ack did not come within ``ack_timeout``
        or an interrupt landed, could never cancel the body, so it is
        cancelled for them. An error the body raises later is logged and
        kept on the worker's status.
        """
        handle = self._target(wid)
        token, reply = handle.request("dispatch", tree, attrs)
        try:
            reply.wait(self.ack_timeout)
        except BaseException:
            handle.cancel(token)
            raise
        return token

    def teleport(self, wid: object, tree: object, attrs: dict | None = None) -> object:
        """Ship ``tree`` to worker ``wid`` and block for its value.

        Interrupted while it waits (a ``KeyboardInterrupt``), the body is
        cancelled in the child too. A body ended by ``interrupt`` raises
        ``Interrupted``; a worker gone meanwhile raises ``WorkerGone``.
        """
        handle = self._target(wid)
        token, reply = handle.request("exec", tree, attrs)
        try:
            return reply.wait(None)
        except BaseException:
            handle.cancel(token)
            raise

    def cancel(self, wid: object, job: int) -> None:
        """Cancel job ``job`` on worker ``wid``: the task running it in the child.

        The body unwinds through its own cleanup there. Fire and forget:
        nothing waits for that to finish. A no-op on an unknown or gone id or
        a job that already finished.
        """
        handle, _ = self._find(wid)
        if handle is not None:
            handle.cancel(job)

    def interrupt(self, wid: object) -> None:
        """SIGINT to worker ``wid``'s group: every job on it ends, the worker serves on.

        A body blocked in sync code gets ``KeyboardInterrupt``, the rest are
        cancelled; each ends with ``Interrupted`` at its caller. Subprocesses
        a body started get the SIGINT too, as from a terminal's Ctrl+C. Never
        blocks; a no-op on an unknown or gone id.
        """
        handle, _ = self._find(wid)
        if handle is not None:
            handle.interrupt()

    # --- end workers ---------------------------------------------------------

    def stop(self, wid: object, grace: float | None = None) -> WorkerStatus:
        """End worker ``wid`` politely, escalating within ``grace``; its status after.

        The ladder: the ``stop`` frame (its jobs are cancelled, ``finally``
        blocks and the init teardown run, it exits 0), SIGINT to its group at
        60% of ``grace``, SIGTERM at 80%, SIGKILL at 95%. Returns once it
        exited, and by ``grace`` either way. ``grace`` defaults to the pool's.

        A worker already gone answers its record at once. An id never
        launched raises ``UnknownWorker``. Interrupted midway (a
        ``KeyboardInterrupt``), the worker gets SIGKILL before the exception
        goes on up.
        """
        handle, record = self._ending(wid)
        if handle is None:
            if record is None:
                raise UnknownWorker(wid)
            return record
        try:
            _climb([handle], time.monotonic(), self.grace if grace is None else grace)
        except BaseException:
            handle.kill_now()
            raise
        return handle.status()

    def kill(self, wid: object) -> None:
        """SIGKILL worker ``wid``'s group now, and wait (up to ``grace``) for the reap.

        No teardown runs: this is the rung for a worker that will not stop.
        Idempotent, and a no-op on an unknown or gone id. Pending requests
        fail with ``WorkerGone`` (cause ``killed``).
        """
        handle, _ = self._ending(wid)
        if handle is not None:
            handle.kill_now()
            handle.wait_exit(self.grace)

    # --- reads -------------------------------------------------------------

    def status(self, wid: object) -> WorkerStatus:
        """What the pool knows of worker ``wid``, alive or gone. Never blocks.

        Readable for the last ``_KEPT_EXITED`` exited workers too. An id never
        launched here (or whose record was dropped) raises ``UnknownWorker``.
        """
        handle, record = self._find(wid)
        if handle is not None:
            return handle.status()
        if record is not None:
            return record
        raise UnknownWorker(wid)

    def wait(self, wid: object, timeout: float | None = None) -> WorkerStatus:
        """Block until worker ``wid`` has exited, at most ``timeout``; its status then.

        The exit is seen through the process itself, so a pipe a grandchild
        still holds open does not keep this waiting. On a timeout the status
        is returned as it stands (``state`` is not ``"exited"``). A worker
        already gone answers at once; an unknown id raises ``UnknownWorker``.
        """
        handle, record = self._find(wid)
        if handle is None:
            if record is None:
                raise UnknownWorker(wid)
            return record
        handle.wait_exit(timeout)
        return handle.status()

    def workers(self) -> list[int]:
        """The live workers handed out, in launch order. Spares (warming or shelved) and gone ones are not."""
        with self._lock:
            spares = {*self._shelf, *self._warming}
            return sorted(wid for wid in self._workers if wid not in spares)

    # --- async twins -------------------------------------------------------

    async def alaunch(self, init: _LifecycleBracket | None = None) -> int:
        """Async ``launch``: a spare at once, else spawn + wait for READY off-thread.

        Cancelling the await does not stop the thread, so the launch runs
        to its end there. A worker that comes up with nobody left to take
        it is killed, by whichever side finishes second.
        """
        if init is None:
            wid = self._take_spare()
            if wid is not None:
                return wid
        landing = _Landing()
        try:
            return await asyncio.to_thread(self._launch_into, landing, init)
        except BaseException:
            wid = landing.abandon()
            if wid is not None:
                self._kill_nowait(wid)
            raise

    def _launch_into(self, landing: _Landing, init: _LifecycleBracket | None) -> int:
        """``launch`` on a thread, handing the id over through ``landing``."""
        wid = self._launch_cold(init)
        if not landing.land(wid):
            self.kill(wid)
        return wid

    def _kill_nowait(self, wid: object) -> _WorkerHandle | None:
        """SIGKILL worker ``wid`` and take it off the books; nothing waited for."""
        handle, _ = self._ending(wid)
        if handle is not None:
            handle.kill_now()
        return handle

    async def adispatch(self, wid: object, tree: object, attrs: dict | None = None) -> int:
        """Async ``dispatch``: the reader thread wakes it on the ack, no thread is held meanwhile.

        A caller cancelled before it has the job id could never cancel the
        body, so the pool cancels it for them; the same when the ack does
        not come in time. The frame and the cancel go out on threads, for
        the reasons ``ateleport`` gives.
        """
        handle = self._target(wid)
        token, reply = handle.open(asyncio.get_running_loop())
        try:
            await asyncio.to_thread(handle.send, "dispatch", token, reply, tree, attrs)
            await reply.await_(self.ack_timeout)
        except BaseException:
            self._cancel_later(handle, token)
            raise
        return token

    async def ateleport(self, wid: object, tree: object, attrs: dict | None = None) -> object:
        """Async ``teleport``: the reader thread wakes it, no thread is held meanwhile.

        Cancelling the await cancels the body in the child: its task is
        cancelled there and unwinds through its own cleanup. The await does
        not wait for that. A worker that dies meanwhile raises ``WorkerGone``.

        The frame goes out off-thread, since a child that is not reading its
        pipe can block a send. So does the cancel, on a thread of its own,
        for the same reason and because the loop may be closing by then.
        """
        handle = self._target(wid)
        token, reply = handle.open(asyncio.get_running_loop(), job=True)
        try:
            await asyncio.to_thread(handle.send, "exec", token, reply, tree, attrs)
            return await reply.await_()
        except asyncio.CancelledError:
            self._cancel_later(handle, token)
            raise

    async def acancel(self, wid: object, job: int) -> None:
        """Async ``cancel``: the frame goes out on a thread, nothing is awaited."""
        handle, _ = self._find(wid)
        if handle is not None:
            self._cancel_later(handle, job)

    @staticmethod
    def _cancel_later(handle: _WorkerHandle, token: int) -> None:
        """Send the cancel for ``token`` on a thread of its own, so the loop never waits on a pipe."""
        threading.Thread(
            target=handle.cancel,
            args=(token,),
            name=f"nu-mp-pool-cancel-{handle.wid}",
            daemon=True,
        ).start()

    async def astop(self, wid: object, grace: float | None = None) -> WorkerStatus:
        """Async ``stop``: the same ladder, awaited on the loop.

        Cancelled midway, the worker gets SIGKILL before the cancellation
        goes on up, so a cancelled stop never leaves it half-stopped.
        """
        handle, record = self._ending(wid)
        if handle is None:
            if record is None:
                raise UnknownWorker(wid)
            return record
        try:
            await _aclimb([handle], time.monotonic(), self.grace if grace is None else grace)
        except BaseException:
            handle.kill_now()
            raise
        return handle.status()

    async def akill(self, wid: object) -> None:
        """Async ``kill``: SIGKILL now, then await the reap (up to ``grace``) on the loop.

        The signal is out before the first await, so a cancelled ``akill``
        has still killed the worker; the reader thread records it.
        """
        handle = self._kill_nowait(wid)
        if handle is not None:
            await handle.await_exit(self.grace)

    async def await_exit(self, wid: object, timeout: float | None = None) -> WorkerStatus:
        """Async ``wait``: no thread is held, the reader thread wakes it.

        Named apart from the sync one only because ``await`` is a keyword.
        Cancelling it just drops the waiter.
        """
        handle, record = self._find(wid)
        if handle is None:
            if record is None:
                raise UnknownWorker(wid)
            return record
        await handle.await_exit(timeout)
        return handle.status()
