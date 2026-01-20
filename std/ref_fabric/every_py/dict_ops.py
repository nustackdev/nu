"""Dict operations for Term expressions.

This module provides type-safe operations on dict Terms:

Access: DictKeysOp, DictValuesOp, DictItemsOp, DictGetOp

Design principles:
1. Atomic classes: one operation = one class
2. All arguments support Term or literal
3. Proper base class inheritance (UnaryOp, NAryOp)
4. Runtime type checking with TypeError for invalid types
"""

from __future__ import annotations

from term.typing import NOT_SET, NotSet, Sentinel, is_notset

from every._abc import NAryOp, UnaryOp


__all__ = [
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
]


# =============================================================================
# MAPPING ACCESS (Unary)
# =============================================================================


class DictKeysOp[K](UnaryOp[list[K]]):
    """Get keys from dict: list(dict.keys())."""

    def _apply_op(self, operand: object) -> list[K]:
        if not isinstance(operand, dict):
            raise TypeError(f"keys_() requires dict, got {type(operand).__name__}")
        return list(operand.keys())  # type: ignore


class DictValuesOp[V](UnaryOp[list[V]]):
    """Get values from dict: list(dict.values())."""

    def _apply_op(self, operand: object) -> list[V]:
        if not isinstance(operand, dict):
            raise TypeError(f"values_() requires dict, got {type(operand).__name__}")
        return list(operand.values())  # type: ignore


class DictItemsOp[K, V](UnaryOp[list[tuple[K, V]]]):
    """Get items from dict: list(dict.items())."""

    def _apply_op(self, operand: object) -> list[tuple[K, V]]:
        if not isinstance(operand, dict):
            raise TypeError(f"items_() requires dict, got {type(operand).__name__}")
        return list(operand.items())  # type: ignore


# =============================================================================
# DICT GET (NAryOp - optional default)
# =============================================================================


class DictGetOp[V](NAryOp[V | Sentinel]):
    """Get value from dict with optional default: dict.get(key, default) or dict[key].

    All args can be Terms for dynamic access.
    """

    def __init__(self, operand: object, key: object, default: object | NotSet = NOT_SET) -> None:
        """Initialize get operation."""
        if is_notset(default):
            super().__init__(operand, key)
        else:
            super().__init__(operand, key, default)

    def _apply_op(self, operand: object, key: object, default: object = NOT_SET) -> V | Sentinel:
        if not isinstance(operand, dict):
            raise TypeError(f"get_() requires dict, got {type(operand).__name__}")
        if is_notset(default):
            return operand[key]  # type: ignore
        return operand.get(key, default)  # type: ignore
