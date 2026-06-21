"""Shared collection mutation commands.

ClearQuery: Clear all items from a mutable collection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "ClearQuery",
]


class ClearQuery(ScalarQuery):
    """Clear all items: collection.clear(); yields the collection."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            if not hasattr(target, "clear"):
                raise TypeError(
                    f"clear() requires clearable collection, got {type(target).__name__}"
                )
            target.clear()
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            if not hasattr(target, "clear"):
                raise TypeError(
                    f"clear() requires clearable collection, got {type(target).__name__}"
                )
            target.clear()
            return target

        return athunk
