"""Shared collection mutation commands.

ClearCommand: clear all items from a mutable collection; mutates, returns nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Command
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "ClearCommand",
]


class ClearCommand(Command):
    """Clear all items: collection.clear(); mutates the collection, returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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
