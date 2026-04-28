"""PV collection ops — unsafe scan and clear primitives.

ScanPrimitivesUnsafeOp: Scan all primitive children — _unsafe_primitive_scan_values()
ClearPrimitivesUnsafeCmd: Clear all primitive children — _unsafe_primitive_clear()

These require PV views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import EMPTY
from nu.terms.types import Effect, Mode


__all__ = [
    "ClearPrimitivesUnsafeCmd",
    "ScanPrimitivesUnsafeOp",
]


class ScanPrimitivesUnsafeOp(ScalarQuery):
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
        """Scan all primitive children via raw storage scan (sync)."""
        try:
            view = self.ref.fetch(ctx)
        except (KeyError, IndexError):
            return EMPTY
        return view._unsafe_primitive_scan_values()

    async def _aapply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        """Scan all primitive children via raw storage scan."""
        try:
            view = await self.ref.afetch(ctx)
        except (KeyError, IndexError):
            return EMPTY
        return view._unsafe_primitive_scan_values()

    def __repr__(self) -> str:
        return f"ScanPrimitivesUnsafeOp({self.ref!r})"


class ClearPrimitivesUnsafeCmd(ScalarCommand):
    """Clear all primitive children via _unsafe_primitive_clear().

    Scan + ctx.delete() each -- no validation, no descendant cleanup.
    The caller must know all children are primitives.

    The ref must implement:
        fetch(ctx) -> view with _unsafe_primitive_clear() method
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        """Clear all primitive children via scan + delete (sync)."""
        view = self.ref.fetch(ctx)
        view._unsafe_primitive_clear()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Clear all primitive children via scan + delete."""
        view = await self.ref.afetch(ctx)
        view._unsafe_primitive_clear()

    def __repr__(self) -> str:
        return f"ClearPrimitivesUnsafeCmd({self.ref!r})"
