"""Dict morphisms for everybase.

Access: DictKeysOp, DictValuesOp, DictItemsOp, DictGetOp
"""

from __future__ import annotations

from everyabc import NAryMorphism, Operation, Sentinel, UnaryMorphism


__all__ = [
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
]


# =============================================================================
# MAPPING ACCESS (Unary)
# =============================================================================


class DictKeysOp[K](Operation, UnaryMorphism[list[K]]):
    """Get keys from dict: list(dict.keys())."""

    def _apply(self, operand: object) -> list[K]:
        if not isinstance(operand, dict):
            raise TypeError(f"keys_() requires dict, got {type(operand).__name__}")
        return list(operand.keys())  # type: ignore


class DictValuesOp[V](Operation, UnaryMorphism[list[V]]):
    """Get values from dict: list(dict.values())."""

    def _apply(self, operand: object) -> list[V]:
        if not isinstance(operand, dict):
            raise TypeError(f"values_() requires dict, got {type(operand).__name__}")
        return list(operand.values())  # type: ignore


class DictItemsOp[K, V](Operation, UnaryMorphism[list[tuple[K, V]]]):
    """Get items from dict: list(dict.items())."""

    def _apply(self, operand: object) -> list[tuple[K, V]]:
        if not isinstance(operand, dict):
            raise TypeError(f"items_() requires dict, got {type(operand).__name__}")
        return list(operand.items())  # type: ignore


# =============================================================================
# DICT GET (NAryMorphism - optional default)
# =============================================================================


class DictGetOp[V](Operation, NAryMorphism[V | Sentinel]):
    """Get value from dict with optional default: dict.get(key, default) or dict[key]."""

    def __init__(self, operand: object, key: object, default: object | None = None) -> None:
        """Initialize get operation."""
        if default is None:
            super().__init__(operand, key)
        else:
            super().__init__(operand, key, default)

    def _apply(self, operand: object, key: object, default: object | None = None) -> V | Sentinel:
        if not isinstance(operand, dict):
            raise TypeError(f"get_() requires dict, got {type(operand).__name__}")
        if default is None:
            return operand[key]  # type: ignore
        return operand.get(key, default)  # type: ignore
