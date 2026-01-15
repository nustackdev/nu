"""Float type for Term expressions.

This module provides FloatType which represents float expressions (literal or computed).
Supports arithmetic, comparison, and logical operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import BaseType, ComparisonBase, LogicalBase


if TYPE_CHECKING:
    from everyshape.term import Term

    from .bool import BoolType  # noqa: F401
    from .int import IntType


__all__ = [
    "FloatType",
]


class FloatType(
    ComparisonBase["int | float | FloatType | IntType"],
    LogicalBase["bool | float | BoolType | FloatType", "BoolType"],
    BaseType[float],
):
    """Float type - represents float expressions (literal or computed).

    Supports arithmetic, comparison, and logical operations.
    All arithmetic operations return FloatType (Python semantics).

    Example:
        >>> x = FloatType(3.14)  # From literal
        >>> y = FloatType(some_op)  # From operation
        >>> z = x * 2  # Returns FloatType
    """

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    # All arithmetic returns FloatType
    def __add__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import AddOp

        return FloatType(AddOp(self, other))

    def __radd__(self, other: int | float) -> FloatType:
        from everyshape.ops import AddOp

        return FloatType(AddOp(other, self))

    def __sub__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import SubOp

        return FloatType(SubOp(self, other))

    def __rsub__(self, other: int | float) -> FloatType:
        from everyshape.ops import SubOp

        return FloatType(SubOp(other, self))

    def __mul__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import MulOp

        return FloatType(MulOp(self, other))

    def __rmul__(self, other: int | float) -> FloatType:
        from everyshape.ops import MulOp

        return FloatType(MulOp(other, self))

    def __truediv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import DivOp

        return FloatType(DivOp(self, other))

    def __rtruediv__(self, other: int | float) -> FloatType:
        from everyshape.ops import DivOp

        return FloatType(DivOp(other, self))

    def __floordiv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import FloorDivOp

        return FloatType(FloorDivOp(self, other))

    def __rfloordiv__(self, other: int | float) -> FloatType:
        from everyshape.ops import FloorDivOp

        return FloatType(FloorDivOp(other, self))

    def __mod__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import ModOp

        return FloatType(ModOp(self, other))

    def __rmod__(self, other: int | float) -> FloatType:
        from everyshape.ops import ModOp

        return FloatType(ModOp(other, self))

    def __pow__(self, other: int | float | IntType | FloatType) -> FloatType:
        from everyshape.ops import PowOp

        return FloatType(PowOp(self, other))

    def __rpow__(self, other: int | float) -> FloatType:
        from everyshape.ops import PowOp

        return FloatType(PowOp(other, self))

    def __neg__(self) -> FloatType:
        from everyshape.ops import NegOp

        return FloatType(NegOp(self))

    def __pos__(self) -> FloatType:
        from everyshape.ops import PosOp

        return FloatType(PosOp(self))

    def __abs__(self) -> FloatType:
        from everyshape.ops import AbsOp

        return FloatType(AbsOp(self))
