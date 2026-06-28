"""Mapping collection — bases + mutations.

MappingForm = Collection + keys/values/items/get
MutableMappingForm = Mapping + set/delete/update/pop/popitem/setdefault/clear

Follows Python's collections.abc.Mapping / MutableMapping pattern.

Type Parameters:
    CollectionT: Native Python collection type (dict[str, int], etc.)
    KeyT: Native Python key type (str, int, etc.)
    ValueT: Native Python value type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
        (keys, values, items, update)
    ValueResultT: Wrapped result for value-level interactions
        (get, key_at)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .collection import CollectionForm


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu2.lang import Arg, Nu


__all__ = [
    "MappingForm",
    "MutableMappingForm",
]


class MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    CollectionForm[KeyT, CollectionResultT, ValueResultT],
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
        CollectionResultT: Result for collection-level interactions (keys, values, items)
        ValueResultT: Result for value-level interactions (get)
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

    def __getitem__(self, key: Arg[KeyT]) -> ValueResultT:
        """Key → value via At."""
        from nu2.core import GetItem as At

        return cast("ValueResultT", self._wrap_value_result(At(self, key)))

    def keys(self) -> CollectionResultT:
        """Get all keys."""
        from .mapping_interactions import KeysQuery

        return cast("CollectionResultT", self._wrap_keys_result(KeysQuery(self)))

    def values(self) -> CollectionResultT:
        """Get all values."""
        from .mapping_interactions import ValuesQuery

        return cast("CollectionResultT", self._wrap_values_result(ValuesQuery(self)))

    def items(self) -> CollectionResultT:
        """Get all key-value pairs."""
        from .mapping_interactions import ItemsQuery

        return cast("CollectionResultT", self._wrap_items_result(ItemsQuery(self)))

    def get(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Get value with default."""
        from .mapping_interactions import GetQuery

        return cast("ValueResultT", self._wrap_value_result(GetQuery(self, key, default)))

    def copy(self) -> Any:  # noqa: ANN401
        """Shallow copy: mapping.copy(). Query yielding a new mapping."""
        from .mapping_interactions import CopyQuery

        return CopyQuery(self)

    def reversed_keys(self) -> CollectionResultT:
        """Keys in reverse insertion order: reversed(mapping). Query (3.8+)."""
        from .mapping_interactions import ReversedKeysQuery

        return cast("CollectionResultT", self._wrap_keys_result(ReversedKeysQuery(self)))

    def merge(self, other: Arg[Mapping[KeyT, ValueT]]) -> Any:  # noqa: ANN401
        """Merge into a new mapping: mapping | other. Query yielding a new mapping."""
        from .mapping_interactions import MergeQuery

        return MergeQuery(self, other)


class MutableMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT](
    MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mutable mapping values — like collections.abc.MutableMapping.

    Type Parameters:
        CollectionT: Native Python collection type
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level interactions (update)
        ValueResultT: Result for value-level interactions (get, pop, setdefault)
    """

    def set(self, key: Arg[KeyT], value: Arg[ValueT]) -> Any:  # noqa: ANN401
        """Set value at key. Mutating Command; returns nothing."""
        from .mapping_interactions import SetItemCommand

        return SetItemCommand(self, key, value)

    def delete(self, key: Arg[KeyT]) -> Any:  # noqa: ANN401
        """Delete entry by key. Mutating Command; returns nothing."""
        from .mapping_interactions import DeleteItemCommand

        return DeleteItemCommand(self, key)

    def update(self, other: Arg[Mapping[KeyT, ValueT]]) -> Any:  # noqa: ANN401
        """Update mapping with another mapping. Mutating Command; returns nothing."""
        from .mapping_interactions import UpdateCommand

        return UpdateCommand(self, other)

    def pop(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Remove key and return value, or default if missing."""
        from .mapping_interactions import DictPopAction

        return cast("ValueResultT", self._wrap_value_result(DictPopAction(self, key, default)))

    def popitem(self) -> ValueResultT:
        """Remove and return arbitrary (key, value) pair."""
        from .mapping_interactions import PopItemAction

        return cast("ValueResultT", self._wrap_value_result(PopItemAction(self)))

    def setdefault(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Get value at key, setting it to default if missing."""
        from .mapping_interactions import SetDefaultAction

        return cast("ValueResultT", self._wrap_value_result(SetDefaultAction(self, key, default)))

    def merge_update(self, other: Arg[Mapping[KeyT, ValueT]]) -> Any:  # noqa: ANN401
        """In-place merge: mapping |= other. Mutating Action; yields the mapping."""
        from .mapping_interactions import MergeUpdateAction

        return MergeUpdateAction(self, other)

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items."""
        from .shared_interactions import ClearCommand

        return ClearCommand(self)
