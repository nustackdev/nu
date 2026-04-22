"""ServiceRef -- resolve a service object directly from Context bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Ref, Sentinel


if TYPE_CHECKING:
    from collections.abc import Generator

    from nu.context import Context
    from nu.primitives import BoolI


__all__ = [
    "ServiceRef",
]


class ServiceRef[T](Ref[T]):
    """Service ref -- resolves an object directly from Context by type tag.

    Like AttrRef but for service bindings instead of attrs.
    The service type is used as the Context key.

    Usage:
        ref = ServiceRef(SolanaRpc)
        val = await ref.fetch(ctx)  # -> ctx[SolanaRpc]
    """

    def __init__(self, service_type: type[T] | None = None) -> None:
        """Initialize with service type tag."""
        super().__init__()
        self._service_type = service_type or self.__class__._default_service_type()

    @classmethod
    def _default_service_type(cls) -> type:
        """Subclasses override to provide their service type."""
        msg = f"{cls.__name__} must provide service_type or override _default_service_type()"
        raise TypeError(msg)

    @property
    def service_type(self) -> type:
        """The service type tag for context lookup."""
        return self._service_type

    async def resolve(self, ctx: Context) -> type:
        """Resolve to the service type."""
        return self._service_type

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch service directly from context bindings."""
        return ctx.get(self._service_type)

    def fetch_sync(self, ctx: Context) -> T | Sentinel:
        """Sync counterpart of `fetch`."""
        return ctx.get(self._service_type)

    def open_sync(self, ctx: Context) -> Generator[T | Sentinel, None, None]:
        """Sync counterpart of `open`; yields the fetched value once."""
        yield self.fetch_sync(ctx)

    def exists(self) -> BoolI:
        """Check if service exists in context."""
        from nu.primitives import BoolI

        from .service_ops import ServiceExistsOp

        return BoolI(ServiceExistsOp(self))
