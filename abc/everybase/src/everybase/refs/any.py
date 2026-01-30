"""Any ref base for dynamic/unknown types.

AnyRefBase = RefBase[object] + Numeric + Comparable + Logical + Bitwise

Returns concrete py types.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.capabilities import Bitwise, Comparable, Logical, Numeric

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import AnyRef, BoolRef


__all__ = [
    "AnyRefBase",
]


class AnyRefBase(
    Numeric["object", "AnyRef"],
    Comparable["object"],
    Logical["object", "BoolRef"],
    Bitwise["object", "AnyRef"],
    RefBase[object],
    ABC,
):
    """Abstract base for any/dynamic type refs.

    AnyRefBase can hold any type and supports all operations.
    Results remain as AnyRef until type is known.
    """

    def _wrap_arithmetic_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)

    def _wrap_bitwise_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)
