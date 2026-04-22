"""Service ref ops - direct Context binding ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Query, Sentinel


if TYPE_CHECKING:
    from nu.context import Context

    from .service_refs import ServiceRef

__all__ = [
    "ServiceExistsOp",
    "ServiceGetOp",
]


class ServiceGetOp[T](Query[T | Sentinel]):
    """Read service from context: ctx[service_type]."""

    def __init__(self, ref: ServiceRef[T]) -> None:
        """Initialize with ref."""
        super().__init__(ref)

    async def arun(self, ctx: Context) -> T | Sentinel:
        """Return service bound in ctx for the ref's service_type."""
        return ctx[self.children[0].service_type]

    def run(self, ctx: Context) -> T | Sentinel:
        """Sync counterpart of `arun`."""
        return ctx[self.children[0].service_type]


class ServiceExistsOp(Query[bool]):
    """Check if service type exists in context."""

    def __init__(self, ref: ServiceRef) -> None:
        """Initialize with ref."""
        super().__init__(ref)

    async def arun(self, ctx: Context) -> bool:
        """Return True if the ref's service_type is bound in ctx."""
        return self.children[0].service_type in ctx

    def run(self, ctx: Context) -> bool:
        """Sync counterpart of `arun`."""
        return self.children[0].service_type in ctx
