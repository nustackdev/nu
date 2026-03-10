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
    UnaryCommand,
    UnaryOperation,
)


__all__ = [
    "CopyOp",
    "DeleteItemCmd",
    "DictPopCmd",
    "GetOp",
    "ItemsOp",
    "KeyAtOp",
    "KeysOp",
    "PopItemCmd",
    "SetDefaultCmd",
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

    def apply(self, left: object, right: object) -> object | Sentinel:
        """Apply."""
        if not isinstance(left, Mapping):
            raise TypeError(f"key_at() requires mapping, got {type(left).__name__}")
        idx = int(right)  # type: ignore[arg-type]
        if hasattr(left, "key_at"):
            return left.key_at(idx)  # type: ignore[union-attr]
        # Fallback: iterate keys up to idx
        import itertools

        keys = list(itertools.islice(left.keys(), idx, idx + 1))
        if not keys:
            return INVALID
        return keys[0]


# =============================================================================
# COMMANDS (impure)
# =============================================================================


class SetItemCmd[K, V](TernaryCommand[None]):
    """Set value at key: mapping[key] = value. Returns None."""

    def apply(self, first: object, second: object, third: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(first, MutableMapping):
            raise TypeError(f"set() requires mutable mapping, got {type(first).__name__}")
        first[second] = third
        return None


class DeleteItemCmd[K](BinaryCommand[None]):
    """Delete entry by key: del mapping[key]. Returns None."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableMapping):
            raise TypeError(f"delete() requires mutable mapping, got {type(left).__name__}")
        try:
            del left[right]
        except KeyError:
            return INVALID
        return None


class UpdateCmd[K, V](BinaryCommand[None]):
    """Update mapping with another: mapping.update(other). Returns None (mutates in-place)."""

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableMapping):
            raise TypeError(f"update() requires mutable mapping, got {type(left).__name__}")
        if not isinstance(right, Mapping):
            return INVALID
        left.update(right)
        return None


class DictPopCmd[K, V](TernaryCommand[V]):
    """Pop value by key with optional default: mapping.pop(key, default). Returns value or default."""

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, MutableMapping):
            raise TypeError(f"pop() requires mutable mapping, got {type(first).__name__}")
        if third is None:
            try:
                return first.pop(second)  # type: ignore[arg-type]
            except KeyError:
                return INVALID
        return first.pop(second, third)  # type: ignore[arg-type]


class PopItemCmd[K, V](UnaryCommand[tuple[K, V]]):
    """Pop arbitrary item: mapping.popitem(). Returns (key, value) tuple."""

    def apply(self, operand: object) -> tuple[K, V] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"popitem() requires mutable mapping, got {type(operand).__name__}")
        try:
            return operand.popitem()  # type: ignore[union-attr]
        except KeyError:
            return INVALID


class SetDefaultCmd[K, V](TernaryCommand[V]):
    """Set default value if key missing: mapping.setdefault(key, default). Returns value at key."""

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, MutableMapping):
            raise TypeError(f"setdefault() requires mutable mapping, got {type(first).__name__}")
        return first.setdefault(second, third)  # type: ignore[arg-type]


class CopyOp[K, V](UnaryOperation[dict[K, V]]):
    """Shallow copy: mapping.copy(). Returns new dict."""

    def apply(self, operand: object) -> dict[K, V] | Sentinel:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"copy() requires mapping, got {type(operand).__name__}")
        return dict(operand)  # type: ignore[arg-type]
