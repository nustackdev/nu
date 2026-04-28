"""Shared collection mutation commands.

ClearCmd: Clear all items from a mutable collection.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "ClearCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ClearCmd(ScalarQuery):
    """Clear all items: collection.clear(). Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not hasattr(operand, "clear"):
            raise TypeError(f"clear() requires clearable collection, got {type(operand).__name__}")
        operand.clear()
        return None
