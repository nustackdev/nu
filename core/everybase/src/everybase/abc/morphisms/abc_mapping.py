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
    BinaryOperation,
    Sentinel,
    TernaryCommand,
    TernaryOperation,
    UnaryOperation,
)


__all__ = [
    "DeleteItemCmd",
    "GetOp",
    "ISliceOp",
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


class KeyAtOp(BinaryOperation):
    """Get key at index position: mapping.key_at(idx).

    If the mapping has a ``key_at`` method (e.g. IndexedDictView), calls it
    directly for O(1) single-key read.  Otherwise falls back to
    ``itertools.islice`` over keys.
    """

    def apply(self, first: object, second: object) -> object | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"key_at_() requires mapping, got {type(first).__name__}")
        idx = int(second)  # type: ignore[arg-type]
        if hasattr(first, "key_at"):
            return first.key_at(idx)  # type: ignore[union-attr]
        # Fallback: iterate keys up to idx
        import itertools

        keys = list(itertools.islice(first.keys(), idx, idx + 1))
        if not keys:
            return INVALID
        return keys[0]


class ISliceOp(TernaryOperation):
    """Slice a mapping by iteration order: mapping.islice(start, stop).

    If the mapping has an ``islice`` method (e.g. IndexedDictView), calls it
    directly for O(1) key-index access.  Otherwise falls back to
    ``itertools.islice`` over items.
    """

    def apply(self, first: object, second: object, third: object) -> object | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"islice_() requires mapping, got {type(first).__name__}")
        start = int(second)  # type: ignore[arg-type]
        stop = int(third) if third is not None else None  # type: ignore[arg-type]
        # Prefer native islice if available (IndexedDictView)
        if hasattr(first, "islice"):
            return first.islice(start, stop)  # type: ignore[union-attr]
        # Fallback: build a dict from itertools.islice
        import itertools

        sliced = itertools.islice(first.items(), start, stop)
        return dict(sliced)


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
