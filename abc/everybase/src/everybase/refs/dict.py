"""Dict ref base combining mapping traits.

DictRefBase = RefBase[dict] + Mapping + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.capabilities import Comparable, Mapping

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import AnyRef, BoolRef, DictRef, ListRef  # noqa: F401


__all__ = [
    "DictRefBase",
]


class DictRefBase[K, V](
    Mapping[K, V, "DictRef[K, V]"],
    Comparable["dict[K, V] | DictRef[K, V]"],
    RefBase[dict[K, V]],
    ABC,
):
    """Abstract base for dict refs.

    Combines mapping traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_keys_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_values_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_items_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_value_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)

    def __getitem__(self, key: K) -> AnyRef:
        from everybase.morphisms import AtOp
        from everybase.py.any import AnyRef

        return AnyRef(AtOp(self, key))
