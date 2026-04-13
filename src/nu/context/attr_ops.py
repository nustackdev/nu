"""Primitive ref ops - flat name-based Context ops."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import Op, Sentinel
from nu.terms.effect import Direction


if TYPE_CHECKING:
    from nu.context import Context

    from .attr_refs import AttrRef

__all__ = [
    "AttrExistsOp",
    "AttrGetOp",
]


class AttrGetOp[T](Op[T | Sentinel]):
    """Read value by name from context: ctx.attrs[name]."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: AttrRef[T]) -> None:
        """Initialize with ref."""
        super().__init__(ref)

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the get operation."""
        key = await self.children[0]._resolve_name(ctx)
        return ctx.attrs[key]


class AttrExistsOp(Op[bool]):
    """Check if name exists in context."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: AttrRef) -> None:
        """Initialize with ref."""
        super().__init__(ref)

    async def execute(self, ctx: Context) -> bool:
        """Execute the exists check."""
        key = await self.children[0]._resolve_name(ctx)
        return key in ctx.attrs
