"""Shared collection mutation commands.

ClearCmd: Clear all items from a mutable collection.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode


__all__ = [
    "ClearCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ClearCmd(ScalarCommand):
    """Clear all items: collection.clear(). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        if not hasattr(target, "clear"):
            raise TypeError(f"clear() requires clearable collection, got {type(target).__name__}")
        target.clear()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        if not hasattr(target, "clear"):
            raise TypeError(f"clear() requires clearable collection, got {type(target).__name__}")
        target.clear()
