"""Mapping morphisms — operations (pure) + commands (impure).

Operations:
    KeysOp: Get all keys
    ValuesOp: Get all values
    ItemsOp: Get all key-value pairs
    GetOp: Get value by key with default

Commands:
    SetItemCmd: Set value at key
    DeleteItemCmd: Delete entry by key
    UpdateCmd: Update mapping with another mapping
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping

from everybase.core import (
    INVALID,
    BinaryCommand,
    Sentinel,
    TernaryCommand,
    TernaryOperation,
    UnaryOperation,
)


__all__ = [
    "DeleteItemCmd",
    "GetOp",
    "ItemsOp",
    "KeysOp",
    "SetItemCmd",
    "UpdateCmd",
    "ValuesOp",
]


# =============================================================================
# OPERATIONS (pure)
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


class GetOp[V](TernaryOperation[V]):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"get_() requires mapping, got {type(first).__name__}")
        if third is None:
            return first[second]  # type: ignore
        return first.get(second, third)  # type: ignore


# =============================================================================
# COMMANDS (impure)
# =============================================================================


class SetItemCmd[K, V](TernaryCommand[V]):
    """Set value at key: mapping[key] = value. Returns the set value."""

    def apply(self, operand: object, key: object, value: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"setitem() requires mutable mapping, got {type(operand).__name__}")
        operand[key] = value
        return value  # type: ignore[return-value]


class DeleteItemCmd[K](BinaryCommand[None]):
    """Delete entry by key: del mapping[key]. Returns None."""

    def apply(self, operand: object, key: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"delitem() requires mutable mapping, got {type(operand).__name__}")
        try:
            del operand[key]
        except KeyError:
            return INVALID
        return None


class UpdateCmd[K, V](BinaryCommand[None]):
    """Update mapping with another: mapping.update(other). Returns None (mutates in-place)."""

    def apply(self, operand: object, other: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"update() requires mutable mapping, got {type(operand).__name__}")
        if not isinstance(other, Mapping):
            return INVALID
        operand.update(other)
        return None
