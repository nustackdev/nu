"""Shared collection mutation commands.

Clear: clear all items from a mutable collection; mutates, returns nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "Clear",
]


class Clear(Command):
    """Clear all items: collection.clear(); mutates the collection, returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            if not hasattr(target, "clear"):
                raise TypeError(
                    f"clear() requires clearable collection, got {type(target).__name__}"
                )
            target.clear()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            if not hasattr(target, "clear"):
                raise TypeError(
                    f"clear() requires clearable collection, got {type(target).__name__}"
                )
            target.clear()

        return athunk
