"""PV collection queries — unsafe scan primitives.

ScanPrimitivesUnsafe: Scan all primitive children — _unsafe_primitive_scan_values().

Requires PV views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import EMPTY
from nu.terms.types import Mode


__all__ = [
    "ScanPrimitivesUnsafe",
]


class ScanPrimitivesUnsafe(ScalarQuery):
    """Scan all direct primitive child values via _unsafe_primitive_scan_values().

    Single ctx.scan() call -- no marker parsing, no type checks.
    Returns lazy iterator of raw values.

    The ref must implement:
        fetch(ctx) -> view with _unsafe_primitive_scan_values() method
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        try:
            view = self.ref.fetch(ctx)
        except (KeyError, IndexError):
            return EMPTY
        return view._unsafe_primitive_scan_values()

    async def _aapply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        try:
            view = await self.ref.afetch(ctx)
        except (KeyError, IndexError):
            return EMPTY
        return view._unsafe_primitive_scan_values()

    def __repr__(self) -> str:
        return f"ScanPrimitivesUnsafe({self.ref!r})"
