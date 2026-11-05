"""``_pool_worker_main``: entry point running inside every pool worker process.

The child owns a Nu ``Context`` (built from the ``init`` bracket it was handed
at spawn) and a duplex ``Pipe`` back to the parent. Unlike ``nustd.mp``'s worker
it does **not** serialize one request at a time: every request becomes its own
asyncio task, so a resident body dispatched with ``Dispatch`` keeps running
while the loop goes back to reading the pipe.

Every frame goes through ``nu.lang.wire`` (cloudpickle), and so does the
``init`` bracket handed over at spawn. Frames::

    parent -> child
        ('exec', token, tree, attrs)      run it, reply with the value
        ('dispatch', token, tree, attrs)  ack, then run it detached
        ('cancel', token)                 cancel that request's task
        ('stop', deadline)                cancel every job, tear down, exit 0

    child -> parent
        ('group', pgid)         leads its own group now; sent before init runs
        ('ready', pid, pgid, started_at)  context built, accepting requests
        ('failed', exc)         context build blew up
        ('ack', token)          a dispatched body was accepted
        ('ok', token, value)    an 'exec' finished
        ('err', token, exc)     an 'exec' or a dispatched body raised
        ('done', token)         a dispatched body finished cleanly
        ('cancelled', token)    a request's task ended cancelled
        ('interrupted', token)  a request ended by an interrupt (SIGINT)

Every frame past ``ready`` carries its token, so the parent can keep several
requests in flight on one worker and match replies to waiters. The ``ack``
always goes out *before* anything the job sends: the job's task is created
and put on the books first, so an interrupt arriving as the parent reads the
ack finds it, but the send lock is taken for the ack before the task's first
step runs, so the parent can never observe ``done`` ahead of the ``ack``
that opened the token.

A cancel names a token the parent sent before it, so the task is always
there to cancel, unless it already finished, and then the cancel is dropped.
Cancelling runs the body's own cleanup where it stands; once the task is
over the child says ``cancelled``, which closes the token like ``done``.
Tasks cancelled because the worker is going away say nothing.

``stop`` is the polite rung of the parent's ladder. The frame loop ends,
every job is cancelled and given until ``deadline`` (wall clock) to unwind,
then the init bracket is torn down and the process exits 0. Interpreter
shutdown after that is bounded too: past the deadline the process leaves
with ``os._exit(0)``, so a thread a body left running cannot hold it up.
Whatever overruns is the parent's next rungs: SIGINT, SIGTERM, SIGKILL.

Containment, in the order the child does it, before any user code runs:

- ``setpgid(0, 0)``: the worker leads its own process group, so a terminal
  Ctrl+C reaches the host alone and the parent can signal the worker and
  every subprocess its bodies start with one ``killpg``. The parent spawns
  it with SIGINT and SIGTERM masked, and the child unblocks them only once
  the group is set and its handlers are in.
- every inherited descriptor above stdio is made non-inheritable, so a
  shell child a body starts cannot hold the worker's pipe or its exit
  sentinel open after the worker is gone.
- a title, ``nu:{name}-{id}``, where the OS lets us set one.
- signal handlers. SIGINT ends every job: ``KeyboardInterrupt`` into the
  body running on the main thread right now, which is how a sync body that
  never yields gets interrupted, and a cooperative cancel for the rest. The
  worker goes on serving. SIGTERM, once: into a running body it raises
  ``SystemExit``, so the body's ``finally`` blocks run; anywhere else it
  cancels the serving task, so the loop winds down in order. Both end in
  the init bracket's teardown and exit code 143. A second SIGTERM is
  ignored, so it cannot cut the teardown the first one started; the rung
  after SIGTERM is SIGKILL anyway.
- a parent watch: a daemon thread blocked on the spawn sentinel. When the
  parent is gone, EOF, it sends SIGTERM to the worker's group, waits a
  moment, then SIGKILL. No ``PR_SET_PDEATHSIG``: it would fire on the
  spawning *thread* exiting, and a SIGKILL there orphans the grandchildren.
- the group is reported to the parent (``group``) before the init bracket
  runs, so a crash during init still leaves a group the parent can sweep.

The pipe is read on a daemon thread of its own that feeds the loop through
``call_soon_threadsafe``, so the worker's exit never waits on a blocked
``recv``. Side threads (the reader, the sends) keep SIGINT and SIGTERM
blocked, so a signal is always taken on the main thread.
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import ctypes
import multiprocessing
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from nu.lang import wire


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterator
    from multiprocessing.connection import Connection

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Context


__all__ = ["_GUARD", "_pool_worker_main"]


# Masked from the spawn until the child has its group and its handlers.
_GUARD = frozenset({signal.SIGINT, signal.SIGTERM})
# How long the parent watch gives the group between SIGTERM and SIGKILL.
_PARENT_GRACE = 1.0
# ``PR_SET_NAME``: the 15-byte ``comm`` Linux shows in ``top`` and ``ps -o comm``.
_PR_SET_NAME = 15
# After a stop, how long interpreter shutdown gets at least before ``os._exit``.
_EXIT_FLOOR = 0.25


class _Serving:
    """What the signal handlers need from the loop: where it is and what is busy.

    ``bodies`` holds the tasks that are inside their body right now, which is
    the only place a ``KeyboardInterrupt`` or a ``SystemExit`` may be raised:
    raised anywhere else on the main thread, in the loop's own bookkeeping,
    in the serving task or in a reply being sent, it would escape the loop
    or lose a wakeup. ``jobs`` is every job task by token, for the
    cooperative path; ``main`` is the serving task, for the cooperative
    shutdown. ``terming`` makes SIGTERM one-shot, ``exitcode`` is what the
    process exits with once the loop has wound down.
    """

    __slots__ = (
        "bodies",
        "exitcode",
        "interrupted",
        "jobs",
        "loop",
        "main",
        "stop_deadline",
        "terming",
    )

    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self.main: asyncio.Task | None = None
        self.bodies: set[asyncio.Task] = set()
        self.jobs: dict[int, asyncio.Task] = {}
        self.interrupted: set[int] = set()
        self.terming = False
        self.exitcode: int | None = None
        # Set by the ``stop`` frame: the wall clock time the polite rung ends.
        self.stop_deadline: float | None = None


_serving = _Serving()

# True inside a body, and in every task a body starts (a task copies the
# context it was created in), so a signal handler can tell a sync stretch of
# a body's sub-task holding the loop from the loop's own bookkeeping.
_IN_BODY: contextvars.ContextVar[bool] = contextvars.ContextVar("nu_mp_pool_in_body", default=False)


def _portable(exc: BaseException) -> BaseException:
    """Return ``exc`` if it survives a wire round trip, else a flat stand-in."""
    try:
        wire.loads(wire.dumps(exc))
    except Exception:
        return RuntimeError(f"{type(exc).__name__}: {exc}")
    return exc


# --- containment -----------------------------------------------------------


def _own_group() -> None:
    """Lead our own process group. Before anything else: it is what contains us."""
    with contextlib.suppress(OSError):
        os.setpgid(0, 0)


def _keep_fds() -> None:
    """Every descriptor we inherited stays with us.

    The spawn hands the pipe, the parent sentinel and our exit sentinel over
    as inheritable descriptors. A body that execs without closing them (a
    shell ``cmd &``, a ``subprocess`` with ``close_fds=False``) would pass
    them on, and a grandchild holding them keeps the parent from ever
    reading EOF or the sentinel once we are gone. Plain ``os.fork`` still
    copies them; that is the parent's problem to solve by watching the pid.
    """
    with contextlib.suppress(OSError):
        for entry in Path("/dev/fd").iterdir():
            with contextlib.suppress(OSError, ValueError):
                fd = int(entry.name)
                if fd > 2:
                    os.set_inheritable(fd, False)


def _quiet() -> None:
    """Keep SIGINT and SIGTERM off this thread, so the main thread always takes them."""
    signal.pthread_sigmask(signal.SIG_BLOCK, _GUARD)


def _set_title(title: str) -> None:
    """Name the process ``title`` where the OS lets us.

    ``setproctitle`` when it is importable (an optional C extension, the only
    way on mac, and it rewrites the full ``ps`` command line). On Linux also
    ``prctl(PR_SET_NAME)``, which sets the 15-byte ``comm`` with no
    dependency at all.
    """
    try:
        import setproctitle  # type: ignore[import-not-found]
    except ImportError:
        pass
    else:
        with contextlib.suppress(Exception):
            setproctitle.setproctitle(title)
    if sys.platform.startswith("linux"):
        with contextlib.suppress(Exception):
            libc = ctypes.CDLL(None, use_errno=True)
            libc.prctl(_PR_SET_NAME, title.encode()[:15], 0, 0, 0)


def _install_signals() -> None:
    """SIGINT ends every job and the worker serves on; SIGTERM, once, winds the worker down.

    Installed with ``signal.signal``, not left to asyncio: ``asyncio.run`` on
    3.11+ only takes SIGINT over when the handler is still the default one,
    and its own handler could never reach a sync body holding the loop.

    Both raise only into a body that is running on the main thread right
    now, where the exception is the body's to unwind: the request's own
    task, or a task the body started (``_IN_BODY`` is set in both). Anywhere
    else (the loop's bookkeeping, ``select``, the serving task, a reply
    being sent) an exception could lose a wakeup or escape the loop, so the
    work is scheduled on the loop instead.

    SIGINT in a body's sub-task cannot be a ``KeyboardInterrupt``: no
    ``_run_one`` frame is there to catch it, and asyncio re-raises it out of
    the loop. It cancels every job right there instead, before any other
    sub-task gets a step, and raises ``CancelledError`` into the one holding
    the loop; the requests end as interrupted.
    """

    def on_int(signum: int, frame: object) -> None:
        loop = _serving.loop
        if loop is None:
            return
        current = asyncio.current_task(loop)
        busy = current in _serving.bodies
        if not busy and current is not None and _IN_BODY.get():
            _interrupt_all(None)
            raise asyncio.CancelledError
        with contextlib.suppress(RuntimeError):  # the loop is closed already
            loop.call_soon_threadsafe(_interrupt_all, current if busy else None)
        if busy:
            raise KeyboardInterrupt

    def on_term(signum: int, frame: object) -> None:
        if _serving.terming:
            return  # one-shot: a repeat must not cut the teardown the first one started
        _serving.terming = True
        code = 128 + signum
        loop = _serving.loop
        if loop is None:
            raise SystemExit(code)  # no loop to wind down, before or after it
        _serving.exitcode = code
        current = asyncio.current_task(loop)
        if current in _serving.bodies or (current is not None and _IN_BODY.get()):
            raise SystemExit(code)
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(_shutdown)

    signal.signal(signal.SIGINT, on_int)
    signal.signal(signal.SIGTERM, on_term)


def _interrupt_all(busy: asyncio.Task | None) -> None:
    """The cooperative half of an interrupt: cancel every job but ``busy``. Runs on the loop.

    ``busy`` is the body that got ``KeyboardInterrupt`` instead; it answers
    for itself, so it is not cancelled on top of that.
    """
    for token, task in list(_serving.jobs.items()):
        if task is not busy and task.cancel():
            _serving.interrupted.add(token)


def _shutdown() -> None:
    """The cooperative half of SIGTERM: cancel the serving task. Runs on the loop.

    Cancelling it ends the frame loop or the init in progress, cancels the
    jobs, and exits the init stack, so the teardown runs in order; the exit
    code waits in ``_serving.exitcode`` for the process to leave the loop.
    """
    main = _serving.main
    if main is not None and not main.done():
        main.cancel()


def _end_group(sig: int) -> None:
    """Send ``sig`` to our own group when we lead it, else to ourselves alone."""
    with contextlib.suppress(OSError):
        if os.getpgrp() == os.getpid():
            os.killpg(os.getpgrp(), sig)
        else:
            os.kill(os.getpid(), sig)


def _watch_parent() -> None:
    """A daemon thread that ends our group once the parent is gone.

    Blocks on the spawn sentinel, which reads EOF when the parent process
    exits however it exits, SIGKILL included. Works while the loop is held
    by a sync body, since the GIL is released around the wait and inside
    any Python loop. SIGTERM first, so the worker's own teardown runs, then
    SIGKILL for whatever is still there.
    """
    parent = multiprocessing.parent_process()
    if parent is None:
        return

    def watch() -> None:
        parent.join()
        _end_group(signal.SIGTERM)
        time.sleep(_PARENT_GRACE)
        _end_group(signal.SIGKILL)

    threading.Thread(target=watch, name="nu-parent-watch", daemon=True).start()


# --- serving ---------------------------------------------------------------


def _pool_worker_main(conn: Connection, init: bytes, title: str = "nu") -> None:
    """Child-process entry: contain, then build the Context, ack READY, serve the pipe.

    ``init`` is the wire payload of the bracket the worker comes up holding.
    The parent spawned us with SIGINT and SIGTERM masked; they are unblocked
    only once the group is set and the handlers are in place. The group is
    reported before the bracket runs, so even a crash in there leaves the
    parent a group to sweep.

    A SIGTERM taken outside a body winds the loop down cooperatively and
    leaves its exit code behind; it is raised once the loop is gone, so the
    process still exits 143.
    """
    _own_group()
    _keep_fds()
    _set_title(title)
    _install_signals()
    _watch_parent()
    with contextlib.suppress(Exception):
        wire.send(conn, ("group", os.getpgrp()))
    signal.pthread_sigmask(signal.SIG_UNBLOCK, _GUARD)
    try:
        try:
            asyncio.run(_run(conn, wire.loads(init)))
        except asyncio.CancelledError:
            if _serving.exitcode is None:
                raise
        if _serving.exitcode is not None:
            raise SystemExit(_serving.exitcode)
        if _serving.stop_deadline is not None:
            _exit_by(_serving.stop_deadline)
    finally:
        with contextlib.suppress(Exception):
            conn.close()


def _exit_by(deadline: float) -> None:
    """Bound what is left of the exit after a stop: ``os._exit(0)`` past ``deadline``.

    The loop is gone and the teardown ran, so all that remains is the
    interpreter's own shutdown, which joins every non-daemon thread a body
    started. A daemon timer ends the process if that is still going at the
    deadline (and never sooner than a short floor), so a stop that got this
    far exits 0 rather than waiting for the parent's next rung.
    """

    def bound() -> None:
        time.sleep(max(deadline - time.time(), _EXIT_FLOOR))
        for stream in (sys.stdout, sys.stderr):
            with contextlib.suppress(Exception):
                stream.flush()
        os._exit(0)

    threading.Thread(target=bound, name="nu-exit-bound", daemon=True).start()


def _send_quiet(conn: Connection, frame: tuple) -> None:
    """``wire.send`` on a side thread, with the signals kept off that thread."""
    _quiet()
    wire.send(conn, frame)


def _pump(conn: Connection, loop: asyncio.AbstractEventLoop, inbox: asyncio.Queue) -> None:
    """The reader thread: every frame onto the loop's inbox, ``None`` at EOF.

    A daemon thread, so an exit never waits on a ``recv`` the parent is not
    going to end. A loop that closed meanwhile has nobody to deliver to.
    """
    _quiet()
    while True:
        try:
            frame = wire.recv(conn)
        except (EOFError, OSError, ValueError):
            frame = None
        try:
            loop.call_soon_threadsafe(inbox.put_nowait, frame)
        except RuntimeError:
            return
        if frame is None:
            return


async def _run(conn: Connection, init: _LifecycleBracket | None) -> None:
    """Build the Context from ``init``, then serve requests until stop/EOF."""
    from nu.lang.runtime import Context

    loop = asyncio.get_running_loop()
    send_lock = asyncio.Lock()

    async def send(frame: tuple) -> None:
        async with send_lock:
            await asyncio.to_thread(_send_quiet, conn, frame)

    _serving.loop = loop
    _serving.main = asyncio.current_task()
    stack = contextlib.AsyncExitStack()
    try:
        async with stack:
            ctx = Context()
            try:
                if init is not None:
                    await stack.enter_async_context(init._aopen(ctx))
            except (SystemExit, KeyboardInterrupt, asyncio.CancelledError):
                raise  # going down; the parent reads the EOF as gone
            except BaseException as exc:
                with contextlib.suppress(Exception):
                    wire.send(conn, ("failed", _portable(exc)))
                raise

            wire.send(conn, ("ready", os.getpid(), os.getpgrp(), time.time()))
            await _serve(ctx, conn, loop, send)
    finally:
        _serving.loop = None
        _serving.main = None


async def _serve(
    ctx: Context, conn: Connection, loop: asyncio.AbstractEventLoop, send: Callable
) -> None:
    """Read frames off the inbox and run them, until stop or EOF.

    On ``stop`` the jobs are cancelled and waited for until the frame's
    deadline, no longer; whatever is still unwinding then is left to the
    teardown and the parent's next rungs. At EOF (the parent is gone) they
    are waited for in full, and the parent watch bounds that.
    """
    inbox: asyncio.Queue = asyncio.Queue()
    threading.Thread(target=_pump, args=(conn, loop, inbox), name="nu-recv", daemon=True).start()

    tasks: set[asyncio.Task] = set()
    jobs = _serving.jobs
    closing = False

    def over(token: int, task: asyncio.Task) -> None:
        jobs.pop(token, None)
        _serving.bodies.discard(task)
        interrupted = token in _serving.interrupted
        _serving.interrupted.discard(token)
        if not task.cancelled():
            # Ended by itself, so ``_run_one`` already replied; one ending
            # per job. A SystemExit here is the exit itself, not a loss.
            task.exception()
            return
        if closing:
            return
        _spawn(tasks, _say(send, ("interrupted" if interrupted else "cancelled", token)))

    try:
        while True:
            frame = await inbox.get()
            if frame is None:
                break
            if frame[0] == "stop":
                _serving.stop_deadline = frame[1] if len(frame) > 1 else time.time()
                break
            if frame[0] == "cancel":
                task = jobs.get(frame[1])
                if task is not None:
                    task.cancel()
                continue
            kind, token, tree, attrs = frame
            reply = kind == "exec"
            task = _spawn(tasks, _run_one(ctx, tree, attrs, token, send, reply=reply))
            jobs[token] = task
            task.add_done_callback(lambda t, token=token: over(token, t))
            if not reply:
                # The ack goes out first: the send lock is taken here, before
                # the task's first step can run, so nothing the job sends can
                # pass it. The job is on the books before the ack, so an
                # interrupt landing the moment the parent has the ack finds it.
                await send(("ack", token))
    finally:
        closing = True
        for task in tasks:
            task.cancel()
        if tasks:
            deadline = _serving.stop_deadline
            if deadline is None:
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                await asyncio.wait(set(tasks), timeout=max(deadline - time.time(), 0.0))


def _spawn(tasks: set[asyncio.Task], coro: Coroutine) -> asyncio.Task:
    """Create a task and keep a strong reference until it finishes."""
    task = asyncio.create_task(coro)
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return task


async def _say(send: Callable, frame: tuple) -> None:
    """Send a frame nobody waits on; a parent already gone is not an error."""
    with contextlib.suppress(Exception):
        await send(frame)


@contextlib.contextmanager
def _exec_context(ctx: Context, attrs: dict | None) -> Iterator[Context]:
    """The Context one request runs against: a branch of ``ctx`` with the caller's names bound."""
    run_ctx = ctx.branch()
    with contextlib.ExitStack() as scope:
        for name, value in (attrs or {}).items():
            scope.enter_context(run_ctx.attrs.let(name, value))
        yield run_ctx


async def _run_one(
    ctx: Context,
    tree: object,
    attrs: dict | None,
    token: int,
    send: Callable,
    *,
    reply: bool,
) -> None:
    """Compile and evaluate one request, then report its outcome upstream.

    The task is in ``bodies`` exactly while the body runs, which is where a
    SIGINT may raise ``KeyboardInterrupt``; that ends the job as interrupted
    and the worker goes on. ``SystemExit`` (SIGTERM) is let through: the
    worker is going down and the loop's shutdown runs the teardown.
    """
    from nu.lang.helpers import compile as compile_term
    from nu.lang.helpers.evaluation import aeval

    task = asyncio.current_task()
    try:
        program = compile_term(tree)
        with _exec_context(ctx, attrs) as exec_ctx:
            _serving.bodies.add(task)  # type: ignore[arg-type]
            marked = _IN_BODY.set(True)
            try:
                value, _ = await aeval(program, exec_ctx)
            finally:
                _IN_BODY.reset(marked)
                _serving.bodies.discard(task)  # type: ignore[arg-type]
    except (asyncio.CancelledError, SystemExit):
        raise
    except KeyboardInterrupt:
        with contextlib.suppress(Exception):
            await send(("interrupted", token))
        return
    except BaseException as exc:
        with contextlib.suppress(Exception):
            await send(("err", token, _portable(exc)))
        return

    if not reply:
        with contextlib.suppress(Exception):
            await send(("done", token))
        return
    try:
        await send(("ok", token, value))
    except Exception as exc:
        with contextlib.suppress(Exception):
            await send(("err", token, RuntimeError(f"result is not sendable: {exc}")))
