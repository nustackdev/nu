# ruff: noqa: D102
"""Mapping collection — protocols + bases + mutations.

MappingProtocol/Base = Collection + keys_/values_/items_/get_
MutableMappingProtocol/Base = Mapping + set_/delete/update_

Follows Python's collections.abc.Mapping / MutableMapping pattern.

Type Parameters:
    CollectionT: Native Python collection type (dict[str, int], etc.)
    KeyT: Native Python key type (str, int, etc.)
    ValueT: Native Python value type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
        (map_, filter_, keys_, values_, items_, update_)
    ValueResultT: Wrapped result for value-level operations
        (get_, set_, delete, sum_, min_, max_)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from ..capabilities.col_collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from collections.abc import Mapping

    from everybase.core import Term


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
        CollectionResultT: Result for collection-level ops (keys_, values_, items_)
        ValueResultT: Result for value-level ops (get_)
    """

    def keys_(self) -> CollectionResultT: ...
    def values_(self) -> CollectionResultT: ...
    def items_(self) -> CollectionResultT: ...
    def get_(self, key: KeyT, default: ValueT | None = None) -> ValueResultT: ...


class MutableMappingProtocol[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    MappingProtocol[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Protocol,
):
    """Protocol for mutable mapping values — like collections.abc.MutableMapping.

    Type Parameters:
        CollectionT: Native Python collection type
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level ops (update_)
        ValueResultT: Result for value-level ops (set_, delete)
    """

    def set_(self, key: KeyT, value: ValueT) -> ValueResultT: ...
    def delete(self, key: KeyT) -> ValueResultT: ...
    def update_(self, other: Mapping[KeyT, ValueT]) -> CollectionResultT: ...


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
        CollectionResultT: Result for collection-level ops (keys_, values_, items_)
        ValueResultT: Result for value-level ops (get_)
    """

    def _wrap_keys_result(self, operand: Term) -> CollectionResultT:
        """Override in subclass to wrap keys sequence result."""
        raise NotImplementedError()

    def _wrap_values_result(self, operand: Term) -> CollectionResultT:
        """Override in subclass to wrap values sequence result."""
        raise NotImplementedError()

    def _wrap_items_result(self, operand: Term) -> CollectionResultT:
        """Override in subclass to wrap items sequence result."""
        raise NotImplementedError()

    def _wrap_value_result(self, operand: Term) -> ValueResultT:
        """Override in subclass to wrap single value result."""
        raise NotImplementedError()

    def keys_(self) -> CollectionResultT:
        """Get all keys."""
        from ..morphisms.abc_mapping import KeysOp

        return cast("CollectionResultT", self._wrap_keys_result(KeysOp(self)))

    def values_(self) -> CollectionResultT:
        """Get all values."""
        from ..morphisms.abc_mapping import ValuesOp

        return cast("CollectionResultT", self._wrap_values_result(ValuesOp(self)))

    def items_(self) -> CollectionResultT:
        """Get all key-value pairs."""
        from ..morphisms.abc_mapping import ItemsOp

        return cast("CollectionResultT", self._wrap_items_result(ItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ValueResultT:
        """Get value with default."""
        from ..morphisms.abc_mapping import GetOp

        return cast("ValueResultT", self._wrap_value_result(GetOp(self, key, default)))


class MutableMappingBase[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    MappingBase[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mutable mapping values — like collections.abc.MutableMapping.

    Type Parameters:
        CollectionT: Native Python collection type
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level ops (update_)
        ValueResultT: Result for value-level ops (set_, delete)
    """

    def set_(self, key: KeyT, value: ValueT) -> ValueResultT:
        """Set value at key."""
        from ..morphisms.abc_mapping import SetItemCmd

        return cast("ValueResultT", self._wrap_value_result(SetItemCmd(self, key, value)))

    def delete(self, key: KeyT) -> ValueResultT:
        """Delete entry by key."""
        from ..morphisms.abc_mapping import DeleteItemCmd

        return cast("ValueResultT", self._wrap_value_result(DeleteItemCmd(self, key)))

    def update_(self, other: Mapping[KeyT, ValueT]) -> CollectionResultT:
        """Update mapping with another mapping."""
        from ..morphisms.abc_mapping import UpdateCmd

        return cast("CollectionResultT", self._wrap_iterable_result(UpdateCmd(self, other)))
