"""``WorkerPool``: the fabric that owns N worker processes.

Where ``nustd.mp.MpWorker`` is the fabric of *one* process - its whole lifecycle
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
- per request in flight, a flag for whether its frame is out yet, so a
  cancel is never sent ahead of the request it cancels
- an exit record: the process's exit code once it is gone, and the asyncio
  futures of whoever is waiting on that, woken from the reader thread

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

from nu.lang import wire

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
        if self.kind == "err":
            raise self.value  # type: ignore[misc]
        if self.kind == "gone":
            raise WorkerGone(str(self.value))
        return self.value

    def wait(self, timeout: float | None) -> object:
        """Block for the reply; raise what came back, or time out."""
        if not self.event.wait(timeout):
            raise TimeoutError("worker did not reply in time")
        return self.result()

    async def await_(self) -> object:
        """Wait for the reply on the loop it was made for; raise what came back."""
        await self.future  # type: ignore[misc]
        return self.result()


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
        self._terminating = False
        # Exit record. ``_exited`` flips once, from whichever thread sees the
        # process gone first; ``_exit_waiters`` are futures on some loop, each
        # woken through that loop's ``call_soon_threadsafe``.
        self._exited = threading.Event()
        self.exitcode: int | None = None
        self._exit_waiters: list[tuple[asyncio.AbstractEventLoop, asyncio.Future]] = []
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
                    frame = wire.recv(self.conn)
                except (EOFError, OSError, ValueError):
                    break
                self._handle(frame)
        finally:
            self._abandon(WorkerGone(f"worker {self.wid} is gone"))
            if not self._terminating:
                # A kill in progress owns the reap and records the code itself.
                self._mark_exited(self._reap_code())

    def _reap_code(self) -> int | None:
        """After EOF: wait for the process itself to end, then read its code.

        EOF means the child closed its end of the pipe, which it does on the
        way out, a moment before the process is actually gone. The sentinel
        becomes readable only when it is, and waiting on it reaps nothing, so
        ``terminate`` joining the same process concurrently is not disturbed.
        A process ``terminate`` closed under us raises here and reads as
        unknown.
        """
        from multiprocessing.connection import wait as _wait

        try:
            _wait([self.proc.sentinel])
            return self.proc.exitcode
        except Exception:
            return None

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
        # 'cancelled' closes the token and wakes nobody: ``cancel`` took the
        # waiter off the books before it sent the frame that led here.

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

    def _mark_exited(self, code: int | None) -> None:
        """Record the exit once and wake every waiter. Safe from any thread."""
        with self._state:
            if self._exited.is_set():
                return
            self.exitcode = code
            self._exited.set()
            waiters, self._exit_waiters = self._exit_waiters, []
        for loop, fut in waiters:
            with contextlib.suppress(RuntimeError):  # that loop is closed already
                loop.call_soon_threadsafe(_resolve, fut, code)

    # --- parent-side calls -----------------------------------------------

    def wait_ready(self, timeout: float | None) -> None:
        """Block until the child has built its Context, or blow up trying."""
        if not self._ready.wait(timeout):
            raise TimeoutError(f"worker {self.wid} did not come up in time")
        if self._ready_error is not None:
            raise self._ready_error

    def open(self, loop: asyncio.AbstractEventLoop | None = None) -> tuple[int, _Reply]:
        """Register a waiter for a new request, without sending anything yet."""
        token = next(self._tokens)
        reply = _Reply(loop)
        with self._state:
            if self._closed:
                raise WorkerGone(f"worker {self.wid} is gone")
            self._pending[token] = reply
        return token, reply

    def send(self, kind: str, token: int, reply: _Reply, tree: object, attrs: dict | None) -> None:
        """Send an opened request's frame. A cancel that came in meanwhile follows it out."""
        try:
            with self._send_lock:
                wire.send(self.conn, (kind, token, tree, attrs))
        except (OSError, ValueError, BrokenPipeError) as exc:
            with self._state:
                self._pending.pop(token, None)
            raise WorkerGone(f"worker {self.wid} is gone") from exc
        with self._state:
            reply.sent = True
            cancelled = reply.cancelled
        if cancelled:
            self._send_cancel(token)

    def request(self, kind: str, tree: object, attrs: dict | None) -> tuple[int, _Reply]:
        """Register a waiter, send the frame, hand the token and the slot back."""
        token, reply = self.open()
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
            if self._closed:
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

    def wait_exit(self, timeout: float | None = None) -> int | None:
        """Block until the process is gone; its exit code, or None if unknown."""
        if not self._exited.wait(timeout):
            raise TimeoutError(f"worker {self.wid} did not exit in time")
        return self.exitcode

    async def await_exit(self) -> int | None:
        """Wait for the process to be gone without holding a thread.

        A future on the running loop is registered under the state lock, so
        an exit that lands between the check and the registration is not
        missed: either the flag is already set here, or ``_mark_exited`` sees
        the future and resolves it. Cancelling the await drops the future.
        """
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        entry = (loop, fut)
        with self._state:
            if self._exited.is_set():
                return self.exitcode
            self._exit_waiters.append(entry)
        try:
            return await fut
        finally:
            with self._state, contextlib.suppress(ValueError):
                self._exit_waiters.remove(entry)

    @property
    def running(self) -> bool:
        """Whether any dispatched body on this worker is still executing."""
        with self._state:
            return bool(self._running)

    def terminate(self) -> None:
        """Kill the process for real, then reap it. Never waits on the child."""
        with self._state:
            self._closed = True
            self._terminating = True
        proc = self.proc
        code: int | None = None
        with contextlib.suppress(Exception):
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=self.grace)
                if proc.is_alive():
                    proc.kill()
                    proc.join(timeout=self.grace)
            else:
                proc.join(timeout=self.grace)
            code = proc.exitcode
        # The child's end is closed by now, so the reader sees EOF and exits.
        self._reader.join(timeout=self.grace)
        with contextlib.suppress(Exception):
            self.conn.close()
        with contextlib.suppress(Exception):
            proc.close()
        self._abandon(WorkerGone(f"worker {self.wid} was killed"))
        self._mark_exited(code)


def _resolve(fut: asyncio.Future, value: object) -> None:
    """Set ``fut`` unless its waiter already went away. Runs on ``fut``'s loop."""
    if not fut.done():
        fut.set_result(value)


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
            default, so the child gets a clean interpreter. ``init`` travels
            through ``nu.lang.wire`` (cloudpickle), so closures and locally
            defined classes go along.
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
            args=(child_conn, wire.dumps(bracket)),
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

    def dispatch(self, wid: object, tree: object, attrs: dict | None = None) -> int:
        """Ship ``tree`` to worker ``wid`` and return once the child acked it.

        The body keeps running in the child afterwards. Nothing is ever
        awaited on its result, which is what makes this usable for resident,
        never-terminating trees. Returns the request's token, which
        ``cancel`` takes.
        """
        token, reply = self._handle(wid).request("dispatch", tree, attrs)
        reply.wait(self.ready_timeout)
        return token

    def teleport(self, wid: object, tree: object, attrs: dict | None = None) -> object:
        """Ship ``tree`` to worker ``wid`` and block for its value.

        Interrupted while it waits (a ``KeyboardInterrupt``), the body is
        cancelled in the child too.
        """
        handle = self._handle(wid)
        token, reply = handle.request("exec", tree, attrs)
        try:
            return reply.wait(None)
        except BaseException:
            handle.cancel(token)
            raise

    def cancel(self, wid: object, token: int) -> None:
        """Cancel request ``token`` on worker ``wid``, the task running it in the child.

        The child cancels the task, so the body unwinds through its own
        cleanup. Fire and forget: nothing waits for that to finish. A no-op
        on an unknown id or a token that already finished.
        """
        with self._lock:
            handle = self._workers.get(wid)  # type: ignore[arg-type]
        if handle is not None:
            handle.cancel(token)

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

    def wait(self, wid: object, timeout: float | None = None) -> int | None:
        """Block until worker ``wid`` has exited; its exit code, or None.

        An id that was killed or never launched is already gone as far as the
        pool knows, so it answers None at once, the way ``alive`` answers
        False. A kill landing while this waits wakes it with the real code.
        """
        with self._lock:
            handle = self._workers.get(wid)  # type: ignore[arg-type]
        return None if handle is None else handle.wait_exit(timeout)

    def workers(self) -> list[int]:
        """Every worker id the pool still tracks, in launch order."""
        with self._lock:
            return sorted(self._workers)

    # --- async wrappers --------------------------------------------------

    async def alaunch(self, init: _LifecycleBracket | None = None) -> int:
        """Async ``launch``: spawn + wait for READY off-thread."""
        return await asyncio.to_thread(self.launch, init)

    async def adispatch(self, wid: object, tree: object, attrs: dict | None = None) -> int:
        """Async ``dispatch``: wait for the ack off-thread. Returns the token."""
        return await asyncio.to_thread(self.dispatch, wid, tree, attrs)

    async def ateleport(self, wid: object, tree: object, attrs: dict | None = None) -> object:
        """Async ``teleport``: the reader thread wakes it, no thread is held meanwhile.

        Cancelling the await cancels the body in the child: its task is
        cancelled there and unwinds through its own cleanup. The await does
        not wait for that. A worker that dies meanwhile raises ``WorkerGone``.

        The frame goes out off-thread, since a child that is not reading its
        pipe can block a send. So does the cancel, on a thread of its own,
        for the same reason and because the loop may be closing by then.
        """
        handle = self._handle(wid)
        token, reply = handle.open(asyncio.get_running_loop())
        try:
            await asyncio.to_thread(handle.send, "exec", token, reply, tree, attrs)
            return await reply.await_()
        except asyncio.CancelledError:
            threading.Thread(
                target=handle.cancel, args=(token,), name=f"nu-mp-pool-cancel-{wid}", daemon=True
            ).start()
            raise

    async def await_exit(self, wid: object) -> int | None:
        """Async ``wait``: the reader thread wakes it, no thread is held meanwhile.

        Named apart from the sync one only because ``await`` is a keyword.
        """
        with self._lock:
            handle = self._workers.get(wid)  # type: ignore[arg-type]
        return None if handle is None else await handle.await_exit()

    async def akill(self, wid: object) -> None:
        """Async ``kill``, shielded so a cancellation still reaps the process."""
        await asyncio.shield(asyncio.to_thread(self.kill, wid))
