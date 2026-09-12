"""``WorkerPool``: the fabric that owns N worker processes.

Where ``nu.mp.MpWorker`` is the fabric of *one* process - its whole lifecycle
is the ``Provide`` bracket - ``WorkerPool`` is the fabric of the *fleet*. One
``Provide`` at the top of a tree owns ``{id -> process}``, and because the
fabric spans many processes it legitimately carries interactions over them:
launch one, kill one, run a tree on one.

Deliberately absent: size, warmth, scheduling, acquire/release. Those are
policy and belong to callers.

Parent-side shape, per worker:

- a ``Process`` and its half of a duplex ``Pipe``
- a daemon reader thread draining that pipe and resolving waiters by token
- a set of tokens that are dispatched but not finished, which is what
  ``running`` reads

Worker ids are monotonic ints and are never reused, so a stale id is
detectably dead rather than silently a different worker.
"""

from __future__ import annotations

import asyncio
import contextlib
import itertools
import multiprocessing as _mp
import threading
from typing import TYPE_CHECKING

from ._worker import _pool_worker_main


if TYPE_CHECKING:
    from multiprocessing.connection import Connection
    from multiprocessing.context import BaseContext, Process

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Context


__all__ = ["UnknownWorker", "WorkerGone", "WorkerPool"]


class WorkerGone(RuntimeError):  # noqa: N818 - a state, not an error kind
    """Raised when the worker a call targets died before it could answer."""


class UnknownWorker(KeyError):  # noqa: N818 - a state, not an error kind
    """Raised when a worker id was never launched, or was already killed."""


class _Reply:
    """A one-shot slot a reader thread fills and a caller waits on."""

    __slots__ = ("event", "kind", "value")

    def __init__(self) -> None:
        self.event = threading.Event()
        self.kind: str | None = None
        self.value: object = None

    def set(self, kind: str, value: object) -> None:
        """Fill the slot and wake the waiter."""
        self.kind = kind
        self.value = value
        self.event.set()

    def wait(self, timeout: float | None) -> object:
        """Block for the reply; raise what came back, or time out."""
        if not self.event.wait(timeout):
            raise TimeoutError("worker did not reply in time")
        if self.kind == "err":
            raise self.value  # type: ignore[misc]
        if self.kind == "gone":
            raise WorkerGone(str(self.value))
        return self.value


class _WorkerHandle:
    """Parent-side handle on one worker process: pipe, reader thread, bookkeeping."""

    def __init__(self, wid: int, proc: Process, conn: Connection, *, grace: float) -> None:
        self.wid = wid
        self.proc = proc
        self.conn = conn
        self.grace = grace
        self._tokens = itertools.count()
        self._send_lock = threading.Lock()
        self._state = threading.Lock()
        self._pending: dict[int, _Reply] = {}
        self._running: set[int] = set()
        self._ready = threading.Event()
        self._ready_error: BaseException | None = None
        self._closed = False
        self._reader = threading.Thread(
            target=self._read_loop,
            name=f"nu-mp-pool-reader-{wid}",
            daemon=True,
        )
        self._reader.start()

    # --- reader thread ---------------------------------------------------

    def _read_loop(self) -> None:
        """Drain the pipe, resolving waiters and running-tokens until EOF."""
        try:
            while True:
                try:
                    frame = self.conn.recv()
                except (EOFError, OSError, ValueError):
                    break
                self._handle(frame)
        finally:
            self._abandon(WorkerGone(f"worker {self.wid} is gone"))

    def _handle(self, frame: tuple) -> None:
        kind = frame[0]
        if kind == "ready":
            self._ready.set()
            return
        if kind == "failed":
            self._ready_error = frame[1]
            self._ready.set()
            return
        token = frame[1]
        with self._state:
            if kind == "ack":
                self._running.add(token)
            else:
                self._running.discard(token)
            reply = self._pending.pop(token, None)
        if reply is None:
            return
        if kind == "ack":
            reply.set("ack", None)
        elif kind == "ok":
            reply.set("ok", frame[2])
        elif kind == "err":
            reply.set("err", frame[2])

    def _abandon(self, exc: BaseException) -> None:
        """Fail everything still waiting; used when the worker dies."""
        with self._state:
            self._closed = True
            pending = list(self._pending.values())
            self._pending.clear()
            self._running.clear()
        for reply in pending:
            reply.set("gone", exc)
        if not self._ready.is_set():
            self._ready_error = exc
            self._ready.set()

    # --- parent-side calls -----------------------------------------------

    def wait_ready(self, timeout: float | None) -> None:
        """Block until the child has built its Context, or blow up trying."""
        if not self._ready.wait(timeout):
            raise TimeoutError(f"worker {self.wid} did not come up in time")
        if self._ready_error is not None:
            raise self._ready_error

    def request(self, kind: str, tree: object, attrs: dict | None) -> _Reply:
        """Register a waiter, send the frame, hand the slot back."""
        token = next(self._tokens)
        reply = _Reply()
        with self._state:
            if self._closed:
                raise WorkerGone(f"worker {self.wid} is gone")
            self._pending[token] = reply
        try:
            with self._send_lock:
                self.conn.send((kind, token, tree, attrs))
        except (OSError, ValueError, BrokenPipeError) as exc:
            with self._state:
                self._pending.pop(token, None)
            raise WorkerGone(f"worker {self.wid} is gone") from exc
        return reply

    @property
    def running(self) -> bool:
        """Whether any dispatched body on this worker is still executing."""
        with self._state:
            return bool(self._running)

    def terminate(self) -> None:
        """Kill the process for real, then reap it. Never waits on the child."""
        with self._state:
            self._closed = True
        proc = self.proc
        with contextlib.suppress(Exception):
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=self.grace)
                if proc.is_alive():
                    proc.kill()
                    proc.join(timeout=self.grace)
            else:
                proc.join(timeout=self.grace)
        # The child's end is closed by now, so the reader sees EOF and exits.
        self._reader.join(timeout=self.grace)
        with contextlib.suppress(Exception):
            self.conn.close()
        with contextlib.suppress(Exception):
            proc.close()
        self._abandon(WorkerGone(f"worker {self.wid} was killed"))


class WorkerPool:
    """N worker processes owned by one bracket; the fleet itself is the fabric.

    Provided once at the top of a tree::

        Provide(WorkerPool, {"init": With(...), "name": "nu"}, body)

    and from there the interactions in this fabric address workers by id:
    ``Launch`` spawns one and yields its id, ``Dispatch`` ships a resident
    tree to it, ``Teleport`` does request/reply, ``Kill`` ends it. Bracket
    close kills every worker that is still up, newest first.

    Args:
        init: the lifecycle bracket every worker comes up holding. Shipped to
            the child, entered there, and torn down LIFO when the worker
            dies. ``Launch`` can override it per worker.
        start_method: the ``multiprocessing`` start method. ``"spawn"`` by
            default, so the child gets a clean interpreter and ``init`` must
            be pickleable (top-level in a module, no closures).
        name: process name prefix; the worker id is appended.
        ready_timeout: how long ``launch`` waits for the child to finish
            building its Context.
        grace: how long a terminate is given before it escalates to SIGKILL,
            and how long each reap step waits.

    Notes:
        - No size, no warmth, no scheduling, no acquire/release. The pool owns
          processes and nothing else; policy is the caller's.
        - Ids are monotonic and never reused, so a stale id reads as dead
          rather than as a different worker.
        - Both lifecycles are supported. ``acleanup`` does its work inline
          with no await points at all, so a cancellation landing on the
          enclosing task cannot abandon a half-torn-down fleet.
    """

    def __init__(
        self,
        *,
        init: _LifecycleBracket | None = None,
        start_method: str = "spawn",
        name: str = "nu",
        ready_timeout: float = 30.0,
        grace: float = 2.0,
    ) -> None:
        self.init = init
        self.start_method = start_method
        self.name = name
        self.ready_timeout = ready_timeout
        self.grace = grace
        self._ids = itertools.count()
        self._lock = threading.Lock()
        self._workers: dict[int, _WorkerHandle] = {}

    # --- lifecycle -------------------------------------------------------

    def setup(self, ctx: Context) -> None:
        """Nothing to build: the pool starts empty and grows on ``Launch``."""

    def cleanup(self) -> None:
        """Kill and reap every live worker, newest first."""
        with self._lock:
            handles = [self._workers.pop(wid) for wid in sorted(self._workers, reverse=True)]
        for handle in handles:
            handle.terminate()

    async def asetup(self, ctx: Context) -> None:
        """Async lifecycle. No awaits: there is no work to move off-thread."""
        self.setup(ctx)

    async def acleanup(self) -> None:
        """Async lifecycle, deliberately with no await points.

        ``asyncio.to_thread(self.cleanup)`` would be the obvious shape and is
        the bug we are avoiding: a cancellation on the enclosing task raises
        out of the await immediately and abandons the cleanup thread, leaving
        child processes alive after the tree has completed. Terminating and
        reaping is short work, so it runs inline where cancellation cannot
        reach it.
        """
        self.cleanup()

    # --- fleet -----------------------------------------------------------

    def _handle(self, wid: object) -> _WorkerHandle:
        with self._lock:
            handle = self._workers.get(wid)  # type: ignore[arg-type]
        if handle is None:
            raise UnknownWorker(wid)
        return handle

    def launch(self, init: _LifecycleBracket | None = None) -> int:
        """Spawn a worker, wait for READY, return its id.

        ``init`` overrides the pool default for this worker only; ``None``
        means "use the pool's".
        """
        bracket = self.init if init is None else init
        with self._lock:
            wid = next(self._ids)
        mp_ctx: BaseContext = _mp.get_context(self.start_method)
        parent_conn, child_conn = mp_ctx.Pipe(duplex=True)
        proc = mp_ctx.Process(
            target=_pool_worker_main,
            args=(child_conn, bracket),
            name=f"{self.name}-{wid}",
            daemon=True,
        )
        proc.start()
        child_conn.close()  # the parent keeps its end only
        handle = _WorkerHandle(wid, proc, parent_conn, grace=self.grace)
        with self._lock:
            self._workers[wid] = handle
        try:
            handle.wait_ready(self.ready_timeout)
        except BaseException:
            self.kill(wid)
            raise
        return wid

    def dispatch(self, wid: object, tree: object, attrs: dict | None = None) -> None:
        """Ship ``tree`` to worker ``wid`` and return once the child acked it.

        The body keeps running in the child afterwards. Nothing is ever
        awaited on its result, which is what makes this usable for resident,
        never-terminating trees.
        """
        reply = self._handle(wid).request("dispatch", tree, attrs)
        reply.wait(self.ready_timeout)

    def teleport(self, wid: object, tree: object, attrs: dict | None = None) -> object:
        """Ship ``tree`` to worker ``wid`` and block for its value."""
        reply = self._handle(wid).request("exec", tree, attrs)
        return reply.wait(None)

    def kill(self, wid: object) -> None:
        """Terminate worker ``wid`` now and reap it. A no-op on an unknown id."""
        with self._lock:
            handle = self._workers.pop(wid, None)  # type: ignore[arg-type]
        if handle is None:
            return
        handle.terminate()

    def alive(self, wid: object) -> bool:
        """Whether worker ``wid`` is a process that is still up."""
        with self._lock:
            handle = self._workers.get(wid)  # type: ignore[arg-type]
        return handle is not None and handle.proc.is_alive()

    def running(self, wid: object) -> bool:
        """Whether a body dispatched to worker ``wid`` is still executing."""
        with self._lock:
            handle = self._workers.get(wid)  # type: ignore[arg-type]
        return handle is not None and handle.running

    def workers(self) -> list[int]:
        """Every worker id the pool still tracks, in launch order."""
        with self._lock:
            return sorted(self._workers)

    # --- async wrappers --------------------------------------------------

    async def alaunch(self, init: _LifecycleBracket | None = None) -> int:
        """Async ``launch``: spawn + wait for READY off-thread."""
        return await asyncio.to_thread(self.launch, init)

    async def adispatch(self, wid: object, tree: object, attrs: dict | None = None) -> None:
        """Async ``dispatch``: wait for the ack off-thread."""
        await asyncio.to_thread(self.dispatch, wid, tree, attrs)

    async def ateleport(self, wid: object, tree: object, attrs: dict | None = None) -> object:
        """Async ``teleport``: wait for the reply off-thread."""
        return await asyncio.to_thread(self.teleport, wid, tree, attrs)

    async def akill(self, wid: object) -> None:
        """Async ``kill``, shielded so a cancellation still reaps the process."""
        await asyncio.shield(asyncio.to_thread(self.kill, wid))
