"""Shared collection mutation commands.

ClearCmd: Clear all items from a mutable collection.
"""

from __future__ import annotations

from everyabc import UnaryCommand


__all__ = [
    "ClearCmd",
]


class ClearCmd(UnaryCommand[None]):
    """Clear all items: collection.clear(). Returns None."""

    def apply(self, operand: object) -> None:
        """Apply."""
        if not hasattr(operand, "clear"):
            raise TypeError(f"clear() requires clearable collection, got {type(operand).__name__}")
        operand.clear()  # type: ignore[union-attr]
        return None
