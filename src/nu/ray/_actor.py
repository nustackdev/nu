"""``_RayServiceActor``: a ``@ray.remote`` host process for Nu execution.

The actor holds a Nu ``Context`` and executes Nu trees against it. It is the
in-actor half of a ``RayService`` - the ``RayService`` resource on the parent
side spawns one of these actors, tells it to build its context, and later
routes tree execution to it through ``aexecute``.

An in-flight ``aexecute`` is tracked so shutdown can cancel and drain it
before the actor tears down its context. This is the same guard the current
distributed ``WorkerProcess`` uses to avoid a use-after-free when closing
storage under a live query.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import ray


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from nu.lang.runtime import Context


@ray.remote
class _RayServiceActor:
    """Ray actor hosting a Nu ``Context`` + tree executor.

    Parent side (``RayService``) calls the async ``start`` / ``aexecute`` /
    ``shutdown`` methods. The actor itself is stateless before ``start`` and
    torn down after ``shutdown``.
    """

    def __init__(self) -> None:
        self._ctx: Context | None = None
        self._inflight: set[asyncio.Task] = set()

    async def start(self, ctx_builder: Callable[[], Context | Awaitable[Context]] | None) -> None:
        """Build this actor's Context via the caller-supplied builder.

        ``ctx_builder`` is any callable that returns a ``Context`` (or an
        awaitable that resolves to one). Passing ``None`` leaves ``self._ctx``
        empty - the tree runs against a bare ``Context()`` at ``aexecute``.
        """
        if ctx_builder is None:
            from nu.lang.runtime import Context

            self._ctx = Context()
            return
        result = ctx_builder()
        if asyncio.iscoroutine(result):
            result = await result
        self._ctx = result

    async def aexecute(self, tree: object, attrs: dict | None = None) -> object:
        """Compile ``tree`` and evaluate it against this actor's Context.

        Returns the root's value (``None`` for effect-only trees). ``attrs``
        is merged into a shallow-copied Context before execution so the
        parent's ``ctx.attrs`` can carry over without polluting the actor's
        baseline.

        Value-rooted trees (Query / Command / effectful Sequential) work
        directly. A stream-rooted tree returns its async generator, which
        won't cross the ray boundary; wrap it in a reducer or ``last()``
        before ``Teleport``.
        """
        from nu.lang import compile as compile_term
        from nu.lang.helpers.drive import aeval

        ctx = self._ctx
        if attrs:
            ctx = ctx._copy()
            for key, value in attrs.items():
                ctx.attrs[key] = value

        task = asyncio.current_task()
        if task is not None:
            self._inflight.add(task)
        try:
            program = compile_term(tree)
            value, _ = await aeval(program, ctx)
            return value
        finally:
            if task is not None:
                self._inflight.discard(task)

    async def shutdown(self) -> None:
        """Cancel in-flight executes and drop the Context."""
        for t in list(self._inflight):
            t.cancel()
        for t in list(self._inflight):
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await t
        self._inflight.clear()
        self._ctx = None
