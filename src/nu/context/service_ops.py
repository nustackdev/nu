"""Service ref ops - direct Context binding ops."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import Op, Sentinel
from nu.terms.effect import Direction


if TYPE_CHECKING:
    from nu.context import Context

    from .service_refs import ServiceRef

__all__ = [
    "ServiceExistsOp",
    "ServiceGetOp",
]


class ServiceGetOp[T](Op[T | Sentinel]):
    """Read service from context: ctx[service_type]."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: ServiceRef[T]) -> None:
        """Initialize with ref."""
        super().__init__(ref)

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute the get operation."""
        return ctx[self.children[0].service_type]


class ServiceExistsOp(Op[bool]):
    """Check if service type exists in context."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: ServiceRef) -> None:
        """Initialize with ref."""
        super().__init__(ref)

    async def execute(self, ctx: Context) -> bool:
        """Execute the exists check."""
        return self.children[0].service_type in ctx
