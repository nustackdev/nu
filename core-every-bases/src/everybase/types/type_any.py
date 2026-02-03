"""Any ref base for dynamic/unknown types.

AnyType = TypeBase[object] + Numeric + Comparable + Logical + Bitwise

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import BitwiseBase, ComparableBase, LogicalBase, NumericBase

from .base import TypeBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import AnyValue, BoolValue


__all__ = [
    "AnyType",
]


class AnyType(
    NumericBase["object", "AnyValue"],
    ComparableBase["object"],
    LogicalBase["object", "BoolValue"],
    BitwiseBase["object", "AnyValue"],
    TypeBase[object],
):
    """Abstract base for any/dynamic type refs.

    AnyType can hold any type and supports all operations.
    Results remain as AnyValue until type is known.
    """

    def _wrap_arithmetic_result(self, operand: Term) -> AnyValue:
        from everybase.values import AnyValue

        return AnyValue(operand)

    def _wrap_bitwise_result(self, operand: Term) -> AnyValue:
        from everybase.values import AnyValue

        return AnyValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)
