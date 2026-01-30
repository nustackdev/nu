"""Mapping ABC morphisms.

Access: KeysOp, ValuesOp, ItemsOp, GetOp
"""

from __future__ import annotations

from collections.abc import Mapping

from everyabc import Sentinel, TernaryOperation, UnaryOperation


__all__ = [
    "GetOp",
    "ItemsOp",
    "KeysOp",
    "ValuesOp",
]


# =============================================================================
# MAPPING ACCESS (Unary)
# =============================================================================


class KeysOp[K](UnaryOperation[list[K]]):
    """Get keys from mapping: list(mapping.keys())."""

    def apply(self, operand: object) -> list[K]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"keys_() requires mapping, got {type(operand).__name__}")
        return list(operand.keys())  # type: ignore


class ValuesOp[V](UnaryOperation[list[V]]):
    """Get values from mapping: list(mapping.values())."""

    def apply(self, operand: object) -> list[V]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"values_() requires mapping, got {type(operand).__name__}")
        return list(operand.values())  # type: ignore


class ItemsOp[K, V](UnaryOperation[list[tuple[K, V]]]):
    """Get items from mapping: list(mapping.items())."""

    def apply(self, operand: object) -> list[tuple[K, V]]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"items_() requires mapping, got {type(operand).__name__}")
        return list(operand.items())  # type: ignore


# =============================================================================
# MAPPING GET (Ternary)
# =============================================================================


class GetOp[V](TernaryOperation[V]):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"get_() requires mapping, got {type(first).__name__}")
        if third is None:
            return first[second]  # type: ignore
        return first.get(second, third)  # type: ignore
