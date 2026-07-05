"""Virtuals collection interactions — unsafe scan / clear of primitive children.

ScanPrimitivesUnsafe: Scan all primitive children — _unsafe_primitive_scan_values().
ClearPrimitivesUnsafeCmd: Clear all primitive children — _unsafe_primitive_clear().

Require virtuals views with UnsafePrimitiveOpsBase in MRO. The container view Ref
is held as ``children[0]``; its ``fetch`` substrate method takes ``(rt, nid)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "ClearPrimitivesUnsafeCmd",
    "ScanPrimitivesUnsafe",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


class ScanPrimitivesUnsafe(ScalarQuery):
    """Scan all direct primitive child values via ``_unsafe_primitive_scan_values``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            try:
                view = ref._fetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            return view._unsafe_primitive_scan_values()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            try:
                view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            return view._unsafe_primitive_scan_values()

        return athunk

    def __repr__(self) -> str:
        return f"ScanPrimitivesUnsafe({self._children[0]!r})"


class ClearPrimitivesUnsafeCmd(Command):
    """Clear all primitive children via ``_unsafe_primitive_clear``."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            view = ref._fetch(rt, _child_nid(rt, nid, 0))
            view._unsafe_primitive_clear()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            view._unsafe_primitive_clear()

        return athunk

    def __repr__(self) -> str:
        return f"ClearPrimitivesUnsafeCmd({self._children[0]!r})"
