"""Teleport - distributed execution span.

Teleport is a Span that ships its children to a Worker for execution.
The tree inside doesn't know it moved - it executes against the
Worker's Context instead of the parent Context.

Usage:
    # Execute subtree on worker 0
    Teleport(
        Seq(
            Data.price.store(42.0),
            Data.quantity.store(10),
        ),
        worker=0,
    )

Workers are resolved from context by index:
    ctx[Worker, 0]
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

    On execute: wraps children in a container, sends to the worker,
    worker executes against its own Context. The parent tree just
    awaits the result.

    Transparent: removing Teleport doesn't change what is computed,
    only where it runs.
    """

    def __init__(self, *children: Executable, worker: int = 0) -> None:
        super().__init__(*children)
        self._worker_idx = worker

    async def execute(self, ctx: Context) -> object:
        """Execute children on the target worker.

        Wraps children in a Seq (if multiple) or sends single child
        directly. The worker executes the tree against its own Context.
        """
        from .worker import Worker

        worker = ctx[Worker, self._worker_idx]

        if len(self.children) == 1:
            subtree = self.children[0]
        else:
            from everybase.abc import Seq

            subtree = Seq(*self.children)

        return await worker.execute(subtree)

    def __repr__(self) -> str:
        return f"Teleport(worker={self._worker_idx})"
