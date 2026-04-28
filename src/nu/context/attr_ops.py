"""Primitive ref ops - flat name-based Context ops.

Queries over `ctx.attrs`. Yield one value each.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import Mode, Query, Sentinel


if TYPE_CHECKING:
    from nu.context import Context

    from .attr_refs import AttrRef

__all__ = [
    "AttrExistsOp",
    "AttrGetOp",
]


class AttrGetOp[T](Query[T | Sentinel]):
    """Read value by name from context: ctx.attrs[name]."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: AttrRef[T]) -> None:
        super().__init__(ref)

    def run(self, ctx: Context) -> T | Sentinel:
        key = self.children[0]._resolve_name_sync(ctx)
        return ctx.attrs[key]


class AttrExistsOp(Query[bool]):
    """Check if name exists in context."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: AttrRef) -> None:
        super().__init__(ref)

    def run(self, ctx: Context) -> bool:
        key = self.children[0]._resolve_name_sync(ctx)
        return key in ctx.attrs
