"""Float ref base combining numeric traits.

FloatType = Object[float] + Numeric + Comparable + Logical
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...capabilities import ComparableBase, LogicalBase, NumericBase
from ..object import Object


if TYPE_CHECKING:
    from nu.terms import BoolArg, FloatArg, IntArg, Nu  # noqa: F401

    from ...values import BoolValue, FloatValue


__all__ = [
    "FloatType",
]


class FloatType(
    NumericBase["IntArg | FloatArg", "FloatValue"],
    ComparableBase["IntArg | FloatArg"],
    LogicalBase["BoolArg | FloatArg", "BoolValue"],
    Object[float],
):
    """Abstract base for float refs.

    Combines:
    - Numeric: +, -, *, /, //, %, **, neg, pos, abs
    - Comparable: >, <, >=, <=, eq(), ne(), is_()
    - Logical: and_(), or_(), not_(), bool_()

    Concrete implementations must add get() for their storage substrate.
    """

    def _wrap_arithmetic_result(self, operand: Nu) -> FloatValue:
        from ...values import FloatValue

        return FloatValue(operand)

    def _wrap_logical_result(self, operand: Nu) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Nu) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def __neg__(self) -> FloatValue:
        from nu.ops import NegOp
        from ...values import FloatValue

        return FloatValue(NegOp(self))

    def __pos__(self) -> FloatValue:
        from nu.ops import PosOp
        from ...values import FloatValue

        return FloatValue(PosOp(self))

    def __abs__(self) -> FloatValue:
        from nu.ops import AbsOp
        from ...values import FloatValue

        return FloatValue(AbsOp(self))
