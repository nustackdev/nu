"""Dict view types — KeysView, ValuesView, ItemsView.

These mirror Python's dict view objects exactly:
    dict.keys()  -> KeysView  (Set-like: &, |, -, ^, issubset, issuperset, isdisjoint)
    dict.values() -> ValuesView (Collection: sized, iterable, containment — no set ops)
    dict.items() -> ItemsView  (Set-like: &, |, -, ^, issubset, issuperset, isdisjoint)

All views are:
    - Lazy (no materialization until iterated)
    - Reusable (can iterate multiple times, unlike iterators)
    - Live (reflect mutations to the underlying dict)
    - Sized (len() works)

Materialization boundaries:
    .to_list() -> ListValue
    .to_set() -> SetValue
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING

from ...collections_abc import CollectionBase
from ...collections_abc.set_ import SetLikeBase
from ..object import Object


if TYPE_CHECKING:
    from nu.terms import Term

    from ...values import AnyValue, ListValue, SetValue


__all__ = [
    "DictItemsType",
    "DictKeysType",
    "DictValuesType",
]


class DictKeysType[K](
    SetLikeBase[KeysView[K], K, "SetValue[K]", "AnyValue"],
    Object[KeysView[K]],
):
    """Type for dict key views — set-like, lazy, live.

    Supports set operations (union, intersection, difference, etc.)
    plus standard collection ops (contains, len_).
    """

    def _wrap_set_result(self, operand: Term) -> SetValue[K]:
        from ...values import SetValue

        return SetValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue[K]:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from ...values import AnyValue

        return AnyValue(operand)

    def to_list(self) -> ListValue[K]:
        """Materialize view into a list."""
        from nu.ops.builtins.conversion import ToListOp
        from ...values import ListValue

        return ListValue(ToListOp(self))

    def to_set(self) -> SetValue[K]:
        """Materialize view into a set."""
        from nu.ops.builtins.conversion import ToSetOp
        from ...values import SetValue

        return SetValue(ToSetOp(self))


class DictValuesType[V](
    CollectionBase[V, "ListValue[V]", "AnyValue"],
    Object[ValuesView[V]],
):
    """Type for dict value views — iterable, sized, containment. No set ops.

    dict_values does not support set operations because values may not be hashable.
    """

    def _wrap_iterable_result(self, operand: Term) -> ListValue[V]:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from ...values import AnyValue

        return AnyValue(operand)

    def to_list(self) -> ListValue[V]:
        """Materialize view into a list."""
        from nu.ops.builtins.conversion import ToListOp
        from ...values import ListValue

        return ListValue(ToListOp(self))

    def to_set(self) -> SetValue[V]:
        """Materialize view into a set."""
        from nu.ops.builtins.conversion import ToSetOp
        from ...values import SetValue

        return SetValue(ToSetOp(self))


class DictItemsType[K, V](
    SetLikeBase[ItemsView[K, V], tuple[K, V], "SetValue[tuple[K, V]]", "AnyValue"],
    Object[ItemsView[K, V]],
):
    """Type for dict item views — set-like, lazy, live.

    Supports set operations (union, intersection, difference, etc.)
    plus standard collection ops (contains, len_).
    """

    def _wrap_set_result(self, operand: Term) -> SetValue[tuple[K, V]]:
        from ...values import SetValue

        return SetValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue[tuple[K, V]]:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from ...values import AnyValue

        return AnyValue(operand)

    def to_list(self) -> ListValue[tuple[K, V]]:
        """Materialize view into a list."""
        from nu.ops.builtins.conversion import ToListOp
        from ...values import ListValue

        return ListValue(ToListOp(self))

    def to_set(self) -> SetValue[tuple[K, V]]:
        """Materialize view into a set."""
        from nu.ops.builtins.conversion import ToSetOp
        from ...values import SetValue

        return SetValue(ToSetOp(self))
