"""Dict view interfaces - DictKeys, DictValues, DictItems."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar

from .abc import CollectionSurface
from .abc.set_ import SetLikeSurface


if TYPE_CHECKING:
    from nu.forms import List, Object, Set
    from nu.lang import Nu


__all__ = [
    "DictItemsSurface",
    "DictKeysSurface",
    "DictValuesSurface",
]


K = TypeVar("K")
V = TypeVar("V")


class DictKeysSurface(SetLikeSurface[KeysView[K], K, "Set[K]", "Object"], Generic[K]):
    """The methods of ``DictKeys``. No slot holds one, so only the form carries them."""

    def _wrap_set_result(self, operand: Nu) -> Set[K]:
        """Wrap operand as Set."""
        from nu.forms import Set

        return Set(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from nu.forms import Object

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
        from nu.forms import List

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
        from nu.forms import Set

        return Set(ToSet(self))


_VALUES_EQ_HINT = (
    "a dict values view has no value equality (Python compares it by identity): "
    "compare a snapshot, v.to_list() == other or v.to_set() == other"
)


class DictValuesSurface(CollectionSurface[V, "List[V]", "Object"], Generic[V]):
    """The methods of ``DictValues``. No slot holds one, so only the form carries them."""

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from nu.forms import Object

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
        from nu.forms import List

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
        from nu.forms import Set

        return Set(ToSet(self))


class DictItemsSurface(
    SetLikeSurface[ItemsView[K, V], tuple[K, V], "Set[tuple[K, V]]", "Object"], Generic[K, V]
):
    """The methods of ``DictItems``. No slot holds one, so only the form carries them."""

    def _wrap_set_result(self, operand: Nu) -> Set[tuple[K, V]]:
        """Wrap operand as Set."""
        from nu.forms import Set

        return Set(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as Object element."""
        from nu.forms import Object

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
        from nu.forms import List

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
        from nu.forms import Set

        return Set(ToSet(self))
