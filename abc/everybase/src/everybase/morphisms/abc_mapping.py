"""Dict morphisms for everybase.

Access: DictKeysOp, DictValuesOp, DictItemsOp, DictGetOp
"""

from __future__ import annotations

from collections.abc import Mapping

from everyabc import Sentinel, TernaryOperation, UnaryOperation


__all__ = [
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
]


# =============================================================================
# MAPPING ACCESS (Unary)
# =============================================================================


class DictKeysOp[K](UnaryOperation[list[K]]):
    """Get keys from dict: list(dict.keys())."""

    def apply(self, operand: object) -> list[K]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"keys_() requires dict, got {type(operand).__name__}")
        return list(operand.keys())  # type: ignore


class DictValuesOp[V](UnaryOperation[list[V]]):
    """Get values from dict: list(dict.values())."""

    def apply(self, operand: object) -> list[V]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"values_() requires dict, got {type(operand).__name__}")
        return list(operand.values())  # type: ignore


class DictItemsOp[K, V](UnaryOperation[list[tuple[K, V]]]):
    """Get items from dict: list(dict.items())."""

    def apply(self, operand: object) -> list[tuple[K, V]]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"items_() requires dict, got {type(operand).__name__}")
        return list(operand.items())  # type: ignore


# =============================================================================
# DICT GET (Ternary)
# =============================================================================


class DictGetOp[V](TernaryOperation[V]):
    """Get value from dict with optional default: dict.get(key, default) or dict[key]."""

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"get_() requires mapping, got {type(first).__name__}")
        if third is None:
            return first[second]  # type: ignore
        return first.get(second, third)  # type: ignore
