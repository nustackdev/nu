"""Service ref morphisms -- direct Context binding ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.core import Morphism, Operation, Sentinel


if TYPE_CHECKING:
    from everybase.core import Context

    from .service import ServiceRef

__all__ = [
    "ServiceExistsOp",
    "ServiceGetOp",
]


class ServiceGetOp[T](Operation, Morphism[T | Sentinel]):
    """Read service from context: ctx[service_type]."""

    def __init__(self, ref: ServiceRef[T]) -> None:
        """Initialize with ref."""
        super().__init__()
        self._ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the get operation."""
        return ctx[self._ref.service_type]


class ServiceExistsOp(Operation, Morphism[bool]):
    """Check if service type exists in context."""

    def __init__(self, ref: ServiceRef) -> None:
        """Initialize with ref."""
        super().__init__()
        self._ref = ref

    async def execute(self, ctx: Context) -> bool:
        """Execute the exists check."""
        return self._ref.service_type in ctx
