"""Shared collection mutation commands.

ClearCmd: Clear all items from a mutable collection.
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import Mode, UnaryQuery


__all__ = [
    "ClearCmd",
]


class ClearCmd(UnaryQuery[None]):
    """Clear all items: collection.clear(). Returns None."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> None:
        """Apply."""
        if not hasattr(operand, "clear"):
            raise TypeError(f"clear() requires clearable collection, got {type(operand).__name__}")
        operand.clear()  # type: ignore[union-attr]
        return None
