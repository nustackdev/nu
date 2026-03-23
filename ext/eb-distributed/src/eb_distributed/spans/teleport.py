"""Teleport - distributed execution span.

Teleport is a Span that ships its children to a Worker for execution.
The tree inside doesn't know it moved - it executes against the
Worker's Context instead of the parent Context.

Transparent: removing Teleport doesn't change what is computed,
only where it runs.

Usage:
    Teleport(
        Data.price.store(42.0),
        Data.quantity.store(10),
        worker=0,
    )

Workers are resolved from context by tag:
    ctx[Worker, 0]      # by index
    ctx[Worker, "gpu"]  # by capability
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
    """Ships children to a Worker for remote execution."""

    def __init__(self, *children: Executable, worker: object = 0) -> None:
        super().__init__(*children)
        self._worker_tag = worker

    async def execute(self, ctx: Context) -> object:
        """Execute children on the target worker."""
        from ..resources.worker import Worker

        worker = ctx[Worker, self._worker_tag]

        if len(self.children) == 1:
            subtree = self.children[0]
        else:
            from everybase.abc import Seq

            subtree = Seq(*self.children)

        return await worker.execute(subtree)

    def __repr__(self) -> str:
        return f"Teleport(worker={self._worker_tag!r})"
