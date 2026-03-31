"""ServiceRef -- resolve a service object directly from Context bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import Ref, Sentinel


if TYPE_CHECKING:
    from nu.core import Context

    from ..values import BoolValue


__all__ = [
    "ServiceRef",
]


class ServiceRef[T](Ref[T]):
    """Service ref -- resolves an object directly from Context by type tag.

    Like PrimRef but for service bindings instead of attrs.
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
        return ctx[self._service_type]  # type: ignore[index]

    def exists(self) -> BoolValue:
        """Check if service exists in context."""
        from ..values import BoolValue
        from .service_morphisms import ServiceExistsOp

        return BoolValue(ServiceExistsOp(self))
