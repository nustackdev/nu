"""Teleport - distributed execution op.

Teleport ships its children to a Worker for execution.
The subtree doesn't know it moved - it executes against the
Worker's Context instead of the parent Context.

Transparent: removing Teleport doesn't change what is computed,
only where it runs.

Usage:
    Teleport(
        Data.price.store(42.0),
        Data.quantity.store(10),
        worker=0,
    )

    # Carry parent's attrs to worker
    Teleport(
        handle_error,
        worker=1,
        carry=True,
    )

Workers are resolved from context by tag:
    ctx[Worker, 0]      # by index
    ctx[Worker, "gpu"]  # by capability
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Query


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = [
    "Teleport",
]


class Teleport(Query[object]):
    """Ships children to a Worker for remote execution.

    Args:
        *children: Nus to execute on the worker.
        worker: Tag to resolve the target Worker from context.
        carry: If True, copy parent's attrs to the worker context
            before execution. Attrs are primitive key-value data
            (error strings, loop counters, config) that PrimRefs read.
    """

    def __init__(
        self,
        *children: Nu,
        worker: object = 0,
        carry: bool = False,
    ) -> None:
        super().__init__(*children)
        self._worker_tag = worker
        self._carry = carry

    async def arun(self, ctx: Context) -> object:
        """Execute children on the target worker."""
        from nu import Nu

        from ..resources.worker import Worker

        worker = ctx.get(Worker, self._worker_tag)

        if len(self.children) == 1:
            subtree = self.children[0]
        else:
            # Sequential composition of multiple children.
            subtree = Nu(*self.children)

        if self._carry:
            return await self._execute_with_carry(ctx, worker, subtree)
        return await worker.aexecute(subtree)

    async def _execute_with_carry(
        self,
        parent_ctx: Context,
        worker: object,
        subtree: object,
    ) -> object:
        """Execute with parent attrs copied to worker context."""
        worker_ctx = worker.ctx._copy()
        # Deep copy parent attrs into worker context
        carried = parent_ctx.attrs.copy()
        for key, value in carried.items():
            worker_ctx.attrs[key] = value
        values = await subtree.acollect(worker_ctx)
        return values[-1] if values else None

    def __repr__(self) -> str:
        carry = ", carry=True" if self._carry else ""
        return f"Teleport(worker={self._worker_tag!r}{carry})"
