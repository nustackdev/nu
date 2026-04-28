"""Mapping ops.

KeysOp, ValuesOp, ItemsOp, GetOp
SetItemCmd, DeleteItemCmd, UpdateCmd
DictPopCmd, PopItemCmd, SetDefaultCmd
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, Mapping, MutableMapping, ValuesView
from typing import ClassVar

from nu.terms import (
    INVALID,
    BinaryQuery,
    Effect,
    Mode,
    Sentinel,
    TernaryQuery,
    UnaryQuery,
)


__all__ = [
    "DeleteItemCmd",
    "DictPopCmd",
    "GetOp",
    "ItemsOp",
    "KeysOp",
    "PopItemCmd",
    "SetDefaultCmd",
    "SetItemCmd",
    "UpdateCmd",
    "ValuesOp",
]


# =============================================================================
# MAPPING READS
# =============================================================================


class KeysOp[K](UnaryQuery[KeysView[K]]):
    """Get keys view from mapping: mapping.keys()."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> KeysView[K]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"keys() requires mapping, got {type(operand).__name__}")
        return operand.keys()  # type: ignore


class ValuesOp[V](UnaryQuery[ValuesView[V]]):
    """Get values view from mapping: mapping.values()."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> ValuesView[V]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"values() requires mapping, got {type(operand).__name__}")
        return operand.values()  # type: ignore


class ItemsOp[K, V](UnaryQuery[ItemsView[K, V]]):
    """Get items view from mapping: mapping.items()."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> ItemsView[K, V]:
        """Apply."""
        if not isinstance(operand, Mapping):
            raise TypeError(f"items() requires mapping, got {type(operand).__name__}")
        return operand.items()  # type: ignore


class GetOp[V](TernaryQuery[V]):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, Mapping):
            raise TypeError(f"get() requires mapping, got {type(first).__name__}")
        if third is None:
            return first[second]  # type: ignore
        return first.get(second, third)  # type: ignore


# =============================================================================
# MAPPING MUTATIONS
# =============================================================================


class SetItemCmd[K, V](TernaryQuery[None]):
    """Set value at key: mapping[key] = value. Returns None."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, first: object, second: object, third: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(first, MutableMapping):
            raise TypeError(f"set() requires mutable mapping, got {type(first).__name__}")
        first[second] = third
        return None


class DeleteItemCmd[K](BinaryQuery[None]):
    """Delete entry by key: del mapping[key]. Returns None."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableMapping):
            raise TypeError(f"delete() requires mutable mapping, got {type(left).__name__}")
        try:
            del left[right]
        except KeyError:
            return INVALID
        return None


class UpdateCmd[K, V](BinaryQuery[None]):
    """Update mapping with another: mapping.update(other). Returns None (mutates in-place)."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> None | Sentinel:
        """Apply."""
        if not isinstance(left, MutableMapping):
            raise TypeError(f"update() requires mutable mapping, got {type(left).__name__}")
        if not isinstance(right, Mapping):
            return INVALID
        left.update(right)
        return None


class DictPopCmd[K, V](TernaryQuery[V]):
    """Pop value by key with optional default: mapping.pop(key, default). Returns value or default."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

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


class PopItemCmd[K, V](UnaryQuery[tuple[K, V]]):
    """Pop arbitrary item: mapping.popitem(). Returns (key, value) tuple."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> tuple[K, V] | Sentinel:
        """Apply."""
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"popitem() requires mutable mapping, got {type(operand).__name__}")
        try:
            return operand.popitem()  # type: ignore[union-attr]
        except KeyError:
            return INVALID


class SetDefaultCmd[K, V](TernaryQuery[V]):
    """Set default value if key missing: mapping.setdefault(key, default). Returns value at key."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, first: object, second: object, third: object) -> V | Sentinel:
        """Apply."""
        if not isinstance(first, MutableMapping):
            raise TypeError(f"setdefault() requires mutable mapping, got {type(first).__name__}")
        return first.setdefault(second, third)  # type: ignore[arg-type]
