"""Teleport - distributed execution span.

Teleport is a Span that ships its children to a Worker for execution.
The tree inside doesn't know it moved - it executes against the
Worker's Context instead of the parent Context.

The target can be a real Worker (in-process) or a WorkerHandle
(Ray actor dispatch). Teleport doesn't care - duck typing.

Usage:
    # Execute subtree on worker 0
    Teleport(
        Data.price.store(42.0),
        Data.quantity.store(10),
        worker=0,
    )

    # Multiple children are wrapped in Seq automatically
    Teleport(
        step_a,
        step_b,
        step_c,
        worker=1,
    )

Workers are resolved from context by tag:
    ctx[Worker, 0]      # by index
    ctx[Worker, "gpu"]  # by capability (future)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Span


if TYPE_CHECKING:
    from everybase import Context, Executable


__all__ = [
    "Teleport",
]


class Teleport(Span):
    """Ships children to a Worker for remote execution.

    On execute: resolves the target worker from context, wraps children
    in a Seq (if multiple), and dispatches to the worker. The worker
    executes the subtree against its own Context.

    Transparent: removing Teleport doesn't change what is computed,
    only where it runs. The subtree is identical either way.
    """

    def __init__(self, *children: Executable, worker: object = 0) -> None:
        """Create a Teleport span.

        Args:
            *children: Tree nodes to execute on the target worker.
            worker: Worker tag for context resolution. Typically an int index.
        """
        super().__init__(*children)
        self._worker_tag = worker

    async def execute(self, ctx: Context) -> object:
        """Execute children on the target worker.

        Resolves the worker from context, builds the subtree,
        and dispatches execution. Works with both in-process Workers
        and remote WorkerHandles (Ray actors).

        Args:
            ctx: Parent context (used only for worker resolution).

        Returns:
            Result of subtree execution on the worker.
        """
        from .worker import Worker

        worker = ctx[Worker, self._worker_tag]

        if len(self.children) == 1:
            subtree = self.children[0]
        else:
            from everybase.abc import Seq

            subtree = Seq(*self.children)

        return await worker.execute(subtree)

    def __repr__(self) -> str:
        return f"Teleport(worker={self._worker_tag!r})"
