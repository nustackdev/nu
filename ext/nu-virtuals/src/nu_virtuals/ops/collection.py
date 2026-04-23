"""PV collection ops — unsafe scan and clear primitives.

ScanPrimitivesUnsafeOp: Scan all primitive children — _unsafe_primitive_scan_values()
ClearPrimitivesUnsafeCmd: Clear all primitive children — _unsafe_primitive_clear()

These require PV views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar

from nu import EMPTY, Sentinel
from nu.terms import Command, Mode, Query


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "ClearPrimitivesUnsafeCmd",
    "ScanPrimitivesUnsafeOp",
]


class ScanPrimitivesUnsafeOp[T](Query[Iterator[T] | Sentinel]):
    """Scan all direct primitive child values via _unsafe_primitive_scan_values().

    Single ctx.scan() call -- no marker parsing, no type checks.
    Returns lazy iterator of raw values.

    The ref must implement:
        fetch(ctx) -> view with _unsafe_primitive_scan_values() method
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def arun(self, ctx: Context) -> Iterator[T] | Sentinel:
        """Scan all primitive children via raw storage scan."""
        try:
            view = await self.ref.afetch(ctx)
        except (KeyError, IndexError):
            return EMPTY
        return view._unsafe_primitive_scan_values()

    def run(self, ctx: Context) -> Iterator[T] | Sentinel:
        """Scan all primitive children via raw storage scan (sync)."""
        try:
            view = self.ref.fetch(ctx)
        except (KeyError, IndexError):
            return EMPTY
        return view._unsafe_primitive_scan_values()

    def __repr__(self) -> str:
        return f"ScanPrimitivesUnsafeOp({self.ref!r})"


class ClearPrimitivesUnsafeCmd(Command):
    """Clear all primitive children via _unsafe_primitive_clear().

    Scan + ctx.delete() each -- no validation, no descendant cleanup.
    The caller must know all children are primitives.

    The ref must implement:
        fetch(ctx) -> view with _unsafe_primitive_clear() method
    """

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def arun(self, ctx: Context) -> None:
        """Clear all primitive children via scan + delete."""
        view = await self.ref.afetch(ctx)
        view._unsafe_primitive_clear()

    def run(self, ctx: Context) -> None:
        """Clear all primitive children via scan + delete (sync)."""
        view = self.ref.fetch(ctx)
        view._unsafe_primitive_clear()

    def __repr__(self) -> str:
        return f"ClearPrimitivesUnsafeCmd({self.ref!r})"
