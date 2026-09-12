"""``_pool_worker_main``: entry point running inside every pool worker process.

The child owns a Nu ``Context`` (built from the ``init`` bracket it was handed
at spawn) and a duplex ``Pipe`` back to the parent. Unlike ``nu.mp``'s worker
it does **not** serialize one request at a time: every request becomes its own
asyncio task, so a resident body dispatched with ``Dispatch`` keeps running
while the loop goes back to reading the pipe.

Wire format is stdlib ``pickle`` - both endpoints are trusted (parent and its
own child). Frames::

    parent -> child
        ('exec', token, tree, attrs)      run it, reply with the value
        ('dispatch', token, tree, attrs)  ack, then run it detached
        ('stop',)                         drain and exit

    child -> parent
        ('ready',)              context built, accepting requests
        ('failed', exc)         context build blew up
        ('ack', token)          a dispatched body was accepted
        ('ok', token, value)    an 'exec' finished
        ('err', token, exc)     an 'exec' or a dispatched body raised
        ('done', token)         a dispatched body finished cleanly

Every frame past ``ready`` carries its token, so the parent can keep several
requests in flight on one worker and match replies to waiters. ``ack`` is
always sent *before* the task is created, so the parent can never observe
``done`` ahead of the ``ack`` that opened the token.
"""

from __future__ import annotations

import asyncio
import contextlib
import pickle
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from multiprocessing.connection import Connection

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Context


__all__ = ["_pool_worker_main"]


def _portable(exc: BaseException) -> BaseException:
    """Return ``exc`` if it survives a pickle round trip, else a flat stand-in."""
    try:
        pickle.loads(pickle.dumps(exc))  # noqa: S301  (our own object, trusted)
    except Exception:
        return RuntimeError(f"{type(exc).__name__}: {exc}")
    return exc


def _pool_worker_main(conn: Connection, init: _LifecycleBracket | None) -> None:
    """Child-process entry: build the Context, ack READY, serve the pipe."""
    try:
        asyncio.run(_run(conn, init))
    finally:
        with contextlib.suppress(Exception):
            conn.close()


async def _run(conn: Connection, init: _LifecycleBracket | None) -> None:
    """Build the Context from ``init``, then serve requests until stop/EOF."""
    from nu.lang.runtime import Context

    send_lock = asyncio.Lock()

    async def send(frame: tuple) -> None:
        async with send_lock:
            await asyncio.to_thread(conn.send, frame)

    stack = contextlib.AsyncExitStack()
    async with stack:
        try:
            if init is not None:
                ctx = await stack.enter_async_context(init._aopen(Context()))
            else:
                ctx = Context()
        except BaseException as exc:
            with contextlib.suppress(Exception):
                conn.send(("failed", _portable(exc)))
            raise

        conn.send(("ready",))

        tasks: set[asyncio.Task] = set()
        try:
            while True:
                try:
                    frame = await asyncio.to_thread(conn.recv)
                except (EOFError, OSError):
                    break
                if frame[0] == "stop":
                    break
                kind, token, tree, attrs = frame
                reply = kind == "exec"
                if not reply:
                    # ack first: the token must open before anything can close it
                    await send(("ack", token))
                tasks.add(_spawn(tasks, _run_one(ctx, tree, attrs, token, send, reply=reply)))
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


def _spawn(tasks: set[asyncio.Task], coro: Coroutine) -> asyncio.Task:
    """Create a task and keep a strong reference until it finishes."""
    task = asyncio.create_task(coro)
    task.add_done_callback(tasks.discard)
    return task


def _exec_context(ctx: Context, attrs: dict | None) -> Context:
    """The Context one request runs against: ``ctx``, or a copy carrying attrs."""
    if not attrs:
        return ctx
    exec_ctx = ctx._copy()
    for key, value in attrs.items():
        exec_ctx.attrs[key] = value
    return exec_ctx


async def _run_one(
    ctx: Context,
    tree: object,
    attrs: dict | None,
    token: int,
    send: Callable,
    *,
    reply: bool,
) -> None:
    """Compile and evaluate one request, then report its outcome upstream."""
    from nu.lang.helpers import compile as compile_term
    from nu.lang.helpers.evaluation import aeval

    try:
        program = compile_term(tree)
        value, _ = await aeval(program, _exec_context(ctx, attrs))
    except asyncio.CancelledError:
        raise
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
