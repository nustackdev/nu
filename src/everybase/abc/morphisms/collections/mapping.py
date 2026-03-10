"""Mapping morphisms — operations (pure) + commands (impure).

Operations:
    KeysOp: Get all keys
    ValuesOp: Get all values
    ItemsOp: Get all key-value pairs
    GetOp: Get value by key with default
    KeyAtOp: Get key at index position

Commands:
    SetItemCmd: Set value at key
    DeleteItemCmd: Delete entry by key
    UpdateCmd: Update mapping with another mapping
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, Mapping, MutableMapping, ValuesView

from everybase.core import (
    INVALID,
    BinaryCommand,
    BinaryOperation,
    Sentinel,
    TernaryCommand,
    TernaryOperation,
    UnaryOperation,
)


__all__ = [
    "DeleteItemCmd",
    "GetOp",
    "ItemsOp",
    "KeyAtOp",
    "KeysOp",
    "SetItemCmd",
    "UpdateCmd",
    "ValuesOp",
]


# =============================================================================
# OPERATIONS (pure)
# =============================================================================


class KeysOp[K](UnaryOperation[KeysView[K]]):
    """Get keys view from mapping: mapping.keys()."""

    def apply(self, operand: object) -> KeysView[K]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"keys() requires mapping, got {type(operand).__name__}")
        return operand.keys()  # type: ignore


class ValuesOp[V](UnaryOperation[ValuesView[V]]):
    """Get values view from mapping: mapping.values()."""

    def apply(self, operand: object) -> ValuesView[V]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"values() requires mapping, got {type(operand).__name__}")
        return operand.values()  # type: ignore


class ItemsOp[K, V](UnaryOperation[ItemsView[K, V]]):
    """Get items view from mapping: mapping.items()."""

    def apply(self, operand: object) -> ItemsView[K, V]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"items() requires mapping, got {type(operand).__name__}")
        return operand.items()  # type: ignore


class GetOp[V](TernaryOperation[V]):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"get() requires mapping, got {type(first).__name__}")
        if third is None:
            return first[second]  # type: ignore
        return first.get(second, third)  # type: ignore


class KeyAtOp(BinaryOperation):
    """Get key at index position: mapping.key_at(idx).

    If the mapping has a ``key_at`` method (e.g. IndexedDictView), calls it
    directly for O(1) single-key read.  Otherwise falls back to
    ``itertools.islice`` over keys.
    """

    def apply(self, first: object, second: object) -> object | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"key_at() requires mapping, got {type(first).__name__}")
        idx = int(second)  # type: ignore[arg-type]
        if hasattr(first, "key_at"):
            return first.key_at(idx)  # type: ignore[union-attr]
        # Fallback: iterate keys up to idx
        import itertools

        keys = list(itertools.islice(first.keys(), idx, idx + 1))
        if not keys:
            return INVALID
        return keys[0]


# =============================================================================
# COMMANDS (impure)
# =============================================================================


class SetItemCmd[K, V](TernaryCommand[None]):
    """Set value at key: mapping[key] = value. Returns None."""

    def apply(self, operand: object, key: object, value: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"set() requires mutable mapping, got {type(operand).__name__}")
        operand[key] = value
        return None


class DeleteItemCmd[K](BinaryCommand[None]):
    """Delete entry by key: del mapping[key]. Returns None."""

    def apply(self, operand: object, key: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"delete() requires mutable mapping, got {type(operand).__name__}")
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
