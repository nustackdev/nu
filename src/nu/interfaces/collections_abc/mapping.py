# ruff: noqa: D102
"""Mapping collection — protocols + bases + mutations.

MappingProtocol/Base = Collection + keys/values/items/get
MutableMappingProtocol/Base = Mapping + set/delete/update

Follows Python's collections.abc.Mapping / MutableMapping pattern.

Type Parameters:
    CollectionT: Native Python collection type (dict[str, int], etc.)
    KeyT: Native Python key type (str, int, etc.)
    ValueT: Native Python value type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
        (keys, values, items, update)
    ValueResultT: Wrapped result for value-level operations
        (get, key_at)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from .collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.terms import Arg, IntArg, Nu

    from nu.interfaces.primitives import NoneI


__all__ = [
    "MappingBase",
    "MappingProtocol",
    "MutableMappingBase",
    "MutableMappingProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


class MappingProtocol[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    CollectionProtocol[KeyT, CollectionResultT, ValueResultT],
    Protocol,
):
    """Protocol for mapping values — like collections.abc.Mapping.

    Type Parameters:
        CollectionT: Native Python collection type (dict[str, int])
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level ops (keys, values, items)
        ValueResultT: Result for value-level ops (get)
    """

    def keys(self) -> CollectionResultT: ...
    def values(self) -> CollectionResultT: ...
    def items(self) -> CollectionResultT: ...
    def get(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT: ...


class MutableMappingProtocol[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    MappingProtocol[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Protocol,
):
    """Protocol for mutable mapping values — like collections.abc.MutableMapping.

    Type Parameters:
        CollectionT: Native Python collection type
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level ops (update)
        ValueResultT: Result for value-level ops (set, delete)
    """

    def set(self, key: Arg[KeyT], value: Arg[ValueT]) -> NoneI: ...
    def delete(self, key: Arg[KeyT]) -> NoneI: ...
    def update(self, other: Arg[Mapping[KeyT, ValueT]]) -> NoneI: ...
    def pop(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT: ...
    def popitem(self) -> ValueResultT: ...
    def setdefault(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT: ...
    def clear(self) -> NoneI: ...
    def copy(self) -> ValueResultT: ...


# =============================================================================
# BASES
# =============================================================================


class MappingBase[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    CollectionBase[KeyT, CollectionResultT, ValueResultT],
):
    """Base for mapping values — like collections.abc.Mapping.

    Subclasses must override:
        _wrap_keys_result(operand): Wrap keys query result.
        _wrap_values_result(operand): Wrap values query result.
        _wrap_items_result(operand): Wrap items query result.
        _wrap_value_result(operand): Wrap single-value result.

    Type Parameters:
        CollectionT: Native Python collection type (dict[str, int])
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level ops (keys, values, items)
        ValueResultT: Result for value-level ops (get)
    """

    def _wrap_keys_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap keys sequence result."""
        raise NotImplementedError()

    def _wrap_values_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap values sequence result."""
        raise NotImplementedError()

    def _wrap_items_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap items sequence result."""
        raise NotImplementedError()

    def _wrap_value_result(self, operand: Nu) -> ValueResultT:
        """Override in subclass to wrap single value result."""
        raise NotImplementedError()

    def keys(self) -> CollectionResultT:
        """Get all keys."""
        from .mapping_ops import KeysOp

        return cast("CollectionResultT", self._wrap_keys_result(KeysOp(self)))

    def values(self) -> CollectionResultT:
        """Get all values."""
        from .mapping_ops import ValuesOp

        return cast("CollectionResultT", self._wrap_values_result(ValuesOp(self)))

    def items(self) -> CollectionResultT:
        """Get all key-value pairs."""
        from .mapping_ops import ItemsOp

        return cast("CollectionResultT", self._wrap_items_result(ItemsOp(self)))

    def get(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Get value with default."""
        from .mapping_ops import GetOp

        return cast("ValueResultT", self._wrap_value_result(GetOp(self, key, default)))

    def key_at(self, idx: IntArg) -> ValueResultT:
        """Get key at index position."""
        from .mapping_ops import KeyAtOp

        return cast("ValueResultT", self._wrap_value_result(KeyAtOp(self, idx)))


class MutableMappingBase[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    MappingBase[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mutable mapping values — like collections.abc.MutableMapping.

    Type Parameters:
        CollectionT: Native Python collection type
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level ops (update)
        ValueResultT: Result for value-level ops (get, key_at)
    """

    def set(self, key: Arg[KeyT], value: Arg[ValueT]) -> NoneI:
        """Set value at key."""
        from .mapping_ops import SetItemCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(SetItemCmd(self, key, value))

    def delete(self, key: Arg[KeyT]) -> NoneI:
        """Delete entry by key."""
        from .mapping_ops import DeleteItemCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(DeleteItemCmd(self, key))

    def update(self, other: Arg[Mapping[KeyT, ValueT]]) -> NoneI:
        """Update mapping with another mapping."""
        from .mapping_ops import UpdateCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(UpdateCmd(self, other))

    def pop(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Remove key and return value, or default if missing."""
        from .mapping_ops import DictPopCmd

        return cast("ValueResultT", self._wrap_value_result(DictPopCmd(self, key, default)))

    def popitem(self) -> ValueResultT:
        """Remove and return arbitrary (key, value) pair."""
        from .mapping_ops import PopItemCmd

        return cast("ValueResultT", self._wrap_value_result(PopItemCmd(self)))

    def setdefault(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Get value at key, setting it to default if missing."""
        from .mapping_ops import SetDefaultCmd

        return cast("ValueResultT", self._wrap_value_result(SetDefaultCmd(self, key, default)))

    def clear(self) -> NoneI:
        """Remove all items."""
        from .shared_ops import ClearCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(ClearCmd(self))

    def copy(self) -> ValueResultT:
        """Shallow copy."""
        from .mapping_ops import CopyOp

        return cast("ValueResultT", self._wrap_value_result(CopyOp(self)))
