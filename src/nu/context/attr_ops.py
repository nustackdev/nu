"""Primitive ref ops - flat name-based Context ops.

Queries over `ctx.attrs`. Yield one value each.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Query, Sentinel


if TYPE_CHECKING:
    from nu.context import Context

    from .attr_refs import AttrRef

__all__ = [
    "AttrExistsOp",
    "AttrGetOp",
]


class AttrGetOp[T](Query[T | Sentinel]):
    """Read value by name from context: ctx.attrs[name]."""

    def __init__(self, ref: AttrRef[T]) -> None:
        super().__init__(ref)

    async def run(self, ctx: Context) -> T | Sentinel:
        key = await self.children[0]._resolve_name(ctx)
        return ctx.attrs[key]


class AttrExistsOp(Query[bool]):
    """Check if name exists in context."""

    def __init__(self, ref: AttrRef) -> None:
        super().__init__(ref)

    async def run(self, ctx: Context) -> bool:
        key = await self.children[0]._resolve_name(ctx)
        return key in ctx.attrs
