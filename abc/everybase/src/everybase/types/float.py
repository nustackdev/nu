"""Float ref base combining numeric traits.

FloatType = TypeBase[float] + Numeric + Comparable + Logical
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import ComparableBase, LogicalBase, NumericBase

from ._base import TypeBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import BoolValue, FloatValue, IntValue  # noqa: F401


__all__ = [
    "FloatType",
]


class FloatType(
    NumericBase["int | float | IntValue | FloatValue", "FloatValue"],
    ComparableBase["int | float | IntValue | FloatValue"],
    LogicalBase["bool | float | BoolValue | FloatValue", "BoolValue"],
    TypeBase[float],
):
    """Abstract base for float refs.

    Combines:
    - Numeric: +, -, *, /, //, %, **, neg, pos, abs
    - Comparable: >, <, >=, <=, eq(), ne(), is_()
    - Logical: and_(), or_(), not_(), bool_()

    Concrete implementations must add get() for their storage substrate.
    """

    def _wrap_arithmetic_result(self, operand: Term) -> FloatValue:
        from everybase.values import FloatValue

        return FloatValue(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def __neg__(self) -> FloatValue:
        from everybase.morphisms import NegOp
        from everybase.values import FloatValue

        return FloatValue(NegOp(self))

    def __pos__(self) -> FloatValue:
        from everybase.morphisms import PosOp
        from everybase.values import FloatValue

        return FloatValue(PosOp(self))

    def __abs__(self) -> FloatValue:
        from everybase.morphisms import AbsOp
        from everybase.values import FloatValue

        return FloatValue(AbsOp(self))
