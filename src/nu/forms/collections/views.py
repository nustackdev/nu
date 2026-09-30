"""Dict view interfaces - DictKeys, DictValues, DictItems."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar

from nu.lang import TypedNu

from .abc import CollectionForm
from .abc.set_ import SetLikeForm


if TYPE_CHECKING:
    from nu.lang import Nu

    from ..primitives import Object
    from .list_ import List
    from .set_ import Set


__all__ = [
    "DictItems",
    "DictKeys",
    "DictValues",
]


K = TypeVar("K")
V = TypeVar("V")


class DictKeys(
    SetLikeForm[KeysView[K], K, "Set[K]", "Object"],
    TypedNu[KeysView[K]],
    Generic[K],
):
    """View of a Dict's keys, produced by `dict.keys()`.

    Notes:
        - Set-like: `union`, `intersection`, `difference`, `issubset`, and
          the `| & - ^` operators all work on it directly, matching
          Python's `dict.keys()`.
        - Lazy and live: it holds no keys of its own, it re-reads the
          backing Dict on every evaluation. Mutate the Dict and the view
          reflects it on the next `nu.run`.
        - Iterable, sized (`len()`), and supports `contains`.

    Example:
        >>> keys = nu.Dict({"a": 1, "b": 2}).keys()
        >>> nu.run(keys.len())[0]
        2
        >>> nu.run(keys.contains("a"))[0]
        True
    """

    def _wrap_set_result(self, operand: Nu) -> Set[K]:
        """Wrap operand as Set."""
        from .set_ import Set

        return Set(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List[K]:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from ..primitives import Object

        return Object(operand)

    def to_list(self) -> List[K]:
        """Snapshot the keys into a List.

        Yields:
            The keys as a plain List, in dict iteration order. Unlike the
            view itself, the result no longer tracks the backing Dict.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).keys().to_list())[0]
            ['a', 'b']
        """
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[K]:
        """Snapshot the keys into a Set.

        Yields:
            The keys as a plain Set. Unlike the view itself, the result no
            longer tracks the backing Dict.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).keys().to_set())[0] == {"a", "b"}
            True
        """
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))


_VALUES_EQ_HINT = (
    "a dict values view has no value equality (Python compares it by identity): "
    "compare a snapshot, v.to_list() == other or v.to_set() == other"
)


class DictValues(
    CollectionForm[V, "List[V]", "Object"],
    TypedNu[ValuesView[V]],
    Generic[V],
):
    """View of a Dict's values, produced by `dict.values()`.

    Notes:
        - Not set-like: values can repeat and aren't required to be
          hashable, so there's no `union`/`intersection` here,
          unlike `DictKeys` and `DictItems`. Just Collection: iterable,
          sized (`len()`), and `contains`.
        - Lazy and live: it holds no values of its own, it re-reads the
          backing Dict on every evaluation. Mutate the Dict and the view
          reflects it on the next `nu.run`.
        - No `==` / `!=`: Python compares values views by identity, never
          by content, so both raise. Compare a snapshot instead:
          `values.to_list() == [...]`.

    Example:
        >>> values = nu.Dict({"a": 1, "b": 2}).values()
        >>> nu.run(values.len())[0]
        2
        >>> nu.run(values.contains(1))[0]
        True
    """

    def _wrap_iterable_result(self, operand: Nu) -> List[V]:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from ..primitives import Object

        return Object(operand)

    def __eq__(self, other: object) -> NoReturn:
        raise TypeError(_VALUES_EQ_HINT)

    def __ne__(self, other: object) -> NoReturn:
        raise TypeError(_VALUES_EQ_HINT)

    def to_list(self) -> List[V]:
        """Snapshot the values into a List.

        Yields:
            The values as a plain List, in dict iteration order. Unlike
            the view itself, the result no longer tracks the backing Dict.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).values().to_list())[0]
            [1, 2]
        """
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[V]:
        """Snapshot the values into a Set.

        Notes:
            - Raises at evaluation time if any value is unhashable.

        Yields:
            The values as a plain Set. Unlike the view itself, the result
            no longer tracks the backing Dict.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).values().to_set())[0] == {1, 2}
            True
        """
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))


class DictItems(
    SetLikeForm[ItemsView[K, V], tuple[K, V], "Set[tuple[K, V]]", "Object"],
    TypedNu[ItemsView[K, V]],
    Generic[K, V],
):
    """View of a Dict's `(key, value)` pairs, produced by `dict.items()`.

    Notes:
        - Set-like: `union`, `intersection`, `difference`, `issubset`, and
          the `| & - ^` operators all work on it directly, matching
          Python's `dict.items()` when the values are hashable.
        - Lazy and live: it holds no items of its own, it re-reads the
          backing Dict on every evaluation. Mutate the Dict and the view
          reflects it on the next `nu.run`.
        - Iterable, sized (`len()`), and supports `contains` with a
          `(key, value)` tuple.

    Example:
        >>> items = nu.Dict({"a": 1, "b": 2}).items()
        >>> nu.run(items.len())[0]
        2
        >>> nu.run(items.contains(("a", 1)))[0]
        True
    """

    def _wrap_set_result(self, operand: Nu) -> Set[tuple[K, V]]:
        """Wrap operand as Set."""
        from .set_ import Set

        return Set(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List[tuple[K, V]]:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from ..primitives import Object

        return Object(operand)

    def to_list(self) -> List[tuple[K, V]]:
        """Snapshot the items into a List.

        Yields:
            The `(key, value)` pairs as a plain List, in dict iteration
            order. Unlike the view itself, the result no longer tracks the
            backing Dict.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).items().to_list())[0]
            [('a', 1), ('b', 2)]
        """
        from nu.core import ToList

        from .list_ import List

        return List(ToList(self))

    def to_set(self) -> Set[tuple[K, V]]:
        """Snapshot the items into a Set.

        Notes:
            - Raises at evaluation time if any value is unhashable.

        Yields:
            The `(key, value)` pairs as a plain Set. Unlike the view
            itself, the result no longer tracks the backing Dict.

        Example:
            >>> nu.run(nu.Dict({"a": 1, "b": 2}).items().to_set())[0] == {("a", 1), ("b", 2)}
            True
        """
        from nu.core import ToSet

        from .set_ import Set

        return Set(ToSet(self))
