"""Teleport - distributed execution Span.

Teleport ships its body to a Worker for execution. The body doesn't know it
moved - it executes against the Worker's Context instead of the parent Context.

Transparent: removing Teleport doesn't change what is computed, only where it
runs. As a Span it forwards the body's yield, so it slots in anywhere the body
would (Parallel/Race members, Sequential steps, etc.). It is a Policy, not a
Bracket: a Bracket governs lifecycle (open a region before, tear it down after),
whereas Teleport governs execution - it decides *where* the body runs, the same
family as Retry / Timeout, and never runs the body locally.

Async-only. The body is not run locally - Teleport captures the body *term*
(slot 0) and hands it to the Worker, which recompiles and drains it against its
own Context (``Worker.aexecute`` -> ``acollect``) and returns the last value. A
stream body is collapsed to that single value, yielded once, so cardinality is
preserved (stream in -> one-item stream out).

Usage:
    Teleport(body, worker=0)

    # Carry parent's attrs to worker
    Teleport(body, worker=1, carry=True)

Workers are resolved from the context by tag:
    ctx.get(Worker, 0)      # by index
    ctx.get(Worker, "gpu")  # by capability
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Attr, Cardinality, Policy


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = [
    "Teleport",
]


async def _one(value: object) -> AsyncIterator:
    """Yield a collapsed worker result once (stream body -> one-item stream)."""
    if value is not None:
        yield value


class Teleport(Policy):
    """Ship the body to a Worker for remote execution.

    Args:
        body: Nu to execute on the worker.
        worker: Tag to resolve the target Worker from the context.
        carry: If True, copy the parent's attrs to the worker context before
            execution.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, body: Nu, *, worker: object = 0, carry: bool = False) -> None:
        super().__init__(body)
        self._payload["worker"] = worker
        self._payload["carry"] = carry

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            msg = "Teleport requires the async runtime; use arun / afirst / acollect"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body_term = self._children[0]
        worker_tag = self._payload["worker"]
        carry = self._payload["carry"]

        async def athunk(rt: Runtime) -> object:
            from ..resources.worker import Worker

            worker = rt.ctx.get(Worker, worker_tag)
            if carry and rt.ctx.attrs:
                result = await worker.aexecute(body_term, attrs=dict(rt.ctx.attrs))
            else:
                result = await worker.aexecute(body_term)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one(result)
            return result

        return athunk

    def __repr__(self) -> str:
        carry = ", carry=True" if self._payload.get("carry") else ""
        return f"Teleport(worker={self._payload.get('worker')!r}{carry})"
