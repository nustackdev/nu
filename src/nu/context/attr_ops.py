"""Primitive ref ops — flat name-based Context ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Op, Calculation, Sentinel


if TYPE_CHECKING:
    from nu.context import Context

    from .attr_refs import PrimRef

__all__ = [
    "PrimExistsOp",
    "PrimGetOp",
]


class PrimGetOp[T](Calculation, Op[T | Sentinel]):
    """Read value by name from context: ctx[name]."""

    def __init__(self, ref: PrimRef[T]) -> None:
        """Initialize with ref."""
        super().__init__()
        self._ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the get operation."""
        return ctx.attrs[self._ref.name]


class PrimExistsOp(Calculation, Op[bool]):
    """Check if name exists in context."""

    def __init__(self, ref: PrimRef) -> None:
        """Initialize with ref."""
        super().__init__()
        self._ref = ref

    async def execute(self, ctx: Context) -> bool:
        """Execute the exists check."""
        return self._ref.name in ctx.attrs
