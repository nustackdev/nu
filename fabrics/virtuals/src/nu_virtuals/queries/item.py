"""virtuals item queries — unsafe primitive reads.

ItemPrimitiveGetUnsafe: Read — _unsafe_primitive_read() (single ctx.get).

Named explicitly Unsafe — optimization internal for tree deformers, not a
user-facing API. Requires virtuals views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import EMPTY, is_sentinel
from nu.terms.types import Mode


__all__ = [
    "ItemPrimitiveGetUnsafe",
]


class ItemPrimitiveGetUnsafe(ScalarQuery):
    """Read primitive value via _unsafe_primitive_read().

    Single ctx[] call — no marker parsing, no type checks.
    Returns EMPTY if the value doesn't exist.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_read()
        resolve_address(ctx) -> key/index
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        value = parent._unsafe_primitive_read(address)
        if is_sentinel(value):
            return EMPTY
        return value

    async def _aapply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        value = parent._unsafe_primitive_read(address)
        if is_sentinel(value):
            return EMPTY
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveGetUnsafe({self.ref!r})"
