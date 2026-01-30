"""Any ref base for dynamic/unknown types.

AnyRefBase = RefBase[object] + Numeric + Comparable + Logical + Bitwise

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import BitwiseBase, ComparableBase, LogicalBase, NumericBase

from ._base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import AnyRef, BoolRef


__all__ = [
    "AnyRefBase",
]


class AnyRefBase(
    NumericBase["object", "AnyRef"],
    ComparableBase["object"],
    LogicalBase["object", "BoolRef"],
    BitwiseBase["object", "AnyRef"],
    RefBase[object],
):
    """Abstract base for any/dynamic type refs.

    AnyRefBase can hold any type and supports all operations.
    Results remain as AnyRef until type is known.
    """

    def _wrap_arithmetic_result(self, operand: Term) -> AnyRef:
        from everybase.py import AnyRef

        return AnyRef(operand)

    def _wrap_bitwise_result(self, operand: Term) -> AnyRef:
        from everybase.py import AnyRef

        return AnyRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)
