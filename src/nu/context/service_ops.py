"""Service ref ops - direct Context binding ops."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.context import Context

    from .service_refs import ServiceRef

__all__ = [
    "ServiceExistsOp",
    "ServiceGetOp",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ServiceGetOp(ScalarQuery):
    """Read service from context: ctx[service_type]."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: ServiceRef) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Context, ops: list[Any]) -> Any:  # noqa: ANN401
        ref: ServiceRef = self._children[0]  # type: ignore[assignment]
        return ctx[ref.service_type]


class ServiceExistsOp(ScalarQuery):
    """Check if service type exists in context."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: ServiceRef) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Context, ops: list[Any]) -> bool:
        ref: ServiceRef = self._children[0]  # type: ignore[assignment]
        return ref.service_type in ctx
