"""Dict - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, overload

from nu.lang import TypedNu

from ..constructor import value_constructor
from .abc import MutableOrderedMappingForm
from .abc.mapping_interactions import DictCreate, DictOf


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang import Arg, DictArg, Nu

    from ..primitives import (
        Bool,
        Bytes,
        Float,
        Int,
        Object,
        Str,
    )
    from .list_ import List
    from .views import DictItems, DictKeys, DictValues


__all__ = [
    "Dict",
]


K = TypeVar("K")
V = TypeVar("V")


class Dict(
    MutableOrderedMappingForm[dict[K, V], K, V, "Dict[K, V]", "Object"],
    TypedNu[dict[K, V]],
    Generic[K, V],
):
    """Dict interface. Mutable ordered mapping, compared by value with `==` only.

    Notes:
        - Keys preserve insertion order, matching Python's `dict`.
        - No ordering comparisons (`>`, `<`, `>=`, `<=`), as on Python's
          `dict`: building one raises `TypeError`. Use `==`/`!=` for
          content comparison.
        - `is_` tests object identity. Each evaluation of a `Dict.of`/
          `Dict.create` expression builds a fresh dict, so comparing two
          separately-built dicts with `is_` is False even when their
          contents match, unlike Python's small-string interning for Str.
        - `copy`, `merge` and `merge_update` are dict-only; the rest of
          the surface comes from the shared mutable ordered-mapping base.
        - Merging is named: `merge` and `merge_update`. `&`, `|` and `>>`
          compose flows on a Dict like on every term.

    Example:
        >>> nu.run(nu.Dict.of(a=1, b=2))[0]
        {'a': 1, 'b': 2}
    """

    @value_constructor
    def create(cls) -> Dict[K, V]:
        """Fresh empty dict.

        Yields:
            A new, empty dict. Never a sentinel.

        Example:
            >>> nu.run(nu.Dict.create())[0]
            {}
        """
        return cls(DictCreate())

    @value_constructor
    def of(cls, **fields: Arg) -> Dict[str, V]:
        """Dict built from named field expressions.

        Args:
            fields: keyword arguments, each evaluated in the current
                context and zipped back in by name: `a=x, b=y` builds
                `{"a": <x>, "b": <y>}`. Values may be Nu expressions or
                plain literals.

        Yields:
            The assembled dict.

        Example:
            >>> nu.run(nu.Dict.of(a=1, b=2))[0]
            {'a': 1, 'b': 2}
        """
        return cls(DictOf(**fields))

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        """Wrap operand as DictKeys."""
        from .views import DictKeys

        return DictKeys(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        """Wrap operand as DictValues."""
        from .views import DictValues

        return DictValues(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        """Wrap operand as DictItems."""
        from .views import DictItems

        return DictItems(operand)

    def _wrap_value_result(self, operand: Nu) -> Object:
        """Wrap operand as a value-typed Form when known; Object otherwise.

        When the wrapping Form carries an annotation-derived ``TypeInfo`` on
        its payload (a Ref like ``PrimitiveDictRef[str, int]``), dispatch the
        value elem to its concrete Form (``Int`` here). Plain value-node
        ``Dict`` s (no payload) fall back to ``Object`` - the honest
        terminal for value-Form descent without narrowing context.
        """
        ti = self._payload.get("type_info")
        if ti is not None and ti.elem is not None:
            form_cls = ti.elem.to_form()
            return form_cls(operand)  # type: ignore[return-value]
        from ..primitives import Object

        return Object(operand)

    # ---- static overloads: narrow value type on subscript ---------------
    #
    # Runtime dispatch above; here we tell mypy which concrete Form to
    # expect based on ``V``. Applies to any subclass (PrimitiveDictRef[K, V],
    # nudle refs holding dicts, etc.) that specializes ``V``.

    @overload
    def __getitem__(self: Dict[K, bool], key: Arg[K]) -> Bool: ...
    @overload
    def __getitem__(self: Dict[K, int], key: Arg[K]) -> Int: ...
    @overload
    def __getitem__(self: Dict[K, float], key: Arg[K]) -> Float: ...
    @overload
    def __getitem__(self: Dict[K, str], key: Arg[K]) -> Str: ...
    @overload
    def __getitem__(self: Dict[K, bytes], key: Arg[K]) -> Bytes: ...
    @overload
    def __getitem__(self, key: Arg[K]) -> Object: ...
    def __getitem__(self, key):  # type: ignore[no-untyped-def]
        """Value at key.

        Args:
            key: the key to look up.

        Notes:
            - A missing key raises `KeyError` at evaluation time, matching
              Python's `dict[key]`. Use `get_item` for a default instead.

        Yields:
            The value, narrowed to a concrete Form (Bool, Int, Float, Str,
            Bytes) when `V` is a known primitive type, Object otherwise.

        Example:
            >>> nu.run(nu.Dict.of(a=1, b=2)["a"])[0]
            1
        """
        return super().__getitem__(key)

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        """Wrap operand as Dict."""
        return Dict(operand)

    @overload  # type: ignore[override]
    def keys(self) -> DictKeys[K]: ...  # type: ignore[overload-overlap]
    @overload
    def keys(self, *, after: Arg[K] | None = ..., limit: Arg[int] | None = ...) -> List[K]: ...
    def keys(
        self, *, after: Arg[K] | None = None, limit: Arg[int] | None = None
    ) -> DictKeys[K] | List[K]:
        """Self's keys as a live view, or one page of them as a List.

        Args:
            after: the key to start past. Paging only.
            limit: the most keys to read. Paging only.

        Notes:
            - Insertion order, matching Python's `dict.keys()`.
            - Paging forwards to the runtime mapping's own
              `keys(after=, limit=)`; it runs on a `PagedMapping` only, a
              Python `dict` is none and raises TypeError.

        Yields:
            The keys, wrapped as DictKeys; with either argument, a List.

        Example:
            >>> list(nu.run(nu.Dict.of(a=1, b=2).keys())[0])
            ['a', 'b']
        """
        return super().keys(after=after, limit=limit)  # type: ignore[call-overload, no-any-return]

    def values(self) -> DictValues[V]:  # type: ignore[override]
        """Self's values as a live view.

        Notes:
            - Insertion order, matching Python's `dict.values()`.

        Yields:
            The values, wrapped as DictValues.

        Example:
            >>> list(nu.run(nu.Dict.of(a=1, b=2).values())[0])
            [1, 2]
        """
        from .abc.mapping_interactions import Values

        return self._wrap_values_result(Values(self))

    def items(self) -> DictItems[K, V]:  # type: ignore[override]
        """Self's key-value pairs as a live view.

        Notes:
            - Insertion order, matching Python's `dict.items()`.

        Yields:
            The (key, value) pairs, wrapped as DictItems.

        Example:
            >>> list(nu.run(nu.Dict.of(a=1, b=2).items())[0])
            [('a', 1), ('b', 2)]
        """
        from .abc.mapping_interactions import Items

        return self._wrap_items_result(Items(self))

    # =========================================================================
    # DICT-ONLY (not on collections.abc.MutableMapping)
    # =========================================================================

    def copy(self) -> Dict[K, V]:
        """Shallow copy of self: mapping.copy().

        Yields:
            A new mapping with the same key/value pairs.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).copy())[0]
            {'a': 1}
        """
        from .abc.mapping_interactions import Copy

        return self._wrap_mapping_result(Copy(self))

    def merge(self, other: Arg[Mapping[K, V]]) -> Dict[K, V]:
        """Self and other merged into a new mapping, like Python's dict `|`.

        Args:
            other: the mapping to merge in. Its keys win over self's on
                overlap.

        Yields:
            A new mapping holding self's entries overridden by other's.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).merge({"b": 2}))[0]
            {'a': 1, 'b': 2}
        """
        from .abc.mapping_interactions import Merge

        return self._wrap_mapping_result(Merge(self, other))

    def merge_update(self, other: Arg[Mapping[K, V]]) -> Dict[K, V]:
        """Merge other into self in place, and yield self, like Python's dict `|=`.

        Args:
            other: the mapping to merge in. Its values win over self's on
                shared keys.

        Notes:
            - Mutates slot 0 in place and yields the mutated mapping: an
              Action, not a Command, mirroring Python's `dict.__ior__`.

        Yields:
            Self, updated with other's entries.

        Example:
            >>> nu.run(nu.Dict({"a": 1}).merge_update({"b": 2}))[0]
            {'a': 1, 'b': 2}
        """
        from .abc.mapping_interactions import MergeUpdate

        return self._wrap_mapping_result(MergeUpdate(self, other))

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from ..primitives import Object

        return Object(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __eq__(self, other: DictArg[K, V]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the dict to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the dicts have the same keys and values, False
            otherwise.

        Example:
            >>> nu.run(nu.Dict.of(a=1) == nu.Dict.of(a=1))[0]
            True
        """
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: DictArg[K, V]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the dict to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the dicts differ, False otherwise.

        Example:
            >>> nu.run(nu.Dict.of(a=1) != nu.Dict.of(a=2))[0]
            True
        """
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: DictArg[K, V]) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For content comparison
              use `==` instead.
            - Each `Dict.of`/`Dict.create` expression builds a fresh dict on
              evaluation, so two separately-built dicts test not identical
              even with equal contents - there's no interning like Str gets
              for short literals.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Dict.of(a=1).is_(nu.Dict.of(a=1)))[0]
            False
        """
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
