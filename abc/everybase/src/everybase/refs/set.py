"""Set ref bases combining set traits.

SetRefBase = RefBase[set] + SetLike + Comparable
FrozenSetRefBase = RefBase[frozenset] + SetLike + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.capabilities import Comparable, SetLike

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef, FrozenSetRef, SetRef


__all__ = [
    "FrozenSetRefBase",
    "SetRefBase",
]


class SetRefBase[T](
    SetLike[T, "SetRef[T]"],
    Comparable["set[T] | SetRef[T]"],
    RefBase[set[T]],
    ABC,
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


class FrozenSetRefBase[T](
    SetLike[T, "FrozenSetRef[T]"],
    Comparable["frozenset[T] | FrozenSetRef[T]"],
    RefBase[frozenset[T]],
    ABC,
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
