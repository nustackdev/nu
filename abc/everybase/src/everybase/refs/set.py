"""Set ref bases combining set traits.

SetRefBase = RefBase[set] + SetLike + Comparable
FrozenSetRefBase = RefBase[frozenset] + SetLike + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import ComparableBase, SetLikeBase

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import AnyRef, BoolRef, FrozenSetRef, ListRef, SetRef


__all__ = [
    "FrozenSetRefBase",
    "SetRefBase",
]


class SetRefBase[T](
    SetLikeBase[T, "SetRef[T]"],
    ComparableBase["set[T] | SetRef[T]"],
    RefBase[set[T]],
):
    """Abstract base for set refs.

    Combines set traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    def _wrap_set_result(self, operand: Term) -> SetRef[T]:
        from everybase.py.set import SetRef

        return SetRef(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_element_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)


class FrozenSetRefBase[T](
    SetLikeBase[T, "FrozenSetRef[T]"],
    ComparableBase["frozenset[T] | FrozenSetRef[T]"],
    RefBase[frozenset[T]],
):
    """Abstract base for frozenset refs.

    Immutable version of SetRefBase.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_set_result(self, operand: Term) -> FrozenSetRef[T]:
        from everybase.py.frozenset import FrozenSetRef

        return FrozenSetRef(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_element_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)
