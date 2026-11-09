"""Mapping collection: bases + mutations.

MappingForm = Collection + keys/values/items/get_item
MutableMappingForm = Mapping + set_item/del_item/update/pop/popitem/setdefault/clear
OrderedMappingForm = Mapping + Reversible: reversed_keys/values/items streams + paging
MutableOrderedMappingForm = OrderedMapping + MutableMapping
ReactiveOrderedMappingForm = MutableOrderedMapping + ReactiveMapping

Follows Python's collections.abc.Mapping / MutableMapping pattern. Built-in-only
methods (``copy``, ``merge``, ``merge_update``) live on ``Dict``.

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

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast, overload

from .collection import CollectionForm


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.forms.collections.iterator_ import Iterator
    from nu.forms.collections.list_ import List
    from nu.lang import Arg, Nu


__all__ = [
    "MappingForm",
    "MutableMappingForm",
    "MutableOrderedMappingForm",
    "OrderedMappingForm",
    "ReactiveMappingForm",
    "ReactiveOrderedMappingForm",
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
        - The four `_wrap_*` methods are the override seam: `_wrap_value_result`
          covers subscript and `get_item`; the other three cover the
          views (`keys`, `values`, `items`). A concrete mapping Form
          overrides all four to pick its own result types.
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

    def __getitem__(self, key: Arg[KeyT]) -> ValueResultT:
        """Value at key: mapping[key].

        Args:
            key: the key to look up.

        Notes:
            - Raises at evaluation time when key is missing, matching
              Python's `dict[key]`. Use `get_item` for a default instead
              of a raise.

        Yields:
            The value at key.

        Example:
            >>> nu.run(nu.Dict({"a": 1})["a"])[0]
            1
        """
        from nu.core import GetItem as At

        return cast("ValueResultT", self._wrap_value_result(At(self, key)))

    def keys(self) -> CollectionResultT:
        """All keys of the mapping: mapping.keys().

        Notes:
            - Paging (``keys(after=, limit=)``) is on ordered mappings
              only, `OrderedMappingForm`.

        Yields:
            A view over the keys, in the mapping's order.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).keys())[0]
            dict_keys(['a', 'b'])
        """
        from .mapping_interactions import Keys

        return cast("CollectionResultT", self._wrap_keys_result(Keys(self)))

    def values(self) -> CollectionResultT:
        """All values of the mapping: mapping.values().

        Yields:
            A view over the values, in insertion order.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).values())[0]
            dict_values([1, 2])
        """
        from .mapping_interactions import Values

        return cast("CollectionResultT", self._wrap_values_result(Values(self)))

    def items(self) -> CollectionResultT:
        """All (key, value) pairs of the mapping: mapping.items().

        Yields:
            A view over the (key, value) pairs, in insertion order.

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
            is given.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).get_item("a"))[0]
            1

            >>> nu.run(nu.Dict({"a": 1}).get_item("b", 0))[0]
            0
        """
        from .mapping_interactions import Get

        return cast("ValueResultT", self._wrap_value_result(Get(self, key, default)))


class MutableMappingForm(
    MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for mutable mapping values: adds in-place writes over MappingForm.

    Notes:
        - `set_item`, `del_item`, `update`, and `clear` are Commands: they
          mutate slot 0 and yield nothing. Running them needs a Ref in slot
          0, not a plain literal mapping.
        - `pop`, `popitem`, and `setdefault` are Actions: they mutate and
          yield a value.
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

    def del_item(self, key: Arg[KeyT], *, missing_ok: bool = False) -> Any:  # noqa: ANN401
        """Delete the entry at key: del mapping[key].

        Args:
            key: the key to delete.
            missing_ok: when ``True``, an absent key is a no-op. A plain
                Python bool fixed at construction, not a Nu value.

        Notes:
            - Mutating Command: mutates slot 0 in place, yields nothing.
              Needs a Ref in slot 0 to run; a plain literal mapping fails
              evaluation.
            - An absent key raises what the mapping's own ``del`` raises,
              KeyError on a Python dict. ``missing_ok`` turns that KeyError
              into a no-op.
            - A key or a target that reads NULL raises ValueError, even
              with ``missing_ok``: a NULL id addresses nothing to delete.

        Example:
            >>> class Port(nu.Shape):
            ...     owners = nu.DictRef.slot(str)
            >>> data = {"owners": {"core": "gor"}}
            >>> ctx = nu.Context().bind(dict, data, Port)
            >>> _ = nu.run(Port.owners.del_item("core"), ctx)
            >>> _ = nu.run(Port.owners.del_item("core", missing_ok=True), ctx)
            >>> data
            {'owners': {}}
        """
        from .mapping_interactions import DeleteItem

        return DeleteItem(self, key, missing_ok=missing_ok)

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
            - Without a default, a missing key raises `KeyError`, as in
              Python.
            - A NULL self or key raises, as any write does.

        Yields:
            The removed value, or default when key is missing.

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
            The removed (key, value) pair.

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
            The value already at key, or default once inserted.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).setdefault("a", 9))[0]
            1

            >>> nu.run(nu.Dict({"a": 1}).setdefault("b", 9))[0]
            9
        """
        from .mapping_interactions import SetDefault

        return cast("ValueResultT", self._wrap_value_result(SetDefault(self, key, default)))

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
          and live on `nu.domains.shape.collection.ReactiveCollectionForm`,
          not here.
    """

    def on_change(self) -> object:
        """Subscribe to any change on this mapping slot.

        Notes:
            - Fires on any mutation to this slot - set_item, del_item,
              update, pop, popitem, setdefault, clear - without
              distinguishing which one.

        Yields:
            A subscription/stream over change events. Needs a live
            reactive fabric to run.

        Example:
            d.on_change()
        """
        from nu.core.reactive import OnChange

        return OnChange(self)


class OrderedMappingForm(
    MappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Base for ordered mappings: Mapping + Reversible.

    Notes:
        - Python's ``Mapping`` has no order to walk back or page through;
          ``dict`` and the ordered fabric mappings do. They sit here, a
          hashed or unordered mapping stays on `MappingForm`.
        - Adds the reversed reads (``reversed_keys``, ``reversed_values``,
          ``reversed_items``), streams like Python's ``reversed``, and
          paging: ``keys(after=, limit=)`` and ``reversed_keys(before=,
          limit=)``, each a List. Paging runs on a runtime mapping that is a
          `PagedMapping`; anything else raises TypeError.
        - Three hooks type the results: `_wrap_iterable_result` (a stream of
          keys), `_wrap_values_stream`, `_wrap_items_stream` and
          `_wrap_keys_page` (a List of keys).
    """

    def _wrap_values_stream(self, operand: Nu) -> Iterator[ValueT]:
        """Wrap a stream term over self's values as an Iterator. Override to type the values."""
        from nu.forms.collections.iterator_ import Iterator

        return Iterator(operand)

    def _wrap_items_stream(self, operand: Nu) -> Iterator[tuple[KeyT, ValueT]]:
        """Wrap a stream term over self's ``(key, value)`` pairs as an Iterator."""
        from nu.forms.collections.iterator_ import Iterator

        return Iterator(operand)

    def _wrap_keys_page(self, operand: Nu) -> List[KeyT]:
        """Wrap a term yielding one page of keys as a List. Override to type the keys."""
        from nu.forms.collections.list_ import List

        return List(operand)

    # no arguments is the keys view, any argument a page: the first overload wins a bare call
    @overload
    def keys(self) -> CollectionResultT: ...  # type: ignore[overload-overlap]
    @overload
    def keys(
        self, *, after: Arg[KeyT] | None = ..., limit: Arg[int] | None = ...
    ) -> List[KeyT]: ...
    def keys(
        self, *, after: Arg[KeyT] | None = None, limit: Arg[int] | None = None
    ) -> CollectionResultT | List[KeyT]:
        """All keys of the mapping, or one page of them as a List.

        Args:
            after: the key to start past. Paging only.
            limit: the most keys to read. Paging only.

        Notes:
            - With neither argument: ``mapping.keys()``, a view over every
              key.
            - With either: ``mapping.keys(after=after, limit=limit)``,
              collected into a List. The mapping pages itself: what
              ``after`` means, and what the page costs, is its own. A
              runtime mapping that is no `PagedMapping` raises TypeError at
              evaluation time; a Python ``dict`` is none.
            - Both are ordinary Nu values, so a ref read at run time works.
              One that reads NULL raises ValueError before the mapping is
              called: branch on it first (``IsNull``).

        Yields:
            A view over the keys, in the mapping's order; with either
            argument, a list of keys.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).keys())[0]
            dict_keys(['a', 'b'])
        """
        if after is None and limit is None:
            from .mapping_interactions import Keys

            return cast("CollectionResultT", self._wrap_keys_result(Keys(self)))
        from .mapping_interactions import KeysPage

        return self._wrap_keys_page(KeysPage(self, after, limit))

    @overload
    def reversed_keys(self) -> Iterator[KeyT]: ...  # type: ignore[overload-overlap]
    @overload
    def reversed_keys(
        self, *, before: Arg[KeyT] | None = ..., limit: Arg[int] | None = ...
    ) -> List[KeyT]: ...
    def reversed_keys(
        self, *, before: Arg[KeyT] | None = None, limit: Arg[int] | None = None
    ) -> Iterator[KeyT] | List[KeyT]:
        """Keys last first as a stream, or one page of them as a List.

        Args:
            before: the key to start before. Paging only.
            limit: the most keys to read. Paging only.

        Notes:
            - With neither argument: ``reversed(mapping)``, a stream; loop
              it with `nu.ForEachDo` or drain it with `.to_list()`.
            - With either: ``mapping.reversed_keys(before=before,
              limit=limit)``, collected into a List. Same contract as
              ``keys(after=, limit=)``: a runtime mapping that is no
              `PagedMapping` raises TypeError, and a ``before`` or ``limit``
              that reads NULL raises ValueError.

        Yields:
            The keys, last first; with either argument, a list of keys.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).reversed_keys().to_list())[0]
            ['b', 'a']
        """
        if before is None and limit is None:
            from .mapping_interactions import ReversedKeys

            return cast("Iterator[KeyT]", self._wrap_iterable_result(ReversedKeys(self)))
        from .mapping_interactions import ReversedKeysPage

        return self._wrap_keys_page(ReversedKeysPage(self, before, limit))

    def reversed_values(self) -> Iterator[ValueT]:
        """Values last first, as a stream: reversed(mapping.values()).

        Yields:
            The values, last first.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).reversed_values().to_list())[0]
            [2, 1]
        """
        from .mapping_interactions import ReversedValues

        return self._wrap_values_stream(ReversedValues(self))

    def reversed_items(self) -> Iterator[tuple[KeyT, ValueT]]:
        """(key, value) pairs last first, as a stream: reversed(mapping.items()).

        Yields:
            The (key, value) pairs, last first.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).reversed_items().to_list())[0]
            [('b', 2), ('a', 1)]
        """
        from .mapping_interactions import ReversedItems

        return self._wrap_items_stream(ReversedItems(self))


class MutableOrderedMappingForm(
    OrderedMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    MutableMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Mutable ordered mapping: the in-place writes of MutableMappingForm over an ordered mapping."""


class ReactiveOrderedMappingForm(
    MutableOrderedMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    ReactiveMappingForm[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
    Generic[CollectionT, KeyT, ValueT, CollectionResultT, ValueResultT],
):
    """Reactive ordered mapping: any-change observation over MutableOrderedMappingForm."""
