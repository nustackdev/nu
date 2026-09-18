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
    """Base for mapping values: key lookup plus key/value/item views.

    Notes:
        - The five `_wrap_*` methods are the override seam: `_wrap_value_result`
          covers subscript and `get_item`; the other four cover
          collection-shaped results (`keys`, `values`, `items`, `copy`,
          `merge`). A concrete mapping Form overrides all five to pick its
          own result types.
    """

    def _wrap_keys_result(self, operand: Nu) -> CollectionResultT:
        """Wrap a raw keys-view term as this Form's keys result type.

        Args:
            operand: the term producing the raw keys view.

        Notes:
            - Override point. The base implementation always raises;
              every concrete mapping Form must supply its own.
        """
        raise NotImplementedError()

    def _wrap_values_result(self, operand: Nu) -> CollectionResultT:
        """Wrap a raw values-view term as this Form's values result type.

        Args:
            operand: the term producing the raw values view.

        Notes:
            - Override point. The base implementation always raises;
              every concrete mapping Form must supply its own.
        """
        raise NotImplementedError()

    def _wrap_items_result(self, operand: Nu) -> CollectionResultT:
        """Wrap a raw items-view term as this Form's items result type.

        Args:
            operand: the term producing the raw items view.

        Notes:
            - Override point. The base implementation always raises;
              every concrete mapping Form must supply its own.
        """
        raise NotImplementedError()

    def _wrap_value_result(self, operand: Nu) -> ValueResultT:
        """Wrap a raw single-value term as this Form's value result type.

        Args:
            operand: the term producing the raw value.

        Notes:
            - Override point, used by `__getitem__`, `get_item`, and (on
              MutableMappingForm) `pop`/`popitem`/`setdefault`. The base
              implementation always raises; every concrete mapping Form
              must supply its own.
        """
        raise NotImplementedError()

    def _wrap_mapping_result(self, operand: Nu) -> CollectionResultT:
        """Wrap a raw mapping-shaped term as this Form's own type.

        Args:
            operand: the term producing the raw mapping.

        Notes:
            - Override point, used by `copy` and `merge` (and by
              `merge_update` on MutableMappingForm). The base implementation
              always raises; every concrete mapping Form must supply its own.
        """
        raise NotImplementedError()

    def __getitem__(self, key: Arg[KeyT]) -> ValueResultT:
        """Value at key: mapping[key].

        Args:
            key: the key to look up.

        Notes:
            - Raises at evaluation time when key is missing, matching
              Python's `dict[key]`. Use `get_item` for a default instead
              of a raise.

        Yields:
            The value at key. INVALID when self or key is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1})["a"])[0]
            1
        """
        from nu.core import GetItem as At

        return cast("ValueResultT", self._wrap_value_result(At(self, key)))

    def keys(self) -> CollectionResultT:
        """All keys of the mapping: mapping.keys().

        Yields:
            A view over the keys, in insertion order. INVALID when self is
            a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).keys())[0]
            dict_keys(['a', 'b'])
        """
        from .mapping_interactions import Keys

        return cast("CollectionResultT", self._wrap_keys_result(Keys(self)))

    def values(self) -> CollectionResultT:
        """All values of the mapping: mapping.values().

        Yields:
            A view over the values, in insertion order. INVALID when self
            is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).values())[0]
            dict_values([1, 2])
        """
        from .mapping_interactions import Values

        return cast("CollectionResultT", self._wrap_values_result(Values(self)))

    def items(self) -> CollectionResultT:
        """All (key, value) pairs of the mapping: mapping.items().

        Yields:
            A view over the (key, value) pairs, in insertion order. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).items())[0]
            dict_items([('a', 1), ('b', 2)])
        """
        from .mapping_interactions import Items

        return cast("CollectionResultT", self._wrap_items_result(Items(self)))

    def get_item(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Value at key, falling back to default: mapping.get_item(key, default).

        Args:
            key: the key to look up.
            default: the value to yield when key is missing.

        Notes:
            - Omitting default does not make a missing key safe: with no
              default this behaves like `mapping[key]` and raises at
              evaluation time on a missing key. Pass a default to get
              Python `dict.get`-style fallback behaviour instead.

        Yields:
            The value at key, or default when key is missing and default
            is given. INVALID when self or key is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).get_item("a"))[0]
            1

            >>> nu.run(nu.Dict({"a": 1}).get_item("b", 0))[0]
            0
        """
        from .mapping_interactions import Get

        return cast("ValueResultT", self._wrap_value_result(Get(self, key, default)))

    def copy(self) -> CollectionResultT:
        """Shallow copy of self: mapping.copy().

        Yields:
            A new mapping with the same key/value pairs. INVALID when self
            is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).copy())[0]
            {'a': 1}
        """
        from .mapping_interactions import Copy

        return cast("CollectionResultT", self._wrap_mapping_result(Copy(self)))

    def reversed_keys(self) -> CollectionResultT:
        """Keys in reverse insertion order: reversed(mapping).

        Yields:
            An iterator over the keys, reversed. INVALID when self is a
            sentinel.

        Example:
            >>> list(nu.run(nu.Dict({"a": 1, "b": 2}).reversed_keys())[0])
            ['b', 'a']
        """
        from .mapping_interactions import ReversedKeys

        return cast("CollectionResultT", self._wrap_keys_result(ReversedKeys(self)))

    def reversed_values(self) -> CollectionResultT:
        """Values in reverse insertion order: reversed(mapping.values()).

        Yields:
            An iterator over the values, reversed. INVALID when self is a
            sentinel.

        Example:
            >>> list(nu.run(nu.Dict({"a": 1, "b": 2}).reversed_values())[0])
            [2, 1]
        """
        from .mapping_interactions import ReversedValues

        return cast("CollectionResultT", self._wrap_values_result(ReversedValues(self)))

    def reversed_items(self) -> CollectionResultT:
        """(key, value) pairs in reverse insertion order: reversed(mapping.items()).

        Yields:
            An iterator over the (key, value) pairs, reversed. INVALID
            when self is a sentinel.

        Example:
            >>> list(nu.run(nu.Dict({"a": 1, "b": 2}).reversed_items())[0])
            [('b', 2), ('a', 1)]
        """
        from .mapping_interactions import ReversedItems

        return cast("CollectionResultT", self._wrap_items_result(ReversedItems(self)))

    def merge(self, other: Arg[Mapping[KeyT, ValueT]]) -> CollectionResultT:
        """Self and other merged into a new mapping: mapping | other.

        Args:
            other: the mapping to merge in. Its keys win over self's on
                overlap.

        Yields:
            A new mapping holding self's entries overridden by other's.
            INVALID when self or other is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).merge({"b": 2}))[0]
            {'a': 1, 'b': 2}
        """
        from .mapping_interactions import Merge

        return cast("CollectionResultT", self._wrap_mapping_result(Merge(self, other)))


class MutableMappingForm(
    MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mutable mapping values: adds in-place writes over MappingForm.

    Notes:
        - `set_item`, `del_item`, `update`, and `clear` are Commands: they
          mutate slot 0 and yield nothing. Running them needs a Ref in slot
          0, not a plain literal mapping.
        - `pop`, `popitem`, `setdefault`, and `merge_update` are Actions:
          they mutate and yield a value.
    """

    def set_item(self, key: Arg[KeyT], value: Arg[ValueT]) -> Any:  # noqa: ANN401
        """Set the value at key, inserting the key if it's missing: mapping[key] = value.

        Args:
            key: the key to set.
            value: the value to store at key.

        Notes:
            - Mutating Command: mutates slot 0 in place, yields nothing.
              Needs a Ref in slot 0 to run; a plain literal mapping fails
              evaluation.

        Example:
            d.set_item("b", 2)
        """
        from nu.core.access import SetItem

        return SetItem(self, key, value)

    def del_item(self, key: Arg[KeyT]) -> Any:  # noqa: ANN401
        """Delete the entry at key: del mapping[key].

        Args:
            key: the key to delete.

        Notes:
            - Mutating Command: mutates slot 0 in place, yields nothing.
              Needs a Ref in slot 0 to run; a plain literal mapping fails
              evaluation.

        Example:
            d.del_item("a")
        """
        from .mapping_interactions import DeleteItem

        return DeleteItem(self, key)

    def update(self, other: Arg[Mapping[KeyT, ValueT]]) -> Any:  # noqa: ANN401
        """Write other's entries into self, in place: mapping.update(other).

        Args:
            other: the mapping whose entries to write in. Its values win
                over self's on shared keys.

        Notes:
            - Mutating Command: mutates slot 0 in place, yields nothing.
              Needs a Ref in slot 0 to run; a plain literal mapping fails
              evaluation.

        Example:
            d.update({"b": 2})
        """
        from .mapping_interactions import Update

        return Update(self, other)

    def pop(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Remove key and yield its value, or default if key is missing.

        Args:
            key: the key to remove.
            default: the value to yield when key is missing.

        Notes:
            - Mutates slot 0 (removes the entry) and yields a value:
              an Action, not a Command.
            - Without a default, a missing key yields INVALID rather than
              raising - unlike `__getitem__`/`get_item` with no default,
              which raise.

        Yields:
            The removed value, or default when key is missing. INVALID
            when key is missing and no default is given, or when self or
            key is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).pop("a"))[0]
            1

            >>> nu.run(nu.Dict({"a": 1}).pop("b", 0))[0]
            0
        """
        from .mapping_interactions import DictPop

        return cast("ValueResultT", self._wrap_value_result(DictPop(self, key, default)))

    def popitem(self) -> ValueResultT:
        """Remove and yield an arbitrary (key, value) pair: mapping.popitem().

        Notes:
            - Mutates slot 0 (removes the entry) and yields a value: an
              Action, not a Command.
            - Removes in LIFO order, matching Python's `dict.popitem`.

        Yields:
            The removed (key, value) pair. INVALID when self is empty or a
            sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).popitem())[0]
            ('b', 2)
        """
        from .mapping_interactions import PopItem

        return cast("ValueResultT", self._wrap_value_result(PopItem(self)))

    def setdefault(self, key: Arg[KeyT], default: Arg[ValueT] | None = None) -> ValueResultT:
        """Value at key, inserting default there first if key is missing.

        Args:
            key: the key to look up, and to insert default at if missing.
            default: the value to insert and yield when key is missing.

        Notes:
            - Mutates slot 0 (inserts the entry when key is missing) and
              yields a value: an Action, not a Command.
            - Self is unchanged when key is already present; default is
              only inserted on a miss.

        Yields:
            The value already at key, or default once inserted. INVALID
            when self or key is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).setdefault("a", 9))[0]
            1

            >>> nu.run(nu.Dict({"a": 1}).setdefault("b", 9))[0]
            9
        """
        from .mapping_interactions import SetDefault

        return cast("ValueResultT", self._wrap_value_result(SetDefault(self, key, default)))

    def merge_update(self, other: Arg[Mapping[KeyT, ValueT]]) -> CollectionResultT:
        """Merge other into self in place, and yield self: mapping |= other.

        Args:
            other: the mapping to merge in. Its values win over self's on
                shared keys.

        Notes:
            - Mutates slot 0 in place and yields the mutated mapping: an
              Action, not a Command, mirroring Python's `dict.__ior__`.

        Yields:
            Self, updated with other's entries. INVALID when self or
            other is a sentinel.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).merge_update({"b": 2}))[0]
            {'a': 1, 'b': 2}
        """
        from .mapping_interactions import MergeUpdate

        return cast("CollectionResultT", self._wrap_mapping_result(MergeUpdate(self, other)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all entries: mapping.clear().

        Notes:
            - Mutating Command: mutates slot 0 in place, yields nothing.
              Needs a Ref in slot 0 to run; a plain literal mapping fails
              evaluation.

        Example:
            d.clear()
        """
        from .shared_interactions import Clear

        return Clear(self)


class ReactiveMappingForm(
    MutableMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Reactive mapping: adds any-change observation over MutableMappingForm.

    Notes:
        - The three tree-aware observers (`on_child_change`,
          `on_children_change`, `on_descendants_change`) are shape-domain
          and live on `nu.domains.shape.forms.collection.ReactiveCollectionForm`,
          not here.
    """

    def on_change(self) -> object:
        """Subscribe to any change on this mapping slot.

        Notes:
            - Fires on any mutation to this slot - set_item, del_item,
              update, pop, popitem, setdefault, merge_update, clear -
              without distinguishing which one.

        Yields:
            A subscription/stream over change events. Needs a live
            reactive fabric to run.

        Example:
            d.on_change()
        """
        from nu.core.reactive import OnChange

        return OnChange(self)
