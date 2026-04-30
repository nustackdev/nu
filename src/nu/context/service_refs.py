"""ServiceRef - resolve a service object directly from Context bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.ref import Ref
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.context import Context
    from nu.forms.primitives import BoolForm


__all__ = [
    "ServiceRef",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ServiceRef[T](Ref[T]):
    """Service ref - resolves an object from Context by type tag.

    Like AttrRef but for service bindings instead of attrs. The service
    type is used as the Context key.

    Usage:
        ref = ServiceRef(SolanaRpc)
        val = ref.eval(ctx)  # -> ctx[SolanaRpc]
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, service_type: type[T] | None = None) -> None:
        super().__init__()
        self._service_type = service_type or self.__class__._default_service_type()

    @classmethod
    def _default_service_type(cls) -> type:
        msg = f"{cls.__name__} must provide service_type or override _default_service_type()"
        raise TypeError(msg)

    @property
    def service_type(self) -> type:
        return self._service_type

    def eval(self, ctx: Context) -> Any:  # noqa: ANN401, D102
        return ctx.get(self._service_type)

    async def aeval(self, ctx: Context) -> Any:  # noqa: ANN401, D102
        return ctx.get(self._service_type)

    def exists(self) -> BoolForm:
        """Check if service exists in context."""
        from nu.forms.primitives import BoolForm

        from .service_ops import ServiceExistsOp

        return BoolForm(ServiceExistsOp(self))
