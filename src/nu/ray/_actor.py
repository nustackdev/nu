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
    from nu.spans.bracket import _LifecycleBracket


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
        self._init_stack: contextlib.AsyncExitStack | None = None

    async def start(
        self,
        init: _LifecycleBracket | None,
        ctx_builder: Callable[[], Context | Awaitable[Context]] | None,
    ) -> None:
        """Build this actor's Context.

        Prefers ``init`` (a lifecycle bracket): enters its ``_aopen`` on a
        fresh ``Context()``, saves the resulting Context, and keeps the exit
        stack open so the bracket's resources stay live until ``shutdown``.

        Falls back to ``ctx_builder`` (a legacy callable returning a Context
        or awaitable). If both are ``None``, the actor gets a bare Context.
        """
        from nu.lang.runtime import Context

        if init is not None:
            stack = contextlib.AsyncExitStack()
            await stack.__aenter__()
            try:
                self._ctx = await stack.enter_async_context(init._aopen(Context()))
            except BaseException:
                await stack.__aexit__(None, None, None)
                raise
            self._init_stack = stack
            return
        if ctx_builder is None:
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
        """Cancel in-flight executes, tear down init bracket, drop the Context."""
        for t in list(self._inflight):
            t.cancel()
        for t in list(self._inflight):
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await t
        self._inflight.clear()
        if self._init_stack is not None:
            with contextlib.suppress(Exception):
                await self._init_stack.__aexit__(None, None, None)
            self._init_stack = None
        self._ctx = None
