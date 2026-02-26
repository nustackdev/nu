"""Primitive ref morphisms — flat name-based Context ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.core import Morphism, Operation, Sentinel


if TYPE_CHECKING:
    from everybase.core import Context

    from .base import PrimRef

__all__ = [
    "PrimExistsOp",
    "PrimGetOp",
]


class PrimGetOp[T](Operation, Morphism[T | Sentinel]):
    """Read value by name from context: ctx[name]."""

    def __init__(self, ref: PrimRef[T]) -> None:
        """Initialize with ref."""
        super().__init__()
        self._ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the get operation."""
        return ctx[self._ref.name]


class PrimExistsOp(Operation, Morphism[bool]):
    """Check if name exists in context."""

    def __init__(self, ref: PrimRef) -> None:
        """Initialize with ref."""
        super().__init__()
        self._ref = ref

    async def execute(self, ctx: Context) -> bool:
        """Execute the exists check."""
        return self._ref.name in ctx
