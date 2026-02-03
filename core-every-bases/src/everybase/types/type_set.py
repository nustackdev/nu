"""Set ref bases combining set traits.

SetType = TypeBase[set] + MutableSet + Clearable + Comparable
FrozenSetType = TypeBase[frozenset] + SetLike + Comparable (immutable)

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import ClearableBase, ComparableBase
from everybase.collections import MutableSetBase, SetLikeBase

from .base import TypeBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import AnyValue, BoolValue, FrozenSetValue, ListValue, SetValue


__all__ = [
    "FrozenSetType",
    "SetType",
]


class SetType[T](
    MutableSetBase[set[T], T, "SetValue[T]", "AnyValue"],
    ClearableBase,
    ComparableBase["set[T] | SetValue[T]"],
    TypeBase[set[T]],
):
    """Abstract base for set refs.

    Combines set traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_set_result(self, operand: Term) -> SetValue[T]:
        from everybase.values import SetValue

        return SetValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from everybase.values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from everybase.values import AnyValue

        return AnyValue(operand)


class FrozenSetType[T](
    SetLikeBase[frozenset[T], T, "FrozenSetValue[T]", "AnyValue"],
    ComparableBase["frozenset[T] | FrozenSetValue[T]"],
    TypeBase[frozenset[T]],
):
    """Abstract base for frozenset refs.

    Immutable version of SetType.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_set_result(self, operand: Term) -> FrozenSetValue[T]:
        from everybase.values import FrozenSetValue

        return FrozenSetValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from everybase.values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from everybase.values import AnyValue

        return AnyValue(operand)
