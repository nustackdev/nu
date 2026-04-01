"""Set ref bases combining set traits.

SetType = Object[set] + MutableSet + Clearable + Comparable
FrozenSetType = Object[frozenset] + SetLike + Comparable (immutable)

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...capabilities import ComparableBase
from ...collections_abc import MutableSetBase, SetLikeBase
from ..object import Object


if TYPE_CHECKING:
    from nu.terms import FrozenSetArg, SetArg, Nu  # noqa: F401

    from ...values import AnyValue, BoolValue, FrozenSetValue, ListValue, SetValue


__all__ = [
    "FrozenSetType",
    "SetType",
]


class SetType[T](
    MutableSetBase[set[T], T, "SetValue[T]", "AnyValue"],
    # ClearableBase,
    ComparableBase["SetArg[T]"],
    Object[set[T]],
):
    """Abstract base for set refs.

    Combines set traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Nu) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_set_result(self, operand: Nu) -> SetValue[T]:
        from ...values import SetValue

        return SetValue(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListValue:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyValue:
        from ...values import AnyValue

        return AnyValue(operand)


class FrozenSetType[T](
    SetLikeBase[frozenset[T], T, "FrozenSetValue[T]", "AnyValue"],
    ComparableBase["FrozenSetArg[T]"],
    Object[frozenset[T]],
):
    """Abstract base for frozenset refs.

    Immutable version of SetType.
    """

    def _wrap_comparison_result(self, operand: Nu) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_set_result(self, operand: Nu) -> FrozenSetValue[T]:
        from ...values import FrozenSetValue

        return FrozenSetValue(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListValue:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyValue:
        from ...values import AnyValue

        return AnyValue(operand)
