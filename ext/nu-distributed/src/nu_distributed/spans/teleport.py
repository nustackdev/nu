"""Teleport - distributed execution Span.

Teleport ships its body to a Worker for execution. The body doesn't
know it moved - it executes against the Worker's Context instead of the
parent Context.

Transparent: removing Teleport doesn't change what is computed, only
where it runs. As a Span, Teleport's yield-shape forwards from the body,
so it slots in anywhere the body would (Parallel/Race members, Sequential
steps, etc.).

Usage:
    Teleport(body, worker=0)

    # Carry parent's attrs to worker
    Teleport(body, worker=1, carry=True)

Workers are resolved from context by tag:
    ctx[Worker, 0]      # by index
    ctx[Worker, "gpu"]  # by capability
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.span import Span
from nu.terms.types import Mode


__all__ = [
    "Teleport",
]


class Teleport(Span):
    """Ship body to a Worker for remote execution.

    Args:
        body: Nu to execute on the worker.
        worker: Tag to resolve the target Worker from context.
        carry: If True, copy parent's attrs to the worker context
            before execution.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, body: Any, *, worker: object = 0, carry: bool = False) -> None:  # noqa: ANN401
        super().__init__(body)
        self._worker_tag = worker
        self._carry = carry

    def _dispatch_sync(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        msg = f"{type(self).__name__} is async-only"
        raise NotImplementedError(msg)

    async def _dispatch_async(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        from ..resources.worker import Worker

        worker = ctx.get(Worker, self._worker_tag)
        body = self._body()
        if self._carry and ctx.attrs:
            return await worker.aexecute(body, attrs=dict(ctx.attrs))
        return await worker.aexecute(body)

    def _open_sync(self, ctx: Any) -> Any:  # noqa: ANN401
        msg = f"{type(self).__name__} is async-only"
        raise NotImplementedError(msg)

    async def _open_async(self, ctx: Any) -> Any:  # noqa: ANN401
        # Streaming is collapsed: the worker drains and returns the last value.
        result = await self._dispatch_async(ctx, "aexecute")
        if result is not None:
            yield result

    def __repr__(self) -> str:
        carry = ", carry=True" if self._carry else ""
        return f"Teleport(worker={self._worker_tag!r}{carry})"
