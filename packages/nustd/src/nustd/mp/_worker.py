"""``_worker_main``: entry point that runs inside each ``MpWorker`` child process.

The child owns a Nu ``Context`` (built from ``init`` or ``ctx_builder``) and a
duplex ``Pipe`` back to the parent. It runs a **sync** request loop -
one request at a time, no interleave - because a single process can only
crunch one CPU-bound job anyway. Scale wider by binding a fleet
(``ProvideList`` / ``ProvideDict``).

Internally the worker uses ``asyncio.run`` because the ``init`` bracket
lifecycle is async and Nu's runtime tree may be async; that is invisible
to the parent, which just does blocking ``pipe.send`` / ``pipe.recv``.

Wire format is stdlib ``pickle`` - both endpoints are trusted (parent and
its own child). Frames::

    ('exec', tree, attrs)   parent -> worker
    ('stop',)               parent -> worker (shutdown)
    ('ok', value)           worker -> parent
    ('err', exc)            worker -> parent
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from multiprocessing.connection import Connection

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Context


def _worker_main(
    conn: Connection,
    init: _LifecycleBracket | None,
    ctx_builder: Callable[[], Context | Awaitable[Context]] | None,
) -> None:
    """Child-process entry: build Context, ack READY, run the request loop."""
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
            ctx = await stack.enter_async_context(init._aopen(Context()))
        elif ctx_builder is not None:
            result = ctx_builder()
            if asyncio.iscoroutine(result):
                result = await result
            ctx = result
        else:
            ctx = Context()

        conn.send(("ready",))

        while True:
            try:
                frame = await asyncio.to_thread(conn.recv)
            except (EOFError, OSError):
                break
            if frame[0] == "stop":
                break
            _, tree, attrs = frame
            try:
                exec_ctx = ctx
                if attrs:
                    exec_ctx = ctx._copy()
                    for key, value in attrs.items():
                        exec_ctx.attrs[key] = value
                program = compile_term(tree)
                value, _ = await aeval(program, exec_ctx)
                conn.send(("ok", value))
            except BaseException as exc:
                with contextlib.suppress(Exception):
                    conn.send(("err", exc))
