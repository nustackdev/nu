"""Primitive ref ops - flat name-based Context ops.

ScalarQueries over `ctx.attrs`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import EMPTY
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.context import Context

    from .attr_refs import AttrRef

__all__ = [
    "AttrExistsOp",
    "AttrGetOp",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class AttrGetOp(ScalarQuery):
    """Read value by name from context: ctx.attrs[name]. EMPTY if missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: AttrRef) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Context, ops: list[Any]) -> Any:  # noqa: ANN401
        ref: AttrRef = self._children[0]  # type: ignore[assignment]
        key = ref._resolve_name_sync(ctx)
        return ctx.attrs[key] if key in ctx.attrs else EMPTY


class AttrExistsOp(ScalarQuery):
    """Check if name exists in context."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: AttrRef) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Context, ops: list[Any]) -> bool:
        ref: AttrRef = self._children[0]  # type: ignore[assignment]
        key = ref._resolve_name_sync(ctx)
        return key in ctx.attrs
