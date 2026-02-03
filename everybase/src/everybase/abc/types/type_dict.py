"""Dict ref base combining mapping traits.

DictType = TypeBase[dict] + MutableMapping + Clearable + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..capabilities import ClearableBase, ComparableBase
from ..collections import MutableMappingBase
from .base import TypeBase


if TYPE_CHECKING:
    from everybase.core import Term

    from ..values import AnyValue, BoolValue, DictValue, ListValue  # noqa: F401


__all__ = [
    "DictType",
]


class DictType[K, V](
    MutableMappingBase[dict[K, V], K, V, "DictValue[K, V]", "AnyValue"],
    ClearableBase,
    ComparableBase["dict[K, V] | DictValue[K, V]"],
    TypeBase[dict[K, V]],
):
    """Abstract base for dict refs.

    Combines mapping traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from ..values import BoolValue

        return BoolValue(operand)

    def _wrap_keys_result(self, operand: Term) -> ListValue:
        from ..values import ListValue

        return ListValue(operand)

    def _wrap_values_result(self, operand: Term) -> ListValue:
        from ..values import ListValue

        return ListValue(operand)

    def _wrap_items_result(self, operand: Term) -> ListValue:
        from ..values import ListValue

        return ListValue(operand)

    def _wrap_value_result(self, operand: Term) -> AnyValue:
        from ..values import AnyValue

        return AnyValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from ..values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from ..values import AnyValue

        return AnyValue(operand)

    def __getitem__(self, key: K) -> AnyValue:
        from ..morphisms import AtOp
        from ..values import AnyValue

        return AnyValue(AtOp(self, key))
