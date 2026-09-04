"""``MpWorker``: a Nu execution service backed by a ``multiprocessing`` process.

Parent-side resource. On ``setup`` it spawns a child running ``_worker_main``,
hands it an ``init`` bracket (or ``ctx_builder``) that builds the worker's
Context, and waits for a READY frame. ``execute`` (sync) / ``aexecute``
(async wrapper) send the tree over a pipe and wait for the reply. ``cleanup``
sends the stop sentinel and joins the child.

The worker processes one request at a time - concurrent parent calls on the
same worker serialize on a lock. Parallelism comes from binding a fleet
(``ProvideList`` / ``ProvideDict``), one request per worker in flight.

Sync and async lifecycle both supported so either Nu runtime can drive it.
"""

from __future__ import annotations

import asyncio
import contextlib
import multiprocessing as _mp
import threading
from typing import TYPE_CHECKING

from ._worker import _worker_main


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from multiprocessing.connection import Connection
    from multiprocessing.context import BaseContext, Process

    from nu.lang.runtime import Context
    from nu.spans.bracket import _LifecycleBracket


__all__ = ["MpWorker"]


class MpWorker:
    """One long-lived child process hosting a Nu Context + tree executor.

    ``init`` is a ``_LifecycleBracket`` (typically ``With(Provide(...), ...)``)
    shipped to the child. The child enters its ``_aopen(Context())`` on start
    and keeps the resulting Context live until shutdown; the bracket's
    resources tear down LIFO on ``cleanup``.

    ``ctx_builder`` is the alternative: a callable returning a Context (or
    awaitable). Pass exactly one of ``init`` or ``ctx_builder``, or neither
    for a bare Context.

    ``start_method`` is the ``multiprocessing`` start method (``"spawn"``,
    ``"fork"``, ``"forkserver"``). Default ``"spawn"`` - cross-platform, the
    child gets a clean interpreter, so ``init`` / ``ctx_builder`` (and their
    captured state) must be pickleable.

    ``name`` is forwarded to ``Process`` for readable ``ps`` output.
    """

    def __init__(
        self,
        ctx_builder: Callable[[], Context | Awaitable[Context]] | None = None,
        *,
        init: _LifecycleBracket | None = None,
        name: str | None = None,
        start_method: str = "spawn",
    ) -> None:
        if init is not None and ctx_builder is not None:
            raise TypeError("MpWorker accepts either init= or ctx_builder=, not both")
        self.ctx_builder = ctx_builder
        self.init = init
        self.name = name
        self.start_method = start_method
        self._proc: Process | None = None
        self._conn: Connection | None = None
        self._lock = threading.Lock()

    def _spawn(self) -> tuple[Process, Connection]:
        ctx: BaseContext = _mp.get_context(self.start_method)
        parent_conn, child_conn = ctx.Pipe(duplex=True)
        proc = ctx.Process(
            target=_worker_main,
            args=(child_conn, self.init, self.ctx_builder),
            name=self.name or "nu-mp-worker",
            daemon=True,
        )
        proc.start()
        child_conn.close()  # parent side keeps its end only
        return proc, parent_conn

    def setup(self, ctx: Context) -> None:
        """Spawn the child, block on its READY frame."""
        proc, conn = self._spawn()
        self._proc = proc
        self._conn = conn
        ack = conn.recv()
        if ack != ("ready",):
            proc.terminate()
            proc.join(timeout=2)
            raise RuntimeError(f"MpWorker did not start cleanly: {ack!r}")

    def cleanup(self) -> None:
        """Send stop, join the child."""
        if self._conn is not None:
            with contextlib.suppress(Exception):
                self._conn.send(("stop",))
        if self._proc is not None:
            self._proc.join(timeout=5)
            if self._proc.is_alive():
                with contextlib.suppress(Exception):
                    self._proc.terminate()
                self._proc.join(timeout=2)
        if self._conn is not None:
            with contextlib.suppress(Exception):
                self._conn.close()
        self._proc = None
        self._conn = None

    def execute(self, tree: object, attrs: dict | None = None) -> object:
        """Ship ``tree`` over the pipe; block on the reply."""
        if self._conn is None:
            raise RuntimeError("MpWorker is not started")
        conn = self._conn
        with self._lock:
            conn.send(("exec", tree, attrs))
            reply = conn.recv()
        kind = reply[0]
        if kind == "ok":
            return reply[1]
        if kind == "err":
            raise reply[1]
        raise RuntimeError(f"Unexpected reply from worker: {reply!r}")

    async def asetup(self, ctx: Context) -> None:
        """Async lifecycle: spawn + await READY off-thread."""
        await asyncio.to_thread(self.setup, ctx)

    async def aexecute(self, tree: object, attrs: dict | None = None) -> object:
        """Async lifecycle: run the blocking ``execute`` off-thread."""
        return await asyncio.to_thread(self.execute, tree, attrs)

    async def acleanup(self) -> None:
        """Async lifecycle: run the blocking ``cleanup`` off-thread."""
        await asyncio.to_thread(self.cleanup)
