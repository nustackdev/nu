"""Mapping collection: bases + mutations.

MappingForm = Collection + keys/values/items/get_item
MutableMappingForm = Mapping + set_item/del_item/update/pop/popitem/setdefault/clear

Follows Python's collections.abc.Mapping / MutableMapping pattern.

Type Parameters:
    CollectionT: Native Python collection type (dict[str, int], etc.)
    KeyT: Native Python key type (str, int, etc.)
    ValueT: Native Python value type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
        (keys, values, items, update)
    ValueResultT: Wrapped result for value-level interactions
        (get_item, key_at)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from .collection import CollectionForm


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang import Arg, Nu


__all__ = [
    "MappingForm",
    "MutableMappingForm",
    "ReactiveMappingForm",
]


CollectionT = TypeVar("CollectionT")
KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")
CollectionResultT = TypeVar("CollectionResultT")
ValueResultT = TypeVar("ValueResultT")


class MappingForm(
    CollectionForm[KeyT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mapping values, like collections.abc.Mapping.

    Subclasses must override:
        _wrap_keys_result(operand): Wrap keys query result.
        _wrap_values_result(operand): Wrap values query result.
        _wrap_items_result(operand): Wrap items query result.
        _wrap_value_result(operand): Wrap single-value result.
        _wrap_mapping_result(operand): Wrap mapping-level result (copy, merge, merge_update).

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

    def _wrap_mapping_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap mapping-level result (copy, merge, merge_update)."""
        raise NotImplementedError()

    def __getitem__(self, key: Arg[KeyT]) -> ValueResultT:
        """Key → value via At."""
        from nu.core import GetItem as At

        return cast("ValueResultT", self._wrap_value_result(At(self, key)))

    def keys(self) -> CollectionResultT:
        """Get all keys."""
        from .mapping_interactions import Keys

        return cast("CollectionResultT", self._wrap_keys_result(Keys(self)))

    def values(self) -> CollectionResultT:
        """Get all values."""
        from .mapping_interactions import Values

        return cast("CollectionResultT", self._wrap_values_result(Values(self)))

    def items(self) -> CollectionResultT:
        """Get all key-value pairs."""
        from .mapping_interactions import Items

        return cast("CollectionResultT", self._wrap_items_result(Items(self)))

    def get_item(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Get value with default."""
        from .mapping_interactions import Get

        return cast("ValueResultT", self._wrap_value_result(Get(self, key, default)))

    def copy(self) -> CollectionResultT:
        """Shallow copy: mapping.copy(). Query yielding a new mapping."""
        from .mapping_interactions import Copy

        return cast("CollectionResultT", self._wrap_mapping_result(Copy(self)))

    def reversed_keys(self) -> CollectionResultT:
        """Keys in reverse insertion order: reversed(mapping). Query (3.8+)."""
        from .mapping_interactions import ReversedKeys

        return cast("CollectionResultT", self._wrap_keys_result(ReversedKeys(self)))

    def merge(self, other: Arg[Mapping[KeyT, ValueT]]) -> CollectionResultT:
        """Merge into a new mapping: mapping | other. Query yielding a new mapping."""
        from .mapping_interactions import Merge

        return cast("CollectionResultT", self._wrap_mapping_result(Merge(self, other)))


class MutableMappingForm(
    MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mutable mapping values, like collections.abc.MutableMapping.

    Type Parameters:
        CollectionT: Native Python collection type
        KeyT: Native Python key type
        ValueT: Native Python value type
        CollectionResultT: Result for collection-level interactions (update)
        ValueResultT: Result for value-level interactions (get, pop, setdefault)
    """

    def set_item(self, key: Arg[KeyT], value: Arg[ValueT]) -> Any:  # noqa: ANN401
        """Set value at key. Mutating Command; returns nothing."""
        from nu.core.access import SetItem

        return SetItem(self, key, value)

    def del_item(self, key: Arg[KeyT]) -> Any:  # noqa: ANN401
        """Delete entry by key. Mutating Command; returns nothing."""
        from .mapping_interactions import DeleteItem

        return DeleteItem(self, key)

    def update(self, other: Arg[Mapping[KeyT, ValueT]]) -> Any:  # noqa: ANN401
        """Update mapping with another mapping. Mutating Command; returns nothing."""
        from .mapping_interactions import Update

        return Update(self, other)

    def pop(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Remove key and return value, or default if missing."""
        from .mapping_interactions import DictPop

        return cast("ValueResultT", self._wrap_value_result(DictPop(self, key, default)))

    def popitem(self) -> ValueResultT:
        """Remove and return arbitrary (key, value) pair."""
        from .mapping_interactions import PopItem

        return cast("ValueResultT", self._wrap_value_result(PopItem(self)))

    def setdefault(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Get value at key, setting it to default if missing."""
        from .mapping_interactions import SetDefault

        return cast("ValueResultT", self._wrap_value_result(SetDefault(self, key, default)))

    def merge_update(self, other: Arg[Mapping[KeyT, ValueT]]) -> CollectionResultT:
        """In-place merge: mapping |= other. Mutating Action; yields the mapping."""
        from .mapping_interactions import MergeUpdate

        return cast("CollectionResultT", self._wrap_mapping_result(MergeUpdate(self, other)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items."""
        from .shared_interactions import Clear

        return Clear(self)


class ReactiveMappingForm(
    MutableMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Reactive mapping. Adds on_change() for any-change observation.

    Provides (in addition to MutableMappingForm):
        on_change() → OnChange

    The three tree-aware methods (on_child_change, on_children_change,
    on_descendants_change) are shape-domain and live on
    ``nu.domains.shape.forms.collection.ReactiveCollectionForm``.
    """

    def on_change(self) -> object:
        """Subscribe to any change on this mapping slot."""
        from nu.reactive import OnChange

        return OnChange(self)
