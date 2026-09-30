"""``_worker_main``: entry point that runs inside each ``MpWorker`` child process.

The child owns a Nu ``Context`` (built from ``init`` or ``ctx_builder``) and a
duplex ``Pipe`` back to the parent. It runs a **sync** request loop -
one request at a time, no interleave - because a single process can only
crunch one CPU-bound job anyway. Scale wider by binding a fleet
(``ProvideList`` / ``ProvideDict``).

Internally the worker uses ``asyncio.run`` because the ``init`` bracket
lifecycle is async and Nu's runtime tree may be async; that is invisible
to the parent, which just does blocking sends and receives on the pipe.

Every frame goes through ``nu.lang.wire`` (cloudpickle), and so do
``init`` and ``ctx_builder``, handed over as one ``setup`` payload. Frames::

    ('exec', tree, attrs)   parent -> worker
    ('stop',)               parent -> worker (shutdown)
    ('ok', value)           worker -> parent
    ('err', exc)            worker -> parent
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

from nu.lang import wire


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterator
    from multiprocessing.connection import Connection

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Context


def _worker_main(conn: Connection, setup: bytes) -> None:
    """Child-process entry: build Context, ack READY, run the request loop.

    ``setup`` is the wire payload of ``(init, ctx_builder)``.
    """
    init, ctx_builder = wire.loads(setup)
    try:
        asyncio.run(_run(conn, init, ctx_builder))
    finally:
        with contextlib.suppress(Exception):
            conn.close()


async def _run(
    conn: Connection,
    init: _LifecycleBracket | None,
    ctx_builder: Callable[[], Context | Awaitable[Context]] | None,
) -> None:
    from nu.lang.helpers import compile as compile_term
    from nu.lang.helpers.evaluation import aeval
    from nu.lang.runtime import Context

    stack = contextlib.AsyncExitStack()
    async with stack:
        if init is not None:
            ctx = Context()
            await stack.enter_async_context(init._aopen(ctx))
        elif ctx_builder is not None:
            result = ctx_builder()
            if asyncio.iscoroutine(result):
                result = await result
            ctx = result
        else:
            ctx = Context()

        wire.send(conn, ("ready",))

        while True:
            try:
                frame = await asyncio.to_thread(wire.recv, conn)
            except (EOFError, OSError):
                break
            if frame[0] == "stop":
                break
            _, tree, attrs = frame
            try:
                program = compile_term(tree)
                with _exec_context(ctx, attrs) as exec_ctx:
                    value, _ = await aeval(program, exec_ctx)
                wire.send(conn, ("ok", value))
            except BaseException as exc:
                with contextlib.suppress(Exception):
                    wire.send(conn, ("err", exc))


@contextlib.contextmanager
def _exec_context(ctx: Context, attrs: dict | None) -> Iterator[Context]:
    """The Context one request runs against: a branch of ``ctx`` with the caller's names bound."""
    run_ctx = ctx.branch()
    with contextlib.ExitStack() as scope:
        for name, value in (attrs or {}).items():
            scope.enter_context(run_ctx.attrs.let(name, value))
        yield run_ctx
